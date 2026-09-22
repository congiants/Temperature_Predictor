from database import engine
from sqlalchemy import text

DAILY_AGG_SQL = """ 
INSERT INTO dht22_aggregate (device_id, date, temp_c_min, temp_c_max,
                             humidity_min, humidity_max, temp_c_avg,
                             humidity_avg, reading_count)
SELECT device_id,
       ts::date AS date,
       MIN(temp_c) AS temp_c_min,
       MAX(temp_c) AS temp_c_max,
       MIN(humidity) AS humidity_min,
       MAX(humidity) AS humidity_max,
       ROUND(AVG(temp_c), 2) AS temp_c_avg,
       ROUND(AVG(humidity), 2) AS humidity_avg,

       COUNT(*) AS reading_count
FROM dht22
GROUP BY device_id, ts::date
ON CONFLICT (device_id, date) DO UPDATE SET
    temp_c_min = EXCLUDED.temp_c_min,
    temp_c_max = EXCLUDED.temp_c_max,
    humidity_min = EXCLUDED.humidity_min,
    humidity_max = EXCLUDED.humidity_max,
    temp_c_avg = EXCLUDED.temp_c_avg,
    humidity_avg = EXCLUDED.humidity_avg,
    reading_count = EXCLUDED.reading_count
"""

with engine.begin() as conn:
    result = conn.execute(text(DAILY_AGG_SQL))
    print(f"Upserted {result.rowcount} rows")
