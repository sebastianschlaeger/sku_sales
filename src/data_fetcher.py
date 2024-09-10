import streamlit as st
from datetime import datetime, timedelta
from src.s3_operations import get_missing_dates, update_data

def fetch_and_save_missing_data(overwrite_data):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    start_date = yesterday - timedelta(days=30)
    missing_dates = get_missing_dates(start_date, yesterday)

    if missing_dates:
        total_dates = len(missing_dates)
        progress_bar = st.progress(0)
        for i, date in enumerate(missing_dates):
            st.write(f"Processing date {date} ({i+1}/{total_dates})")
            update_data(date, overwrite_data)
            progress = (i + 1) / total_dates
            progress_bar.progress(progress)
        st.success(f"Data fetched and saved successfully for {total_dates} dates!")
        st.rerun()  # Add this line to rerun the app
    else:
        st.info("No missing data to fetch.")