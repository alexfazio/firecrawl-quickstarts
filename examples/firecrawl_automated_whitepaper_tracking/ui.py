import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import Database
from dotenv import dotenv_values

# Must be the first Streamlit command
st.set_page_config(page_title="HF Papers Tracker", page_icon="📚", layout="wide")

# Debug: Print environment info
st.write("Current working directory:", os.getcwd())
st.write("Files in directory:", os.listdir())

# Load environment variables using dotenv_values instead
config = dotenv_values(".env")
st.write("Loaded config:", {k: v for k, v in config.items() if 'POSTGRES' in k})

# Set environment variables manually
for key, value in config.items():
    os.environ[key] = value

# Debug: Print the database URL (mask password in production!)
db_url = os.getenv("POSTGRES_URL")
if not db_url:
    st.error("POSTGRES_URL is not set in environment variables")
    st.error("Please check if your .env file exists and contains POSTGRES_URL")
    st.stop()
else:
    st.success("Database URL found!")
    # Only show this in development!
    masked_url = db_url.replace(db_url.split("@")[0], "postgresql://****:****")
    st.write("Using database URL:", masked_url)

with st.spinner("Loading database..."):
    db = Database(os.getenv("POSTGRES_URL"))

# Main content
st.title("📚 HuggingFace Papers Dashboard")

# Add filters in the sidebar
with st.sidebar:
    st.title("Filters")
    days_filter = st.slider(
        "Show papers from last N days",
        min_value=1,
        max_value=30,
        value=7
    )
    min_upvotes = st.number_input(
        "Minimum upvotes",
        min_value=0,
        value=0
    )

# Get all papers and their metrics
papers = db.get_all_papers()

# Create a card for each paper
for paper in papers:
    metrics_history = db.get_paper_metrics(paper.url)
    if metrics_history:
        # Create DataFrame for plotting
        df = pd.DataFrame(
            [
                {
                    "timestamp": m.timestamp,
                    "upvotes": m.upvotes,
                    "comments": m.comments
                }
                for m in metrics_history
            ]
        )

        # Create a card-like container for each paper
        with st.expander(paper.title, expanded=False):
            st.markdown("---")
            
            # Paper metadata
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.markdown(f"**Authors:** {', '.join(paper.authors)}")
                st.markdown(f"**Published:** {paper.publication_date.strftime('%Y-%m-%d')}")
                
                # Metrics
                current_metrics = metrics_history[0]
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(
                        label="Upvotes",
                        value=current_metrics.upvotes,
                        delta=current_metrics.upvotes - metrics_history[-1].upvotes
                        if len(metrics_history) > 1 else None
                    )
                with col_b:
                    st.metric(
                        label="Comments",
                        value=current_metrics.comments,
                        delta=current_metrics.comments - metrics_history[-1].comments
                        if len(metrics_history) > 1 else None
                    )
                
                # Links
                st.markdown("### Links")
                if paper.pdf_url:
                    st.markdown(f"[📄 PDF]({paper.pdf_url})")
                if paper.arxiv_url:
                    st.markdown(f"[📝 arXiv]({paper.arxiv_url})")
                if paper.github_url:
                    st.markdown(f"[💻 GitHub]({paper.github_url})")

            with col2:
                # Abstract
                st.markdown("### Abstract")
                st.markdown(paper.abstract)
                
                # Metrics history plot
                if len(df) > 1:  # Only show plot if we have historical data
                    fig = px.line(
                        df,
                        x="timestamp",
                        y=["upvotes", "comments"],
                        title="Engagement Over Time"
                    )
                    fig.update_layout(
                        xaxis_title=None,
                        yaxis_title="Count",
                        legend_title=None,
                        margin=dict(l=0, r=0, t=30, b=0),
                        height=200
                    )
                    st.plotly_chart(fig, use_container_width=True)

st.write("Current working directory:", os.getcwd())
st.write("Files in directory:", os.listdir())
