CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS device (
    device_id UUID PRIMARY KEY,
    display_name VARCHAR(255),
    token_hash VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    location VARCHAR(255),
    location_point GEOGRAPHY(POINT, 4326), 
    firmware_version VARCHAR(50),
    first_activation TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    device_metadata JSONB,
    CONSTRAINT device_status_chk CHECK (status IN ('active', 'inactive', 'decommissioned'))
);

/*Indexes improve retrieve operations speed but slow down inser/update/delete. Created in mind for most frequent querries*/
CREATE INDEX idx_device_location_point ON device USING GIST(location_point); /* Using GIST instead of default (B-Tree) for the index as spatial points are multi dimensional and require spatial distance calculations, not numeric comparissons*/
CREATE INDEX idx_device_status ON device(status);
CREATE INDEX idx_device_last_seen ON device(last_seen DESC);

CREATE TABLE IF NOT EXISTS dht22(
    id  BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL,
    temp_c NUMERIC(5,2),
    humidity NUMERIC(5,2),
    ts TIMESTAMPTZ,
    quality VARCHAR(20) NOT NULL DEFAULT 'ok',
    CONSTRAINT dht22_quality_chk CHECK (quality IN ('ok', 'outlier', 'duplicate', 'error')),
    CONSTRAINT dht22_device_fk
        FOREIGN KEY (device_id)
        REFERENCES device(device_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT dht22_temp_chk 
        CHECK (temp_c >= -80 AND temp_c <= 80),
    CONSTRAINT dht22_humidity_chk 
        CHECK (humidity >= 0 AND humidity <= 100)
);

CREATE INDEX idx_dht22_device_ts ON dht22 (device_id, ts DESC);
CREATE INDEX idx_dht22_ts ON dht22 (ts DESC);
CREATE INDEX idx_dht22_quality ON dht22 (quality) WHERE quality != 'ok';

CREATE TABLE IF NOT EXISTS dht22_aggregate(
    device_id UUID NOT NULL,
    date DATE NOT NULL, 
    temp_c_max NUMERIC(5,2),
    temp_c_min NUMERIC(5,2),
    temp_c_avg NUMERIC(5,2),
    humidity_max NUMERIC(5,2),
    humidity_min NUMERIC(5,2),
    humidity_avg NUMERIC(5,2),
    reading_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(device_id, date),

    CONSTRAINT dht22_reading_aggregate_device_fk
        FOREIGN KEY (device_id)
        REFERENCES device(device_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE INDEX idx_dht22_aggregate_date ON dht22_aggregate (date DESC);


CREATE TABLE IF NOT EXISTS prediction(
    device_id UUID NOT NULL,
    based_on_date DATE NOT NULL,
    target_date DATE NOT NULL, 
    temp_c_max NUMERIC(5,2),
    temp_c_min NUMERIC(5,2),
    model VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(device_id, based_on_date, target_date),

    CONSTRAINT dht22_prediction_device_fk
        FOREIGN KEY (device_id)
        REFERENCES device(device_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT target_date_greater_than_issued_at_date_check CHECK (target_date>based_on_date),
    CONSTRAINT temp_ranges_chck CHECK(temp_c_max > -100 AND temp_c_max < 80 AND temp_c_min > -100 AND temp_c_min < 80)
);
