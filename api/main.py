from fastapi import FastAPI, Depends, HTTPException 
from sqlalchemy.orm import Session
from datetime import datetime,timezone
from database import get_db
from models import DHT22, Device 
from schemas import ReadingCreate, ReadingResponse

app = FastAPI()

#declare it in the path operation decorator and FastAPI reads the type hints in your function signature. both are fastAPI instructions
@app.get("/") #When someone askss for the front page http://localhost:8000/, run function bellow
async def read_root():
    return {"message" : "Welcome to Temp Predictor API"}


@app.post("/readings", response_model=ReadingResponse, status_code=201) #When device POSTs data in readings excecute function bellow and reply 201
def create_reading(reading: ReadingCreate, db: Session= Depends(get_db)):
    if reading.ts == None: ts =(datetime.now(timezone.utc)) 
    else: ts = reading.ts
    if db.get(Device, reading.device_id) is None:
        raise HTTPException(status_code=404, detail="Device UUID not registered in database.")
    dht22 = DHT22(device_id=reading.device_id, temp_c=reading.temp_c, humidity = reading.humidity, ts=ts)

    db.add(dht22)
    db.commit()
    db.refresh(dht22)

    return dht22
