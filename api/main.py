from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer 
from sqlalchemy.orm import Session
from datetime import datetime,timezone, date
from database import get_db
from models import DHT22, Device, Prediction 
from schemas import ReadingCreate, ReadingResponse, DeviceCreate, DeviceResponse, DeviceListItem, PredictionResponse
from auth import verify_token, generate_token, hash_token
from uuid import UUID
from sqlalchemy import func

app = FastAPI() #Object of FastAPI class

bearer_scheme = HTTPBearer() #Object of HTTPBearer class. Used for the token verification


#declare it in the path operation decorator and FastAPI reads the type hints in your function signature. both are fastAPI instructions
@app.get("/") #When someone askss for the front page http://localhost:8000/, run function bellow
async def read_root():
    return {"message" : "Welcome to Temp Predictor API"}

#Received new post about a new reading
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

    device.last_seen = datetime.now(timezone.utc)

    dht22_readings = DHT22(device_id=reading.device_id, temp_c=reading.temp_c, humidity = reading.humidity, ts=ts)

    db.add(dht22_readings) #New object, to be added to the db
    db.commit()#Commits the whole session worksapce: device updated last seen and the dht22 new readings
    db.refresh(dht22_readings)

    return dht22_readings

#Received new post about a new device
@app.post("/devices", response_model=DeviceResponse, status_code=201)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):

    raw_token = generate_token()
    hashed = hash_token(raw_token)

    new_device = Device(
        display_name=device.display_name,
        location=device.location,
        firmware_version=device.firmware_version,
        token_hash=hashed,
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return DeviceResponse(
        device_id=new_device.device_id,
        token=raw_token,
        display_name=new_device.display_name,
        status=new_device.status,
    )

#In case someome asks from the DB to get all the devices
@app.get("/devices", response_model=list[DeviceListItem], status_code=200)
def get_devices_list( db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return devices

#In case I wanna see the readings
@app.get("/readings", response_model=list[ReadingResponse], status_code = 200)
def get_readings_list(device_id: UUID | None = None,  limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    readings = db.query(DHT22)
    if device_id is not None:
        readings = readings.filter(DHT22.device_id == device_id)
    readings = readings.order_by(DHT22.ts.desc()).limit(limit).all()
    return readings

#I wanna get a new prediction
@app.get("/prediction", response_model=list[PredictionResponse], status_code=200)
def get_prediction(device_id: UUID, based_on_date: date | None = None, db: Session = Depends(get_db)):
    predictions = db.query(Prediction)
    if based_on_date == None:
        based_on_date = db.query(func.max(Prediction.based_on_date)).filter(Prediction.device_id == device_id).scalar()
    predictions = predictions.filter(Prediction.based_on_date == based_on_date, Prediction.device_id == device_id).order_by(Prediction.target_date).all()
    return predictions