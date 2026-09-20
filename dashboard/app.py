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
