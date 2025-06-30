import colorsys
import math
import random
import streamlit as st

# ------------------------------
# Page Configuration
# ------------------------------
st.set_page_config(page_title="Realestate Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.colors as pc
from consume_analysis import cla
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sklearn.cluster import KMeans
import numpy as np
from chat import chat
from bla_analysis import bla
from trajectory_analysis import trajectory_analysis

# ------------------------------
# Navbar HTML
# ------------------------------
navbar_html = """
<style>
.navbar {
    position: fixed;
    width: 100%;
    top: 40px;
    font-family: 'Arial', sans-serif;
    font-weight: bold;
    font-size: 28px;
    text-align: left;
    padding: 1rem 0;
    z-index: 999;
    transition: background-color 0.3s, color 0.3s;
    background-color: #FFFFFF;
    color: black;
}
@media (prefers-color-scheme: dark) {
    .navbar {
        background-color: #0E1117;
        color: white;
    }
    .s { color: #CCCCCC; }
    .i { color: #00BCD4; }
    .x { color: #4FC3F7; }
    .t { color: #909090; }
    .h { color: #CCCCCC; }
    .ai { color: #AAAAAA; }
}
.s { color: #606060; }
.i { color: #00BCD4; }
.x { color: #0088C2; }
.t { color: #303030; }
.h { color: #606060; }
.ai { color: #A0A0A0; }
.stApp {
    padding-top: 0rem;
}
</style>
<div class="navbar">
  <span class="ai">T</span>
  <span class="ai">H</span>
  <span class="ai">E</span>
  <span class="s">S</span>
  <span class="i">I</span>
  <span class="x">X</span>
  <span class="t">T</span>
  <span class="h">H</span>
  <span class="ai">.</span>
  <span class="ai">A</span>
  <span class="ai">I</span>
</div>
<br/><br/><br/>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

# ------------------------------
# Sidebar Navigation
# ------------------------------
page = st.sidebar.radio("📊 Select Dashboard", ["Search Trends", "Brand Led Analysis", "Consumer Led Analysis", "Trend Trajectory"])

# ------------------------------
# Load Data Once (cached)
# ------------------------------
@st.cache_data
def load_data():
    df = pd.read_parquet("realestate_google_trends.parquet")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

df = load_data()


# import os
# os.environ["GEMINI_API_KEY"] = "AIzaSyB8YE6UDTnljAx145_hkq6SqAfixsIjdzY"

# llm = LiteLLM(model="gemini/gemini-2.5-flash-preview-04-17")

# # Set your OpenAI API key
# pai.config.set({"llm": llm})

if page == "Trend Trajectory":
    trajectory_analysis()

elif page == "Consumer Led Analysis":
    cla()

elif page == "Brand Led Analysis":
    bla()

# ------------------------------
# Search Trends Page
# ------------------------------
elif page == "Search Trends":


    if df.empty:
        st.warning("No data available.")
        st.stop()

    # Prepare options
    themes = sorted(df["theme"].dropna().unique().tolist())
    subthemes = sorted(df["keyword"].dropna().unique().tolist())
    countries = sorted(df["country"].dropna().unique().tolist())

    min_date, max_date = df["date"].min(), df["date"].max()

    # -----------------------------
    # Initialize session state (only if not set)
    # -----------------------------
    if "theme" not in st.session_state:
        st.session_state["theme"] = "All"
    if "country" not in st.session_state:
        st.session_state["country"] = "All"
    if "subtheme" not in st.session_state:
        st.session_state["subtheme"] = "All"
    if "date_range" not in st.session_state:
        st.session_state["date_range"] = (min_date, max_date)

    
    # -----------------------------
    # Filter widgets (no value=, just key=)
    # -----------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("🎨 Select Theme", ["All"] + themes, key="theme")
    with col2:
        st.selectbox("🌍 Select Country", ["All"] + countries, key="country")

    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("🧩 Select Sub Theme", ["All"] + subthemes, key="subtheme")
    with col4:
        st.date_input("📅 Select Date Range", key="date_range")
    

    # -----------------------------
    # Reset button
    # -----------------------------
    if st.button("🔄 Reset Filters"):
        st.session_state["theme"] = "All"
        st.session_state["country"] = "All"
        st.session_state["subtheme"] = "All"
        st.session_state["date_range"] = (min_date, max_date)
        st.experimental_rerun()


    # -----------------------------
    # Apply filters
    # -----------------------------
    filtered_df = df.copy()

    if st.session_state["theme"] != "All":
        filtered_df = filtered_df[filtered_df["theme"] == st.session_state["theme"]]
    if st.session_state["country"] != "All":
        filtered_df = filtered_df[filtered_df["country"] == st.session_state["country"]]
    if st.session_state["subtheme"] != "All":
        filtered_df = filtered_df[filtered_df["keyword"] == st.session_state["subtheme"]]

    # Ensure it's a date range
    if isinstance(st.session_state["date_range"], tuple) and len(st.session_state["date_range"]) == 2:
        start_date, end_date = pd.to_datetime(st.session_state["date_range"][0]), pd.to_datetime(st.session_state["date_range"][1])
        filtered_df = filtered_df[(filtered_df["date"] >= start_date) & (filtered_df["date"] <= end_date)]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    # Create consistent color maps
    unique_themes = filtered_df["theme"].dropna().unique()
    unique_keywords = filtered_df["keyword"].dropna().unique()

    
    def assign_distinct_colors(items):
        """Generate maximally distinct colors using perceptual color distance"""
        n_items = len(items)
        colors = []
        
        # Pre-defined highly distinct colors for common cases
        distinct_colors = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
            "#800000", "#008000", "#000080", "#808000", "#800080", "#008080",
            "#FFA500", "#A52A2A", "#DDA0DD", "#98FB98", "#F0E68C", "#DEB887",
            "#5F9EA0", "#FF1493", "#00CED1", "#FF4500", "#2E8B57", "#DAA520",
            "#9932CC", "#8B4513", "#228B22", "#DC143C", "#00BFFF", "#696969",
            "#FF6347", "#40E0D0", "#EE82EE", "#90EE90", "#FFB6C1", "#20B2AA",
            "#87CEEB", "#778899", "#B0C4DE", "#FFFFE0", "#32CD32", "#FAF0E6"
        ]
        
        if n_items <= len(distinct_colors):
            selected_colors = distinct_colors[:n_items]
        else:
            # Use predefined colors first, then generate more
            selected_colors = distinct_colors[:]
            
            # Generate additional colors with maximum separation
            remaining = n_items - len(distinct_colors)
            
            for i in range(remaining):
                # Use prime number spacing for better distribution
                hue = (i * 83) % 360 / 360.0  # 83 is prime
                
                # Alternate between high and low saturation/value
                if i % 4 == 0:
                    sat, val = 1.0, 0.8
                elif i % 4 == 1:
                    sat, val = 0.6, 1.0
                elif i % 4 == 2:
                    sat, val = 0.8, 0.6
                else:
                    sat, val = 1.0, 1.0
                    
                rgb = colorsys.hsv_to_rgb(hue, sat, val)
                hex_color = '#{:02x}{:02x}{:02x}'.format(
                    int(rgb[0] * 255), 
                    int(rgb[1] * 255), 
                    int(rgb[2] * 255)
                )
                
                # Ensure this color is sufficiently different from existing ones
                min_distance = min([color_distance(hex_color, existing) 
                                for existing in selected_colors])
                
                if min_distance > 50:  # Minimum perceptual distance
                    selected_colors.append(hex_color)
                else:
                    # Try a completely different approach for this color
                    hue = (i * 137 + 45) % 360 / 360.0
                    sat = 0.9 if i % 2 == 0 else 0.7
                    val = 0.9 if (i // 2) % 2 == 0 else 0.7
                    
                    rgb = colorsys.hsv_to_rgb(hue, sat, val)
                    hex_color = '#{:02x}{:02x}{:02x}'.format(
                        int(rgb[0] * 255), 
                        int(rgb[1] * 255), 
                        int(rgb[2] * 255)
                    )
                    selected_colors.append(hex_color)
        
        return {item: selected_colors[i] for i, item in enumerate(items)}

    def color_distance(color1, color2):
        """Calculate perceptual distance between two hex colors"""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        
        # Simple perceptual distance formula
        return math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)

    # Apply color mapping
    keyword_color_map = assign_distinct_colors(unique_keywords)
    theme_color_map = assign_distinct_colors(unique_themes)



    tab1, tab2, tab3 = st.tabs(["Theme", "Sub Theme", "Ask SixthAI"])

    # ------------------------------
    # THEME ANALYSIS
    # ------------------------------
    with tab1:
        theme_avg = filtered_df.groupby("theme", as_index=False)["value"].mean()

        col1, col2 = st.columns(2)

        # Top 5 Themes by Average Interest
        with col1:
            top_5 = theme_avg.sort_values("value", ascending=False).head(5)
            fig = px.bar(top_5, x="theme", y="value", color="theme", 
                        title="Top 5 Themes by Average Interest",
                        color_discrete_map=theme_color_map)
            fig.update_layout(showlegend=False, yaxis_tickformat=".0f", bargap=0.5)
            st.plotly_chart(fig, use_container_width=True)

        # Theme Distribution
        with col2:
            # Prepare data sorted by value
            pie_df = theme_avg.query("value > 0").sort_values("value", ascending=False)

            # Create color map only for themes in the sorted pie chart
            top_themes = pie_df["theme"].tolist()
            top_theme_color_map = {theme: theme_color_map[theme] for theme in top_themes}

            # Create the pie chart
            fig = px.pie(
                pie_df,
                names="theme",
                values="value",
                hole=0.4,
                title="Theme Distribution",
                color="theme",
                color_discrete_map=top_theme_color_map,
                category_orders={"theme": top_themes}  # enforces the correct order
            )
            fig.update_traces(textinfo="percent", pull=[0.03]*len(pie_df))
            st.plotly_chart(fig, use_container_width=True)

        # Top 3 Themes – Trend Over Time
        theme_time = filtered_df.groupby(["theme", "date"], as_index=False)["value"].mean()
        theme_avg = theme_time.groupby("theme", as_index=False)["value"].mean()
        top_themes = theme_avg.sort_values("value", ascending=False).head(3)["theme"]
        trend_df = filtered_df[filtered_df["theme"].isin(top_themes)]
        trend_df = trend_df.groupby(["date", "theme"], as_index=False)["value"].mean()
        fig = px.line(trend_df, x="date", y="value", color="theme",
                    title="Top 3 Themes – Trend Over Time",
                    line_shape="spline",
                    color_discrete_map=theme_color_map)
        st.plotly_chart(fig, use_container_width=True)

        # Fastest Growing Themes
        growth_theme = theme_time.sort_values("date").groupby("theme").agg(
            start_value=("value", "first"),
            end_value=("value", "last")
        )
        growth_theme["growth"] = growth_theme["end_value"] - growth_theme["start_value"]
        top_theme_growers = growth_theme.sort_values("growth", ascending=False).head(3).index.tolist()
        grow_theme_df = theme_time[theme_time["theme"].isin(top_theme_growers)]
        fig = px.line(grow_theme_df, x="date", y="value", color="theme",
                    title="📈 Top 3 Fastest Growing Themes",
                    line_shape="spline",
                    color_discrete_map=theme_color_map)
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------
    # KEYWORD ANALYSIS
    # ------------------------------
    with tab2:

        col1, col2 = st.columns(2)

        # Top 15 Keywords by Average Interest
        keyword_avg = filtered_df.groupby("keyword", as_index=False)["value"].mean()
        with col1:
            top_keywords = keyword_avg.sort_values("value", ascending=False).head(5)
            fig = px.bar(top_keywords, x="keyword", y="value", color="keyword",
                        title="Top 5 Sub Themes by Average Interest",
                        color_discrete_map=keyword_color_map)
            fig.update_layout(showlegend=False, yaxis_tickformat=".0f", bargap=0.4, xaxis_title="Sub Theme")
            st.plotly_chart(fig, use_container_width=True)

        # Keyword Distribution
        with col2:
            # Sort and take top N
            TOP_N = 15
            pie_kw_df = keyword_avg.sort_values("value", ascending=False).head(TOP_N)

            # Create a color map just for the top N keywords
            top_keywords = pie_kw_df["keyword"].tolist()
            top_kw_color_map = {kw: keyword_color_map[kw] for kw in top_keywords}

            # Create the pie chart
            fig = px.pie(
                pie_kw_df,
                names="keyword",
                values="value",
                hole=0.4,
                title=f"Top {TOP_N} Sub Themes Distribution",
                color="keyword",
                color_discrete_map=top_kw_color_map,
                category_orders={"keyword": top_keywords}  # preserves value order
            )
            fig.update_traces(textinfo="percent", pull=[0.03]*len(pie_kw_df))
            st.plotly_chart(fig, use_container_width=True)

        # Top 3 Keywords – Trend Over Time
        keyword_time = filtered_df.groupby(["keyword", "date"], as_index=False)["value"].mean()
        keyword_avg = keyword_time.groupby("keyword", as_index=False)["value"].mean()
        top_3_kw = keyword_avg.sort_values("value", ascending=False).head(3)["keyword"]
        trend_kw_df = filtered_df[filtered_df["keyword"].isin(top_3_kw)]
        trend_kw_df = trend_kw_df.groupby(["date", "keyword"], as_index=False)["value"].mean()
        fig = px.line(trend_kw_df, x="date", y="value", color="keyword",
                    title="Top 3 Sub Themes – Trend Over Time",
                    line_shape="spline",
                    color_discrete_map=keyword_color_map)
        st.plotly_chart(fig, use_container_width=True)


        # Convert date to numeric for regression
        keyword_time["t"] = keyword_time["date"].map(pd.Timestamp.toordinal)

        # Calculate slope (growth rate) for each keyword
        keyword_growth_slopes = []
        for kw, group in keyword_time.groupby("keyword"):
            if len(group) < 2:
                continue  # Skip if not enough data points
            X = group["t"].values.reshape(-1, 1)
            y = group["value"].values
            model = LinearRegression().fit(X, y)
            slope = model.coef_[0]
            keyword_growth_slopes.append((kw, slope))

        # Select top 3 keywords by slope
        top_kw_growers = [k[0] for k in sorted(keyword_growth_slopes, key=lambda x: x[1], reverse=True)[:3]]

        # Plot
        grow_df = keyword_time[keyword_time["keyword"].isin(top_kw_growers)]
        fig = px.line(grow_df, x="date", y="value", color="keyword",
                    title="📈 Top 3 Fastest Growing Sub Themes",
                    line_shape="spline",
                    color_discrete_map=keyword_color_map)
        st.plotly_chart(fig, use_container_width=True)
    

    
    with tab3:
        chat("trends")
        

        with st.expander("Suggested Questions"):
            st.write("1. what are the top 3 keywords in the last 6 months.?")
            st.write("2. What are the most searched themes in 2023?")
            st.write("3. What are the top 3 keywords in the last 6 months for the theme 'amenities' in 'united kingdom'?")