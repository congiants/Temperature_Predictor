from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime,timezone
from database import get_db
from models import DHT22
from schemas import ReadingCreate, ReadingResponse

app = FastAPI()

@app.get("/")

async def read_root():
    return {"message" : "Welcome to Temp Predictor API"}


@app.post("/readings", response_model=ReadingResponse, status_code=201)

def create_reading(reading: ReadingCreate, db: Session= Depends(get_db)):
    if reading.ts == None: ts =(datetime.now(timezone.utc)) 
    else: ts = reading.ts
    dht22 = DHT22(device_id=reading.device_id, temp_c=reading.temp_c, humidity = reading.humidity, ts=ts)

    db.add(dht22)
    db.commit()
    db.refresh(dht22)

    return dht22
