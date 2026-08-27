from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime,timezone
from database import get_db
from models import DHT22, Device 
from schemas import ReadingCreate, ReadingResponse
from auth import verify_token

app = FastAPI() #Object of FastAPI class

bearer_scheme = HTTPBearer() #Object of HTTPBearer class. Used for the token verification


#declare it in the path operation decorator and FastAPI reads the type hints in your function signature. both are fastAPI instructions
@app.get("/") #When someone askss for the front page http://localhost:8000/, run function bellow
async def read_root():
    return {"message" : "Welcome to Temp Predictor API"}


@app.post("/readings", response_model=ReadingResponse, status_code=201) #When device POSTs data in readings excecute function bellow and reply 201
def create_reading(reading: ReadingCreate, db: Session= Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):

    token = creds.credentials

    if reading.ts == None: ts =(datetime.now(timezone.utc)) 
    else: ts = reading.ts

    device = db.get(Device, reading.device_id) 
    if device is None:
        raise HTTPException(status_code=404, detail="Device UUID not registered in database.")

    if device.token_hash is None or verify_token(token, device.token_hash) is False:
         raise HTTPException(status_code=401, detail="Incorrect token.")

    dht22_readings = DHT22(device_id=reading.device_id, temp_c=reading.temp_c, humidity = reading.humidity, ts=ts)

    db.add(dht22_readings)
    db.commit()
    db.refresh(dht22_readings)

    return dht22_readings
