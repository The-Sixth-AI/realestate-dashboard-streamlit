import pandas as pd
import numpy as np
from datetime import datetime


# Load data
df = pd.read_parquet("realestate_developers.parquet")


# Utility to format large numbers
def format_number(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(int(num))

def get_top_10_accounts_by_volume(df):
    return (
        df.groupby("username")
        .size()
        .reset_index(name="post_count")
        .sort_values(by="post_count", ascending=False)
        .head(10)
    )

def get_total_volume(df):
    return format_number(len(df))


def get_total_countries(df):
    return format_number(df['country'].nunique())


def get_total_engagement(df):
    return format_number(
        (df['post_likes'] + df['post_video_view_count'] + df['post_comments']).sum()
    )


def get_total_unique_accounts(df):
    return format_number(df['username'].nunique())

def estimate_post_reach_row(row):
    likes = row.get("post_likes", 0) or 0
    comments = row.get("post_comments", 0) or 0
    views = row.get("post_video_view_count", 0) or 0
    followers = row.get("followers", 0) or 0

    engagement = likes + comments + views
    return (0.1 * followers) + (0.05 * engagement)


def get_total_estimated_reach(df):
    df = df.copy()
    df['estimated_reach'] = df.apply(estimate_post_reach_row, axis=1)
    return format_number(df['estimated_reach'].sum())


def get_average_post_engagement(df):
    total_engagement = (df['post_likes'] + df['post_video_view_count'] + df['post_comments']).sum()
    total_posts = len(df)
    avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
    return format_number(avg_engagement)


def get_post_trends_over_time(df):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date'])
    post_trend = (
        df.groupby(df['post_upload_date'].dt.date)
        .size()
        .reset_index(name='post_count')
        .rename(columns={'post_upload_date': 'date'})
    )
    return post_trend


def get_yearly_post_trend(df, last_n_years=5):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date'])
    df['year'] = df['post_upload_date'].dt.year
    current_year = datetime.now().year
    recent_years = list(range(current_year - last_n_years + 1, current_year + 1))
    df = df[df['year'].isin(recent_years)]
    yearly_post_counts = df.groupby('year').size().reset_index(name='post_count')
    return yearly_post_counts


def get_engagement_trends_over_time(df):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date'])
    df['post_likes'] = df['post_likes'].fillna(0)
    df['post_video_view_count'] = df['post_video_view_count'].fillna(0)
    df['post_comments'] = df['post_comments'].fillna(0)
    df['engagement'] = df['post_likes'] + df['post_video_view_count'] + df['post_comments']
    engagement_trend = (
        df.groupby(df['post_upload_date'].dt.date)['engagement']
        .sum()
        .reset_index()
        .rename(columns={'post_upload_date': 'date'})
    )
    return engagement_trend


def get_top_themes(df, top_n=5):
    top_themes = (
        df['theme']
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    top_themes.columns = ['theme', 'post_count']
    return top_themes


def get_theme_distribution(df):
    theme_distribution = (
        df['theme']
        .value_counts(dropna=True)
        .reset_index()
    )
    theme_distribution.columns = ['theme', 'post_count']
    return theme_distribution


def get_top_theme_trends(df, top_n=3):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'theme'])
    top_themes = df['theme'].value_counts().nlargest(top_n).index.tolist()
    df_top = df[df['theme'].isin(top_themes)]
    trend_df = (
        df_top.groupby([df_top['post_upload_date'].dt.date, 'theme'])
        .size()
        .reset_index(name='post_count')
        .rename(columns={'post_upload_date': 'date'})
    )
    return trend_df


def get_fastest_growing_themes(df, top_n=3):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'theme'])
    grouped = (
        df.groupby([df['post_upload_date'].dt.date, 'theme'])
        .size()
        .reset_index(name='daily_post_count')
        .rename(columns={'post_upload_date': 'date'})
    )
    grouped = grouped.sort_values(by=['theme', 'date'])
    grouped['cumulative_post_count'] = grouped.groupby('theme')['daily_post_count'].cumsum()
    growth_rates = []
    for theme, group in grouped.groupby('theme'):
        if len(group) >= 2:
            days = np.arange(len(group))
            values = group['cumulative_post_count'].values
            slope = np.polyfit(days, values, 1)[0]
            growth_rates.append((theme, slope))
    fastest = sorted(growth_rates, key=lambda x: x[1], reverse=True)[:top_n]
    top_themes = [t[0] for t in fastest]
    result = grouped[grouped['theme'].isin(top_themes)]
    return result


def get_top_growing_themes_per_year(df, top_n=3, last_n_years=5):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'theme'])
    df['year'] = df['post_upload_date'].dt.year
    current_year = datetime.now().year
    recent_years = list(range(current_year - last_n_years + 1, current_year + 1))
    df = df[df['year'].isin(recent_years)]
    results = []
    for year in recent_years:
        yearly_df = df[df['year'] == year]
        grouped = (
            yearly_df.groupby([yearly_df['post_upload_date'].dt.date, 'theme'])
            .size()
            .reset_index(name='daily_post_count')
            .sort_values(by=['theme', 'post_upload_date'])
        )
        grouped['cumulative_post_count'] = grouped.groupby('theme')['daily_post_count'].cumsum()
        growth = grouped.groupby('theme')['cumulative_post_count'].agg(['first', 'last']).reset_index()
        growth['growth'] = growth['last'] - growth['first']
        top_themes = growth.nlargest(top_n, 'growth')
        for _, row in top_themes.iterrows():
            results.append({
                'year': year,
                'theme': row['theme'],
                'growth': row['growth']
            })
    return pd.DataFrame(results)


def get_theme_color_map(df):
    import plotly.express as px
    unique_themes = df['theme'].dropna().unique()
    base_colors = px.colors.qualitative.Set3 + px.colors.qualitative.Bold + px.colors.qualitative.Dark24
    return {theme: base_colors[i % len(base_colors)] for i, theme in enumerate(sorted(unique_themes))}


theme_color_map = get_theme_color_map(df)


def get_sub_theme_color_map(df):
    import plotly.express as px
    unique_keywords = df['matched_keyword'].dropna().unique()
    base_colors = px.colors.qualitative.Set3 + px.colors.qualitative.Bold + px.colors.qualitative.Dark24
    return {k: base_colors[i % len(base_colors)] for i, k in enumerate(sorted(unique_keywords))}


sub_theme_color_map = get_sub_theme_color_map(df)


def get_top_sub_themes(df, top_n=5):
    top_keywords = (
        df['matched_keyword']
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    top_keywords.columns = ['matched_keyword', 'post_count']
    return top_keywords


def get_sub_theme_distribution(df, top_n=10):
    distribution = (
        df['matched_keyword']
        .value_counts(dropna=True)
        .head(top_n)
        .reset_index()
    )
    distribution.columns = ['matched_keyword', 'post_count']
    return distribution


def get_top_sub_theme_trends(df, top_n=3):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_keyword'])
    top_keywords = df['matched_keyword'].value_counts().nlargest(top_n).index.tolist()
    df_top = df[df['matched_keyword'].isin(top_keywords)]
    trend_df = (
        df_top.groupby([df_top['post_upload_date'].dt.date, 'matched_keyword'])
        .size()
        .reset_index(name='post_count')
        .rename(columns={'post_upload_date': 'date'})
    )
    return trend_df


def get_fastest_growing_sub_themes(df, top_n=3):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_keyword'])
    grouped = (
        df.groupby([df['post_upload_date'].dt.date, 'matched_keyword'])
        .size()
        .reset_index(name='daily_post_count')
        .rename(columns={'post_upload_date': 'date'})
    )
    grouped = grouped.sort_values(by=['matched_keyword', 'date'])
    grouped['cumulative_post_count'] = grouped.groupby('matched_keyword')['daily_post_count'].cumsum()
    growth_rates = []
    for keyword, group in grouped.groupby('matched_keyword'):
        if len(group) >= 2:
            days = np.arange(len(group))
            values = group['cumulative_post_count'].values
            slope = np.polyfit(days, values, 1)[0]
            growth_rates.append((keyword, slope))
    fastest = sorted(growth_rates, key=lambda x: x[1], reverse=True)[:top_n]
    top_keywords = [k[0] for k in fastest]
    result = grouped[grouped['matched_keyword'].isin(top_keywords)]
    return result


def get_top_growing_sub_themes_per_year(df, top_n=3, last_n_years=5):
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_keyword'])
    df['year'] = df['post_upload_date'].dt.year
    current_year = datetime.now().year
    recent_years = list(range(current_year - last_n_years + 1, current_year + 1))
    df = df[df['year'].isin(recent_years)]
    results = []
    for year in recent_years:
        yearly_df = df[df['year'] == year]
        grouped = (
            yearly_df.groupby([yearly_df['post_upload_date'].dt.date, 'matched_keyword'])
            .size()
            .reset_index(name='daily_post_count')
            .sort_values(by=['matched_keyword', 'post_upload_date'])
        )
        grouped['cumulative_post_count'] = grouped.groupby('matched_keyword')['daily_post_count'].cumsum()
        growth = grouped.groupby('matched_keyword')['cumulative_post_count'].agg(['first', 'last']).reset_index()
        growth['growth'] = growth['last'] - growth['first']
        top_keywords = growth.nlargest(top_n, 'growth')
        for _, row in top_keywords.iterrows():
            results.append({
                'year': year,
                'matched_keyword': row['matched_keyword'],
                'growth': row['growth']
            })
    return pd.DataFrame(results)
