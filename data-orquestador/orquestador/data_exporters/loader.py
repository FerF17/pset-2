import pandas as pd
from sqlalchemy import create_engine
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from os import path
import gc

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def etl_en_chunks_masivos(*args, **kwargs):
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    schema_name = 'clean' 
    
    # 1. Configurar la conexión SQLAlchemy para leer
    config = ConfigFileLoader(config_path, config_profile)
    connection_string = (
        f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}"
        f"@{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DBNAME']}"
    )
    engine = create_engine(connection_string)
    
    query = "SELECT * FROM raw.raw"
    chunk_size = 100000
    
    # Controles de flujo
    es_primer_chunk = True
    
    # Usamos 'sets' de Python para guardar IDs únicos de las locaciones.
    # Esto consume casi cero RAM y evita duplicados en las dimensiones.
    unique_pu_locations = set()
    unique_do_locations = set()
    
    print("Iniciando extracción, transformación y carga por chunks...")
    
    with Postgres.with_config(config) as loader:
        # El iterador extrae de 100k en 100k desde la base raw
        for i, chunk in enumerate(pd.read_sql(query, engine, chunksize=chunk_size)):
            
            # --- 1. TRANSFORMACIÓN DEL CHUNK ---
            chunk.columns = [col.lower() for col in chunk.columns]
            chunk.rename(columns={
                "vendorid":"vendor_id",
                "ratecodeid":"rate_code_id",
                "pulocationid":"pu_location_id",
                "dolocationid":"do_location_id",
            }, inplace=True)

            chunk['tpep_pickup_datetime'] = pd.to_datetime(chunk['tpep_pickup_datetime'])
            chunk['tpep_dropoff_datetime'] = pd.to_datetime(chunk['tpep_dropoff_datetime'])
            
            # Filtro de inconsistencias
            chunk = chunk[(chunk['trip_distance'] > 0) & (chunk['passenger_count'] > 0)]
            
            # --- 2. PREPARACIÓN DE LA FACT TABLE ---
            # Usamos .copy() para evitar advertencias de memoria fragmentada en Pandas
            fact_trips = chunk[[
                'vendor_id', 'pu_location_id', 'do_location_id', 'payment_type', 'rate_code_id',
                'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count',
                'trip_distance', 'fare_amount', 'extra', 'mta_tax', 'tip_amount',
                'tolls_amount', 'improvement_surcharge', 'total_amount'
            ]].copy()
            
            fact_trips['trip_duration_seconds'] = (
                fact_trips['tpep_dropoff_datetime'] - fact_trips['tpep_pickup_datetime']
            ).dt.total_seconds()
            
            # --- 3. RECOPILACIÓN DE DIMENSIONES ---
            # Guardamos los IDs que van apareciendo. Al ser un set, ignora los repetidos automáticamente.
            unique_pu_locations.update(chunk['pu_location_id'].dropna().unique())
            unique_do_locations.update(chunk['do_location_id'].dropna().unique())
            
            # --- 4. CARGA DE LA FACT TABLE ---
            # El primer chunk reemplaza/crea la tabla, los demás agregan filas
            politica = 'replace' if es_primer_chunk else 'append'
            
            loader.export(
                fact_trips,
                schema_name,
                'fact_trips',
                index=False,
                if_exists=politica
            )
            
            print(f"  - Chunk {i+1} procesado y cargado en fact_trips ({len(fact_trips)} filas validadas).")
            
            es_primer_chunk = False
            
            # ¡CRÍTICO! Limpieza de memoria RAM antes del siguiente ciclo
            del chunk
            del fact_trips
            gc.collect()

        # --- 5. CREACIÓN Y CARGA DE DIMENSIONES ---
        # Esto ocurre FUERA del bucle, una sola vez al final del proceso.
        print("\nProcesando y cargando tablas de dimensiones...")
        
        dim_vendor = pd.DataFrame({
            'vendor_id': [1, 2],
            'vendor_name': ['Creative Mobile', 'VeriFone']
        })
        
        dim_payment_type = pd.DataFrame({
            'payment_type': [1, 2, 3, 4],
            'payment_type_name': ['Credit Card', 'Cash', 'No Charge', 'Dispute']
        })
        
        dim_pickup_location = pd.DataFrame({'location_id': list(unique_pu_locations)})
        dim_dropoff_location = pd.DataFrame({'location_id': list(unique_do_locations)})
        
        dimensiones = {
            'dim_vendor': dim_vendor,
            'dim_payment_type': dim_payment_type,
            'dim_pickup_location': dim_pickup_location,
            'dim_dropoff_location': dim_dropoff_location
        }
        
        for table_name, df_dim in dimensiones.items():
            loader.export(df_dim, schema_name, table_name, index=False, if_exists='replace')
            print(f"  - Dimensión {table_name} creada y cargada con éxito.")
            
    return "Pipeline ETL completado. Base estructurada en estrella exitosamente."