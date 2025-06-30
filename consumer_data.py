import pandas as pd
import numpy as np
from datetime import datetime


# Load data
df = pd.read_parquet("cla-realestate.parquet")

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

# Total number of posts
def get_total_volume(df):
    return format_number(len(df))

# Total number of unique countries
def get_total_countries(df):
    print(df['country'].nunique())
    return format_number(df['country'].nunique())

# Total engagement (likes + views + comments)
def get_total_engagement(df):
    return format_number(
        (df['post_likes'] + df['post_video_view_count'] + df['post_comments']).sum()
    )

def get_total_unique_accounts(df):
    return format_number(df['username'].nunique())


# Average engagement per post
def get_average_post_engagement(df):
    total_engagement = (df['post_likes'] + df['post_video_view_count'] + df['post_comments']).sum()
    total_posts = len(df)
    avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
    return format_number(avg_engagement)


def get_post_trends_over_time(df):
    # Ensure 'post_upload_date' is datetime
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')

    # Drop rows with invalid dates
    df = df.dropna(subset=['post_upload_date'])

    # ✅ Filter data from 2021 onwards
    df = df[df['post_upload_date'] >= pd.Timestamp('2021-01-01')]

    # Group by date
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

    yearly_post_counts = (
        df.groupby('year')
        .size()
        .reset_index(name='post_count')
    )

    return yearly_post_counts


def get_engagement_trends_over_time(df):
    # Ensure date format
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date'])

    # ✅ Filter data from 2021 onwards
    df = df[df['post_upload_date'] >= pd.Timestamp('2021-01-01')]

    # Fill NaNs in engagement fields
    df['post_likes'] = df['post_likes'].fillna(0)
    df['post_video_view_count'] = df['post_video_view_count'].fillna(0)
    df['post_comments'] = df['post_comments'].fillna(0)

    # Calculate total engagement per row
    df['engagement'] = df['post_likes'] + df['post_video_view_count'] + df['post_comments']

    # Group by date
    engagement_trend = (
        df.groupby(df['post_upload_date'].dt.date)['engagement']
        .sum()
        .reset_index()
        .rename(columns={'post_upload_date': 'date'})
    )

    return engagement_trend



def get_top_themes(df, top_n=5):
    top_themes = (
        df['matched_theme']
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    top_themes.columns = ['matched_theme', 'post_count']
    return top_themes



def get_theme_distribution(df):
    """
    Returns a DataFrame with theme-wise post count distribution
    suitable for pie chart visualization.
    """
    theme_distribution = (
        df['matched_theme']
        .value_counts(dropna=True)
        .reset_index()
    )
    theme_distribution.columns = ['matched_theme', 'post_count']
    return theme_distribution



def get_top_theme_trends(df, top_n=3):
    # Ensure datetime format
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_theme'])

    # Get top N themes
    top_themes = df['matched_theme'].value_counts().nlargest(top_n).index.tolist()

    # Filter for top themes only
    df_top = df[df['matched_theme'].isin(top_themes)]

    # Group by date and theme
    trend_df = (
        df_top.groupby([df_top['post_upload_date'].dt.date, 'matched_theme'])
        .size()
        .reset_index(name='post_count')
        .rename(columns={'post_upload_date': 'date'})
    )

    return trend_df


def get_fastest_growing_themes(df, top_n=3):
    import numpy as np

    # Clean and prepare
    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_theme'])

    # Group and compute daily post count
    grouped = (
        df.groupby([df['post_upload_date'].dt.date, 'matched_theme'])
        .size()
        .reset_index(name='daily_post_count')
        .rename(columns={'post_upload_date': 'date'})
    )

    # Sort and compute cumulative sum
    grouped = grouped.sort_values(by=['matched_theme', 'date'])
    grouped['cumulative_post_count'] = grouped.groupby('matched_theme')['daily_post_count'].cumsum()

    # Compute growth rate (slope over the full range of data)
    growth_rates = []
    for theme, group in grouped.groupby('matched_theme'):
        if len(group) >= 2:
            days = np.arange(len(group))
            values = group['cumulative_post_count'].values
            slope = np.polyfit(days, values, 1)[0]
            growth_rates.append((theme, slope))

    # Sort by slope
    fastest = sorted(growth_rates, key=lambda x: x[1], reverse=True)[:top_n]
    top_themes = [t[0] for t in fastest]

    # Filter original data for top themes
    result = grouped[grouped['matched_theme'].isin(top_themes)]

    return result



def get_top_growing_themes_per_year(df, top_n=3, last_n_years=5):
    import numpy as np
    from datetime import datetime

    df['post_upload_date'] = pd.to_datetime(df['post_upload_date'], errors='coerce')
    df = df.dropna(subset=['post_upload_date', 'matched_theme'])

    df['year'] = df['post_upload_date'].dt.year
    current_year = datetime.now().year
    recent_years = list(range(current_year - last_n_years + 1, current_year + 1))

    df = df[df['year'].isin(recent_years)]

    results = []

    for year in recent_years:
        yearly_df = df[df['year'] == year]

        # Daily cumulative post count
        grouped = (
            yearly_df.groupby([yearly_df['post_upload_date'].dt.date, 'matched_theme'])
            .size()
            .reset_index(name='daily_post_count')
            .sort_values(by=['matched_theme', 'post_upload_date'])
        )
        grouped['cumulative_post_count'] = grouped.groupby('matched_theme')['daily_post_count'].cumsum()

        # Calculate growth (end - start of cumulative)
        growth = grouped.groupby('matched_theme')['cumulative_post_count'].agg(['first', 'last']).reset_index()
        growth['growth'] = growth['last'] - growth['first']
        top_themes = growth.nlargest(top_n, 'growth')

        for _, row in top_themes.iterrows():
            results.append({
                'year': year,
                'matched_theme': row['matched_theme'],
                'growth': row['growth']
            })

    result_df = pd.DataFrame(results)
    return result_df


def get_theme_color_map(df):
    import plotly.express as px

    unique_themes = df['matched_theme'].dropna().unique()
    base_colors = px.colors.qualitative.Set3 + px.colors.qualitative.Bold + px.colors.qualitative.Dark24

    color_map = {theme: base_colors[i % len(base_colors)] for i, theme in enumerate(sorted(unique_themes))}
    return color_map


theme_color_map = get_theme_color_map(df)



# Sub themes

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
    from datetime import datetime

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
