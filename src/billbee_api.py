import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class BillbeeAPI:
    BASE_URL = "https://api.billbee.io/api/v1"

    def __init__(self):
        self.api_key = st.secrets["billbee"]["API_KEY"]
        self.username = st.secrets["billbee"]["USERNAME"]
        self.password = st.secrets["billbee"]["PASSWORD"]

    def get_orders(self, start_date, end_date):
        endpoint = f"{self.BASE_URL}/orders"
        headers = {
            "X-Billbee-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        params = {
            "minOrderDate": start_date.isoformat(),
            "maxOrderDate": end_date.isoformat(),
            "pageSize": 250  # Max page size
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params, auth=(self.username, self.password))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error querying Billbee API: {str(e)}")
            return {"Data": []}  # Return empty data instead of raising

billbee_api = BillbeeAPI()