import streamlit as st
import polars as pl
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px
from datetime import datetime

def trajectory_analysis():
    # -----------------------------
    # Load and Normalize Data
    # -----------------------------
    dev = pl.read_parquet("realestate_developers-min.parquet")
    trend = pl.read_parquet("realestate_google_trends-min.parquet")
    cla = pl.read_parquet("cla-realestate-min.parquet")

    # Convert to datetime (handle both string and datetime inputs)
    def ensure_datetime(df, col_name):
        if df.schema[col_name] in [pl.Datetime, pl.Datetime('ms'), pl.Datetime('us'), pl.Datetime('ns')]:
            # Cast to consistent datetime precision (nanoseconds)
            return df.with_columns(pl.col(col_name).cast(pl.Datetime('ns')))
        else:
            return df.with_columns(pl.col(col_name).str.to_datetime().cast(pl.Datetime('ns')))
    
    dev = ensure_datetime(dev, 'post_upload_date')
    trend = ensure_datetime(trend, 'date')
    cla = ensure_datetime(cla, 'post_upload_date')

    # Add sub_theme column
    dev = dev.with_columns(
        pl.col('matched_keyword').alias('sub_theme')
    )
    cla = cla.with_columns(
        pl.col('matched_keyword').alias('sub_theme')
    )
    trend = trend.with_columns(
        pl.col('keyword').alias('sub_theme')
    )

    # -----------------------------
    # Country Normalization
    # -----------------------------
    COUNTRY_MAPPING = {
        "uae": "United Arab Emirates",
        'uk': 'United Kingdom',
        'egy': 'Egypt',
        'aus': 'Australia',
        'sg': 'Singapore',
        'sgp': 'Singapore',
        'ksa': 'Saudi Arabia'
    }

    def normalize_country(df, column='country'):
        return df.with_columns(
            pl.col(column).str.to_lowercase().replace(COUNTRY_MAPPING, default=None)
            .fill_null(pl.col(column).str.to_titlecase())
            .alias(column)
        )

    dev = normalize_country(dev)
    trend = normalize_country(trend)
    cla = normalize_country(cla)

    # -----------------------------
    # Dropdown Setup
    # -----------------------------
    combined_countries = (
        pl.concat([
            dev.select('country'),
            trend.select('country'),
            cla.select('country')
        ])
        .drop_nulls()
        .with_columns(pl.col('country').str.to_titlecase())
        .unique()
        .sort('country')
        .to_pandas()['country'].tolist()
    )

    selected_country = st.selectbox(
        "🌍 Select Country",
        options=["All countries"] + combined_countries,
        index=0
    )

    # -----------------------------
    # Helper Functions
    # -----------------------------
    def prepare_data(use_sub_theme=False, country=None):
        group_keys = ['theme', 'sub_theme'] if use_sub_theme else ['theme']

        trend_temp = trend.clone()
        dev_temp = dev.clone()
        cla_temp = cla.clone()

        if country is not None:
            dev_temp = dev_temp.filter(pl.col('country') == country)
            trend_temp = trend_temp.filter(pl.col('country') == country)
            cla_temp = cla_temp.filter(pl.col('country') == country)

        # Prepare developer data
        dev_temp = dev_temp.with_columns([
            pl.col('theme').alias('theme'),
            pl.col('matched_keyword').alias('sub_theme')
        ])

        # Prepare trend data
        trend_temp = trend_temp.with_columns([
            pl.col('theme').alias('theme'),
            pl.col('keyword').alias('sub_theme')
        ])

        # Prepare CLA data
        cla_temp = cla_temp.with_columns([
            pl.col('matched_theme').alias('theme'),
            pl.col('matched_keyword').alias('sub_theme')
        ])

        # Google Trends aggregation
        trend_agg = (
            trend_temp
            .group_by(group_keys + ['date'])
            .agg(pl.col('value').mean().alias('raw_volume'))
            .with_columns([
                pl.col('raw_volume').min().over(group_keys).alias('min_val'),
                pl.col('raw_volume').max().over(group_keys).alias('max_val')
            ])
            .with_columns([
                (100 * (pl.col('raw_volume') - pl.col('min_val')) / 
                 (pl.col('max_val') - pl.col('min_val') + 1e-6)).alias('volume'),
                pl.lit('google').alias('source'),
                pl.col('date').cast(pl.Datetime('ns')).alias('date')
            ])
            .select(group_keys + ['date', 'volume', 'source'])
        )

        # Developer Posts aggregation
        dev_agg = (
            dev_temp
            .with_columns(
                pl.col('post_upload_date').dt.truncate('1mo').cast(pl.Datetime('ns')).alias('date')
            )
            .group_by(group_keys + ['date'])
            .agg(pl.len().alias('count'))
            .with_columns([
                pl.col('count').min().over(group_keys).alias('min_count'),
                pl.col('count').max().over(group_keys).alias('max_count')
            ])
            .with_columns([
                (100 * (pl.col('count') - pl.col('min_count')) / 
                 (pl.col('max_count') - pl.col('min_count') + 1e-6)).alias('volume'),
                pl.lit('developer').alias('source')
            ])
            .select(group_keys + ['date', 'volume', 'source'])
        )

        # CLA Posts aggregation
        cla_agg = (
            cla_temp
            .with_columns(
                pl.col('post_upload_date').dt.truncate('1mo').cast(pl.Datetime('ns')).alias('date')
            )
            .group_by(group_keys + ['date'])
            .agg(pl.len().alias('count'))
            .with_columns([
                pl.col('count').min().over(group_keys).alias('min_count'),
                pl.col('count').max().over(group_keys).alias('max_count')
            ])
            .with_columns([
                (100 * (pl.col('count') - pl.col('min_count')) / 
                 (pl.col('max_count') - pl.col('min_count') + 1e-6)).alias('volume'),
                pl.lit('ugc').alias('source')
            ])
            .select(group_keys + ['date', 'volume', 'source'])
        )

        # Combine all sources
        all_sources = pl.concat([trend_agg, dev_agg, cla_agg])
        all_sources = all_sources.filter(pl.col('date') >= datetime(2021, 1, 1))

        if all_sources.height == 0:
            return pl.DataFrame(), group_keys

        # Calculate average volume across sources and ensure proper time series
        avg_volume = (
            all_sources
            .group_by(group_keys + ['date'])
            .agg(pl.col('volume').mean().alias('volume'))
            .sort(['date'] + group_keys)  # Sort for proper time series
        )

        return avg_volume, group_keys

    def classify_themes(avg_volume, group_keys):
        if avg_volume.height == 0:
            return pl.DataFrame(schema={
                **{key: pl.Utf8 for key in group_keys},
                'volume': pl.Float64,
                'growth': pl.Float64,
                'category': pl.Utf8
            })

        stats = []
        
        # Convert to pandas for sklearn operations
        avg_volume_pd = avg_volume.to_pandas()
        
        for keys, group in avg_volume_pd.groupby(group_keys):
            if not isinstance(keys, tuple):
                keys = (keys,)
            
            x = (group['date'] - group['date'].min()).dt.days.values.reshape(-1, 1)
            y = group['volume'].values.reshape(-1, 1)
            
            if len(x) < 2:
                continue
                
            reg = LinearRegression().fit(x, y)
            entry = {
                group_keys[0]: keys[0],
                'volume': float(y.mean()),
                'growth': float(reg.coef_[0][0]),
            }
            if len(group_keys) > 1:
                entry[group_keys[1]] = keys[1]
            stats.append(entry)

        if not stats:
            return pl.DataFrame(schema={
                **{key: pl.Utf8 for key in group_keys},
                'volume': pl.Float64,
                'growth': pl.Float64,
                'category': pl.Utf8
            })

        df = pl.DataFrame(stats)
        
        # Calculate medians
        v_median = df.select(pl.col('volume').median()).item()
        g_median = df.select(pl.col('growth').median()).item()

        # Classify themes
        df = df.with_columns([
            pl.when(
                (pl.col('volume') >= v_median) & (pl.col('growth') >= g_median)
            ).then(pl.lit('High Volume + High Growth'))
            .when(pl.col('volume') >= v_median)
            .then(pl.lit('High Volume + Low Growth'))
            .when(pl.col('growth') >= g_median)
            .then(pl.lit('Low Volume + High Growth'))
            .otherwise(pl.lit('Low Volume + Low Growth'))
            .alias('category')
        ])

        return df

    def plot_time_series(avg_volume, top_df, group_keys, category):
        key = group_keys[1] if len(group_keys) > 1 else group_keys[0]
        selected = top_df.filter(pl.col('category') == category).select(key).to_pandas()[key].tolist()
        
        # Filter and sort data properly for smooth lines
        data = (
            avg_volume
            .filter(pl.col(key).is_in(selected))
            .sort(['date', key])  # Sort by date and key for proper line continuity
            .to_pandas()
        )
        
        # Ensure proper datetime format for plotting
        data['date'] = pd.to_datetime(data['date'])
        
        fig = px.line(data, x='date', y='volume', color=key,
                      title=f"{category} - Top 3",
                      labels={'volume': 'Trend Score (0–100)'})
        
        # Improve line appearance
        fig.update_traces(line=dict(width=2))
        fig.update_layout(
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified'
        )
        return fig

    def plot_bar(stats_df, group_keys, use_top5=False):
        # Normalize volume
        stats_df = stats_df.with_columns([
            pl.col('volume').min().alias('min_vol'),
            pl.col('volume').max().alias('max_vol')
        ]).with_columns([
            (100 * (pl.col('volume') - pl.col('min_vol')) / 
             (pl.col('max_vol') - pl.col('min_vol') + 1e-6)).alias('normalized_volume')
        ])

        for category in stats_df.select('category').unique().to_pandas()['category']:
            data = stats_df.filter(pl.col('category') == category)
            key = group_keys[1] if len(group_keys) > 1 else group_keys[0]

            if use_top5:
                data = data.sort('volume', descending=True).head(5)

            data_pd = data.to_pandas()
            fig = px.bar(
                data_pd,
                x=key,
                y='normalized_volume',
                color=key,
                title=f"{category} - Normalized Volume",
                text='normalized_volume'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)

    def show_tab(title, use_sub_theme=False, country=None):
        avg_volume, group_keys = prepare_data(use_sub_theme=use_sub_theme, country=country)

        if avg_volume.height == 0:
            st.warning(f"No data available for {title.lower()} in the selected scope.")
            return

        stats_df = classify_themes(avg_volume, group_keys)

        if stats_df.height == 0:
            st.warning(f"Not enough data points for trend classification in {title.lower()}.")
            return

        # Get top 3 for each category
        top_df = (
            stats_df
            .with_row_index()
            .sort(['category', 'volume'], descending=[False, True])
            .with_columns(
                pl.int_range(pl.len()).over('category').alias('rank')
            )
            .filter(pl.col('rank') < 3)
            .drop(['index', 'rank'])
        )

        st.markdown(f"### {title} Summary")
        display_cols = ['theme'] + (['sub_theme'] if use_sub_theme else []) + ['volume', 'growth', 'category']
        st.dataframe(stats_df.select(display_cols).to_pandas(), use_container_width=True)

        line_graph, bar_graph = st.tabs(["Line Graphs", "Bar Graphs"])
        with line_graph:
            for cat in stats_df.select('category').unique().to_pandas()['category']:
                st.plotly_chart(plot_time_series(avg_volume, top_df, group_keys, cat), use_container_width=True)
        with bar_graph:
            plot_bar(stats_df, group_keys, use_top5=use_sub_theme)

    # -----------------------------
    # Layout
    # -----------------------------
    st.subheader("📊 Real Estate Trend Trajectory")

    selected_country_param = None if selected_country == "All countries" else selected_country

    theme_tab, sub_theme_tab = st.tabs(["Themes", "Sub-Themes"])
    with theme_tab:
        show_tab("Themes", use_sub_theme=False, country=selected_country_param)
    with sub_theme_tab:
        show_tab("Sub-Themes", use_sub_theme=True, country=selected_country_param)