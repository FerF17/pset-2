-- 1. Preparamos el terreno
CREATE SCHEMA IF NOT EXISTS clean;

-- Borramos si ya existen para evitar errores al re-ejecutar
DROP TABLE IF EXISTS clean.fact_trips;
DROP TABLE IF EXISTS clean.dim_pickup_location;
DROP TABLE IF EXISTS clean.dim_dropoff_location;

-- 2. Creamos la Fact Table (Implementación defensiva de Nulos)
CREATE TABLE clean.fact_trips AS
SELECT 
    NULLIF(REGEXP_REPLACE(vendorid, '[^0-9\.-]', '', 'g'), '')::numeric::int AS vendor_id,
    NULLIF(LOWER(pulocationid), 'nan')::numeric::int AS pu_location_id,
    NULLIF(LOWER(dolocationid), 'nan')::numeric::int AS do_location_id,
    NULLIF(LOWER(payment_type), 'nan')::numeric::int AS payment_type,
    NULLIF(LOWER(ratecodeid), 'nan')::numeric::int AS rate_code_id,
    -- Las fechas nulas en pandas se exportan como 'nat' (Not a Time)
    NULLIF(LOWER(tpep_pickup_datetime), 'nat')::timestamp AS tpep_pickup_datetime,
    NULLIF(LOWER(tpep_dropoff_datetime), 'nat')::timestamp AS tpep_dropoff_datetime,
    NULLIF(LOWER(passenger_count), 'nan')::numeric::int AS passenger_count,
    NULLIF(LOWER(trip_distance), 'nan')::numeric AS trip_distance,
    NULLIF(LOWER(fare_amount), 'nan')::numeric AS fare_amount,
    NULLIF(LOWER(extra), 'nan')::numeric AS extra,
    NULLIF(LOWER(mta_tax), 'nan')::numeric AS mta_tax,
    NULLIF(LOWER(tip_amount), 'nan')::numeric AS tip_amount,
    NULLIF(LOWER(tolls_amount), 'nan')::numeric AS tolls_amount,
    NULLIF(LOWER(improvement_surcharge), 'nan')::numeric AS improvement_surcharge,
    NULLIF(LOWER(total_amount), 'nan')::numeric AS total_amount,
    -- Calculamos la duración directamente en SQL
    EXTRACT(EPOCH FROM (
        NULLIF(LOWER(tpep_dropoff_datetime), 'nat')::timestamp - 
        NULLIF(LOWER(tpep_pickup_datetime), 'nat')::timestamp
    )) AS trip_duration_seconds
FROM raw.raw
WHERE NULLIF(LOWER(trip_distance), 'nan')::numeric > 0 
  AND NULLIF(LOWER(passenger_count), 'nan')::numeric > 0;

-- 3. Creamos Dimensiones de Ubicación (Excluyendo nulos para integridad referencial)
CREATE TABLE clean.dim_pickup_location AS 
SELECT DISTINCT NULLIF(LOWER(pulocationid), 'nan')::numeric::int AS location_id 
FROM raw.raw
WHERE NULLIF(LOWER(pulocationid), 'nan') IS NOT NULL;

CREATE TABLE clean.dim_dropoff_location AS 
SELECT DISTINCT NULLIF(LOWER(dolocationid), 'nan')::numeric::int AS location_id 
FROM raw.raw
WHERE NULLIF(LOWER(dolocationid), 'nan') IS NOT NULL;

-- 4. Crear las dimensiones maestras de texto
DROP TABLE IF EXISTS clean.dim_vendor;
CREATE TABLE clean.dim_vendor (vendor_id int, vendor_name text);
INSERT INTO clean.dim_vendor VALUES (1, 'Creative Mobile'), (2, 'VeriFone');

DROP TABLE IF EXISTS clean.dim_payment_type;
CREATE TABLE clean.dim_payment_type (payment_type int, payment_type_name text);
INSERT INTO clean.dim_payment_type VALUES 
(1, 'Credit Card'), (2, 'Cash'), (3, 'No Charge'), (4, 'Dispute');