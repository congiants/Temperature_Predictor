import joblib
import pandas as pd
from database import engine
from sqlalchemy import text
from datetime import timedelta

GET_AGG_SQL = """ 
SELECT DISTINCT ON (device_id) *
    FROM dht22_aggregate
    WHERE date < CURRENT_DATE
    ORDER BY device_id, date DESC
"""

ISERT_PRED_SQL = """ 
INSERT INTO prediction (device_id, based_on_date, target_date, temp_c_max, temp_c_min, model)
    VALUES (:device_id, :based_on_date, :target_date, :temp_c_max, :temp_c_min, :model)
    ON CONFLICT (device_id, based_on_date, target_date)
    DO UPDATE SET temp_c_max = EXCLUDED.temp_c_max, temp_c_min = EXCLUDED.temp_c_min, model = EXCLUDED.model
"""

prediction_model = "ridge_v1"


model = joblib.load("../models/ridge_v1.joblib")


latest_agg = pd.read_sql(text(GET_AGG_SQL), engine)

predictors_max = latest_agg[model["predictors_max"]]
predictors_min = latest_agg[model["predictors_min"]]

daily_predictions = []
for i in range(7):           
    max_prediction = model["max"][i].predict(predictors_max)
    min_prediction = model["min"][i].predict(predictors_min)
    daily_predictions.append(pd.DataFrame({
    "device_id":latest_agg["device_id"],  
    "based_on_date":latest_agg["date"],
    "target_date":latest_agg["date"] + timedelta(days=i+1),
    "temp_c_max": max_prediction,
    "temp_c_min": min_prediction,
    "model":prediction_model,
    }))

forecast = pd.concat(daily_predictions)
forecast = forecast.to_dict("records")

with engine.begin() as conn:
    result = conn.execute(text(ISERT_PRED_SQL), forecast)
    print(f"Upserted {result.rowcount} rows")