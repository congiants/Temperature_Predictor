import streamlit as st
import requests

import pandas as pd

st.title("Temperature Predictor")

response = requests.get("http://localhost:8000/devices")
devices = response.json()

chosen = st.selectbox("Pick a device", devices)
st.write("You picked:", chosen["device_id"])

readings = requests.get("http://localhost:8000/readings", params={"device_id": chosen["device_id"], "limit": 500}).json()
if len(readings) == 0:
    st.info("No readings yet")
else:
    df = pd.DataFrame(readings)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.set_index("ts")
    st.line_chart(df[["temp_c", "humidity"]])

st.subheader("7-day forecast")
forecast = requests.get("http://localhost:8000/prediction", params={"device_id": chosen["device_id"]}).json()
if len(forecast) == 0:
    st.info("No forecast yet")
else:
    df = pd.DataFrame(forecast)
    df["target_date"] = pd.to_datetime(df["target_date"])
    df = df.set_index("target_date")
    st.write("Based on data up to:", forecast[0]["based_on_date"])
    st.line_chart(df[["temp_c_max", "temp_c_min"]])