import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression


def trajectory_analysis():
    st.title("📈 Real Estate Theme Trends")

    # --- Load and Merge Data ---
    @st.cache_data
    def load_data():
        df1 = pd.read_parquet("cla-realestate.parquet")
        df2 = pd.read_parquet("realestate_developers.parquet")
        df3 = pd.read_parquet("realestate_google_trends.parquet")

        df1 = df1.rename(columns={"matched_theme": "theme", "post_upload_date": "date"})
        df2 = df2.rename(columns={"post_upload_date": "date"})
        df3 = df3.rename(columns={"theme": "theme", "date": "date"})

        df1 = df1[["theme", "date"]]
        df2 = df2[["theme", "date"]]
        df3 = df3[["theme", "date"]]

        df_all = pd.concat([df1, df2, df3], ignore_index=True)
        df_all = df_all.dropna(subset=["theme", "date"])
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_all = df_all[df_all["date"] >= "2021-01-01"]
        df_all["month"] = df_all["date"].dt.to_period("M").astype(str)

        return df_all

    df = load_data()

    # --- Monthly Counts ---
    monthly_counts = df.groupby(["theme", "month"]).size().reset_index(name="count")

    # --- Volume & Growth Calculation ---
    volume_df = (
        monthly_counts.groupby("theme")["count"]
        .sum()
        .reset_index()
        .rename(columns={"count": "total_volume"})
    )

    growth_data = []
    for theme in monthly_counts["theme"].unique():
        df_t = monthly_counts[monthly_counts["theme"] == theme].copy()
        df_t["month_num"] = pd.to_datetime(df_t["month"]).map(lambda x: x.toordinal())
        if len(df_t) > 1:
            model = LinearRegression().fit(df_t[["month_num"]], df_t["count"])
            slope = model.coef_[0]
            growth_data.append((theme, slope))

    growth_df = pd.DataFrame(growth_data, columns=["theme", "growth_slope"])

    # --- Merge Volume + Growth ---
    merged = pd.merge(volume_df, growth_df, on="theme", how="inner")
    merged["volume_score"] = merged["total_volume"].rank(pct=True)
    merged["growth_score"] = merged["growth_slope"].rank(pct=True)
    merged["combined_score"] = merged["volume_score"] + merged["growth_score"]

    # --- 1. High Volume + High Growth ---
    top_themes = merged.sort_values("combined_score", ascending=False).head(3)
    df_top_plot = monthly_counts[monthly_counts["theme"].isin(top_themes["theme"])]

    st.subheader("📊 Top 3 Themes: High Volume + High Growth")
    fig1 = px.line(
        df_top_plot,
        x="month",
        y="count",
        color="theme",
        markers=True,
        title="Top 3 Themes by Volume & Growth"
    )
    fig1.update_layout(hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("### 📌 High Growth Theme Summary")
    st.dataframe(
        top_themes[["theme", "total_volume", "growth_slope", "combined_score"]]
        .set_index("theme")
        .sort_values("combined_score", ascending=False),
        use_container_width=True
    )

    # --- 2. High Volume + Low Growth ---
    low_growth = merged.sort_values(["total_volume", "growth_slope"], ascending=[False, True]).head(3)
    df_low_growth_plot = monthly_counts[monthly_counts["theme"].isin(low_growth["theme"])]

    st.subheader("📉 Top 3 Themes: High Volume + Low Growth")
    fig2 = px.line(
        df_low_growth_plot,
        x="month",
        y="count",
        color="theme",
        markers=True,
        title="Top 3 Volume Themes That Are Slowing Down"
    )
    fig2.update_layout(hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 📌 Slow Growth Theme Summary")
    st.dataframe(
        low_growth[["theme", "total_volume", "growth_slope"]]
        .set_index("theme")
        .sort_values("total_volume", ascending=False),
        use_container_width=True
    )

    # --- 3. Low Volume + High Growth (Emerging Themes) ---
    low_vol_cutoff = merged["total_volume"].quantile(0.25)
    emerging_pool = merged[merged["total_volume"] <= low_vol_cutoff]
    emerging = emerging_pool.sort_values("growth_slope", ascending=False).head(3)

    df_emerging_plot = monthly_counts[monthly_counts["theme"].isin(emerging["theme"])]

    st.subheader("🚀 Emerging Themes: Low Volume + High Growth")
    fig3 = px.line(
        df_emerging_plot,
        x="month",
        y="count",
        color="theme",
        markers=True,
        title="Top 3 Emerging Themes"
    )
    fig3.update_layout(hovermode="x unified")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 🌱 Emerging Theme Summary")
    st.dataframe(
        emerging[["theme", "total_volume", "growth_slope"]]
        .set_index("theme")
        .sort_values("growth_slope", ascending=False),
        use_container_width=True
    )


    # --- 4. Low Volume + Low Growth (Stagnant Themes) ---
    stagnant_themes = (
        merged.sort_values(["total_volume", "growth_slope"], ascending=[True, True])
        .head(3)
    )
    df_stagnant_plot = monthly_counts[monthly_counts["theme"].isin(stagnant_themes["theme"])]

    st.subheader("😴 Quiet Themes: Low Volume + Low Growth")
    fig4 = px.line(
        df_stagnant_plot,
        x="month",
        y="count",
        color="theme",
        markers=True,
        title="Top 3 Quiet Themes (Low Engagement & No Growth)"
    )
    fig4.update_layout(hovermode="x unified")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("### 💤 Quiet Theme Summary")
    st.dataframe(
        stagnant_themes[["theme", "total_volume", "growth_slope"]]
        .set_index("theme")
        .sort_values("total_volume", ascending=True),
        use_container_width=True
    )

