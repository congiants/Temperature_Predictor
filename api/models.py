from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from geoalchemy2 import Geography
import uuid as uuid_pkg

#ORM. Translation between db and python classes. Only python used 
class Device(Base):
    __tablename__ = "device"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    display_name = Column(String(255), nullable=True)
    token_hash = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default = 'active')
    location = Column(String(255), nullable=True)
    location_point = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    firmware_version = Column(String(255), nullable=True)
    first_activation = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen =Column(DateTime(timezone=True), nullable=True)
    device_metadata = Column(JSONB, nullable=True)

    __table_args__ = (CheckConstraint("status IN ('active', 'inactive', 'decommissioned')", name='device_status_chk'),)

    readings = relationship("DHT22", back_populates="device") #Virtual attribute pointing to another virtual attribute in DH22 class (device) which also points to this attribute for quick navigation between classes
    aggregates = relationship("DHT22Aggregate", back_populates="device")

class DHT22(Base):
    __tablename__ = "dht22"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("device.device_id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    temp_c = Column(Numeric(5,2), nullable=True)
    humidity = Column(Numeric(5,2), nullable=True)
    ts = Column(DateTime(timezone=True), nullable=True)
    quality = Column(String(20), nullable=False, default="ok")

    __table_args__ = (
        CheckConstraint("quality IN ('ok', 'outlier', 'duplicate', 'error')", name='dht22_quality_chk'),
        CheckConstraint("temp_c >= -80 AND temp_c <= 80",name='dht22_temp_chk'),
        CheckConstraint("humidity >= 0 AND humidity <= 100",name='dht22_humidity_chk'),
        )

    device = relationship("Device", back_populates="readings")

class DHT22Aggregate(Base):
    __tablename__="dht22_aggregate"

    device_id = Column(UUID(as_uuid=True), ForeignKey("device.device_id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True) #device.device_id refers to table not class
    date = Column(Date, primary_key=True)
    temp_c_max = Column(Numeric(5,2), nullable=True)
    temp_c_min = Column(Numeric(5,2), nullable=True)
    temp_c_avg = Column(Numeric(5,2), nullable=True)
    humidity_max = Column(Numeric(5,2), nullable=True)
    humidity_min = Column(Numeric(5,2), nullable=True)
    humidity_avg = Column(Numeric(5,2), nullable=True)
    reading_count = Column(Integer, nullable=False, default=0)

    device = relationship("Device", back_populates="aggregates")