import streamlit as st
import plotly.express as px
from bla_data import *
from datetime import datetime
import datetime
from chat import chat


def bla():
    st.subheader("Brand Led Analysis")

    f1, f2, f3 = st.columns([2, 2, 2])
    f4, f5 = st.columns([3, 3])

    themes = sorted(df['theme'].dropna().unique())
    sub_themes = sorted(df['matched_keyword'].dropna().unique())
    countries = sorted(df['country'].dropna().unique())
    accounts = sorted(df['username'].dropna().unique())
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    min_date = df['post_upload_date'].min()
    max_date = df['post_upload_date'].max()

    with f1:
        selected_themes = st.multiselect("Theme", options=themes)

    with f2:
        selected_sub_themes = st.multiselect("Sub Theme", options=sub_themes)

    with f3:
        selected_countries = st.multiselect("Country", options=countries)

    with f4:
        selected_date_range = st.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    with f5:
        selected_accounts = st.multiselect("Brands", options=accounts)

    

    # 🧼 Filtering Logic
    filtered_df = df.copy()

    if selected_accounts:
        filtered_df = filtered_df[filtered_df['username'].isin(selected_accounts)]

    if selected_themes:
        filtered_df = filtered_df[filtered_df['theme'].isin(selected_themes)]

    if selected_sub_themes:
        filtered_df = filtered_df[filtered_df['matched_keyword'].isin(selected_sub_themes)]

    if selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]

    start_date = datetime.datetime.combine(selected_date_range[0], datetime.datetime.min.time())
    end_date = datetime.datetime.combine(selected_date_range[1], datetime.datetime.max.time())

    filtered_df = filtered_df[
        filtered_df['post_upload_date'].between(start_date, end_date)
    ]

    # Refresh color maps for filtered data
    theme_color_map = get_theme_color_map(filtered_df)
    sub_theme_color_map = get_sub_theme_color_map(filtered_df)

    st.markdown("""
        <style>
        .metric-box {
            background-color: #ffffff;
            padding: 1rem;
            border: 1px solid rgba(200, 200, 200, 0.6);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: all 0.3s ease-in-out;
            margin: 3rem 0;
            cursor: pointer;
            max-width: 15rem;
            height: 7.5rem;
        }
        .metric-title {
            font-weight: bold;
            font-size: 14px;
        }
        .metric-value {
            font-size: 22px;
            margin-top: 1rem;
        }
        .metric-tooltip {
            font-size: 14px;
            cursor: help;
            margin-left: 6px;
        }
        @media (prefers-color-scheme: dark) {
            .metric-box {
                background-color: #0E1117;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 2px 8px rgba(255, 255, 255, 0.05);
                color: #fff;
            }
        }
        </style>
    """, unsafe_allow_html=True)


    # 🔢 Summary Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">Total Brands</div>
        <div class="metric-value">{get_total_unique_accounts(filtered_df)}</div></div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">🌍 Total Countries</div>
        <div class="metric-value">{get_total_countries(filtered_df)}</div></div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">📸 Total Volume</div>
        <div class="metric-value">{get_total_volume(filtered_df)}</div></div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">💬 Total Engagements</div>
        <div class="metric-value">{get_total_engagement(filtered_df)}</div></div>""", unsafe_allow_html=True)

    with col5:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">👥 Avg Post Engagement</div>
        <div class="metric-value">{get_average_post_engagement(filtered_df)}</div></div>""", unsafe_allow_html=True)

    with col6:
        st.markdown(f"""<div class="metric-box"><div class="metric-title">🌟 Reach</div>
        <div class="metric-value">{get_total_estimated_reach(filtered_df)}</div></div>""", unsafe_allow_html=True)

    # 📊 Tabs
    overall_tab, theme_tab, sub_theme_tab, sixthai_tab = st.tabs(["Overall", "Theme", "Sub Theme", "SixthAI"])

    with overall_tab:
        col1, col2 = st.columns(2)

        with col1:
            yearly_post_df = get_yearly_post_trend(filtered_df)
            fig = px.bar(yearly_post_df, x='year', y='post_count', title='📅 Yearly Post Volume (Last 5 Years)',
                         text='post_count', labels={'year': 'Year', 'post_count': 'Volume'})
            fig.update_layout(template="plotly_white", xaxis=dict(type='category'))
            fig.update_traces(textposition='outside', width=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            post_trend_df = get_post_trends_over_time(filtered_df)
            fig = px.line(post_trend_df, x='date', y='post_count', title='📈 Post Volume Over Time',
                          labels={'date': 'Date', 'post_count': 'Volume'},
                          markers=True)
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        engagement_df = get_engagement_trends_over_time(filtered_df)
        fig = px.line(engagement_df, x='date', y='engagement', title='📈Engagement Trend',
                      labels={'date': 'Date', 'engagement': 'Total Engagement'},
                      markers=True)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # 📊 Top 10 Accounts by Volume
        top_accounts_df = get_top_10_accounts_by_volume(filtered_df)
        fig = px.bar(top_accounts_df, x="username", y="post_count",
                    title="👤 Top 10 Brands by Post Volume",
                    text="post_count", color="username")
        fig.update_layout(template="plotly_white", xaxis_title="Brand", yaxis_title="Volume")
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with theme_tab:
        col1, col2 = st.columns(2)

        with col1:
            top_themes_df = get_top_themes(filtered_df)
            fig = px.bar(top_themes_df, x='theme', y='post_count', text='post_count',
                         title='Top 5 Most Frequent Themes', color='theme',
                         color_discrete_map=theme_color_map)
            fig.update_layout(template="plotly_white", xaxis_title="Theme", yaxis_title="Volume")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            theme_distribution_df = get_theme_distribution(filtered_df)
            fig = px.pie(theme_distribution_df, names='theme', values='post_count',
                         title='🎯 Theme-wise Post Distribution', hole=0.4,
                         color='theme', color_discrete_map=theme_color_map)
            fig.update_traces(textinfo='percent', pull=[0.03]*len(theme_distribution_df))
            st.plotly_chart(fig, use_container_width=True)

        top_theme_trend_df = get_top_theme_trends(filtered_df)
        fig = px.line(top_theme_trend_df, x='date', y='post_count', color='theme',
                      title='📅 Top 3 Themes - Post Trends Over Time',
                      labels={'date': 'Date', 'post_count': 'Volume'},
                      markers=True, color_discrete_map=theme_color_map)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fast_growth_df = get_fastest_growing_themes(filtered_df)
            fig = px.line(fast_growth_df, x='date', y='cumulative_post_count', color='theme',
                          title='🚀 Fastest Growing Themes Over Time',
                          labels={'date': 'Date', 'cumulative_post_count': 'Cumulative Volume'},
                          markers=True, color_discrete_map=theme_color_map)
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_growth_yearly_df = get_top_growing_themes_per_year(filtered_df)
            fig = px.bar(top_growth_yearly_df, x='year', y='growth', color='theme',
                         title='📊 Top 3 Fastest Growing Themes Per Year (Last 5 Years)',
                         barmode='group', color_discrete_map=theme_color_map)
            fig.update_layout(template="plotly_white", xaxis=dict(type='category'))
            st.plotly_chart(fig, use_container_width=True)

    with sub_theme_tab:
        col1, col2 = st.columns(2)

        with col1:
            top_sub_themes_df = get_top_sub_themes(filtered_df)
            fig = px.bar(top_sub_themes_df, x='matched_keyword', y='post_count',
                         title='Top 5 Most Frequent Sub Themes', text='post_count',
                         color='matched_keyword', color_discrete_map=sub_theme_color_map)
            fig.update_layout(template="plotly_white", xaxis_title="Sub Theme", yaxis_title="Volume")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            sub_theme_distribution_df = get_sub_theme_distribution(filtered_df)
            fig = px.pie(sub_theme_distribution_df, names='matched_keyword', values='post_count',
                         title='🎯 Sub Theme-wise Post Distribution', hole=0.4,
                         color='matched_keyword', color_discrete_map=sub_theme_color_map)
            fig.update_traces(textinfo='percent', pull=[0.03]*len(sub_theme_distribution_df))
            st.plotly_chart(fig, use_container_width=True)

        top_sub_theme_trend_df = get_top_sub_theme_trends(filtered_df)
        fig = px.line(top_sub_theme_trend_df, x='date', y='post_count', color='matched_keyword',
                      title='📅 Top 3 Sub Themes - Post Trends Over Time',
                      labels={'date': 'Date', 'post_count': 'Volume'},
                      markers=True, color_discrete_map=sub_theme_color_map)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fast_sub_growth_df = get_fastest_growing_sub_themes(filtered_df)
            fig = px.line(fast_sub_growth_df, x='date', y='cumulative_post_count', color='matched_keyword',
                          title='🚀 Fastest Growing Sub Themes Over Time',
                          labels={'date': 'Date', 'cumulative_post_count': 'Cumulative Volume'},
                          markers=True, color_discrete_map=sub_theme_color_map)
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            sub_theme_growth_yearly_df = get_top_growing_sub_themes_per_year(filtered_df)
            fig = px.bar(sub_theme_growth_yearly_df, x='year', y='growth', color='matched_keyword',
                         title='📊 Top 3 Fastest Growing Sub Themes Per Year (Last 5 Years)',
                         barmode='group', color_discrete_map=sub_theme_color_map)
            fig.update_layout(template="plotly_white", xaxis=dict(type='category'))
            st.plotly_chart(fig, use_container_width=True)

    with sixthai_tab:
        chat("cla")
