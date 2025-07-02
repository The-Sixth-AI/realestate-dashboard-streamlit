import streamlit as st

st.set_page_config(page_title="Realestate Dashboard", layout="wide")

from bla_analysis import bla


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
with st.sidebar:
    page = st.sidebar.radio("📊 Select Dashboard", ["Search Trends", "Brand Led Analysis", "Consumer Led Analysis", "Trend Trajectory"])


if page == "Search Trends":
    st.write("Search Trends Page")

elif page == "Brand Led Analysis":
    bla()

elif page == "Consumer Led Analysis":
    st.write("Consumer Led Analysis Page")

elif page == "Trend Trajectory":
    st.write("Trend Trajectory Page")