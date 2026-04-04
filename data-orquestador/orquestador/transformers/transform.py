if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

import pandas as pd

@transformer
def transform(data, *args, **kwargs):
    """
    Template code for a transformer block.

    Add more parameters to this function if this block has multiple parent blocks.
    There should be one parameter for each output variable from each parent block.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # 1. Estandarización inicial

    data.columns = [col.lower() for col in data.columns]
    data.rename(columns={
        "vendorid":"vendor_id",
        "ratecodeid":"rate_code_id",
        "pulocationid":"pu_location_id",
        "dolocationid":"do_location_id",
    }, inplace = True)

    # 2. Limpieza y Tipificación 
    data['tpep_pickup_datetime'] = pd.to_datetime(data['tpep_pickup_datetime'])
    data['tpep_dropoff_datetime'] = pd.to_datetime(data['tpep_dropoff_datetime'])
    
    # Filtrar registros inconsistentes (ej. distancia o pasajeros <= 0)
    data = data[(data['trip_distance'] > 0) & (data['passenger_count'] > 0)]
    
    # 3. Creación de Dimensiones
    
    # dim_vendor 
    # Mapeamos los IDs a nombres reales para dar valor analítico
    vendor_map = {1: 'Creative Mobile', 2: 'VeriFone'}
    dim_vendor = data[['vendor_id']].drop_duplicates().reset_index(drop=True)
    dim_vendor['vendor_name'] = dim_vendor['vendor_id'].map(vendor_map)

    # dim_payment_type 
    payment_map = {1: 'Credit Card', 2: 'Cash', 3: 'No Charge', 4: 'Dispute'}
    dim_payment_type = data[['payment_type']].drop_duplicates().reset_index(drop=True)
    dim_payment_type['payment_type_name'] = dim_payment_type['payment_type'].map(payment_map)

    # dim_pickup_location
    dim_pickup_location = data[['pu_location_id']].drop_duplicates().reset_index(drop=True)
    dim_pickup_location.rename(columns={'pu_location_id': 'location_id'}, inplace=True)

    # dim_dropoff_location
    dim_dropoff_location = data[['do_location_id']].drop_duplicates().reset_index(drop=True)
    dim_dropoff_location.rename(columns={'do_location_id': 'location_id'}, inplace=True)

    # 4. Creación de la Tabla de Hechos (Fact Table)
    # La Fact Table solo debe tener llaves foráneas y métricas
    fact_trips = data[[
        'vendor_id', 'pu_location_id', 'do_location_id', 'payment_type', 'rate_code_id',
        'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count',
        'trip_distance', 'fare_amount', 'extra', 'mta_tax', 'tip_amount',
        'tolls_amount', 'improvement_surcharge', 'total_amount'
    ]]
    
    # Añadimos una métrica calculada: duración del viaje 
    fact_trips['trip_duration_seconds'] = (
        fact_trips['tpep_dropoff_datetime'] - fact_trips['tpep_pickup_datetime']
    ).dt.total_seconds()

    # 5. Retornar diccionario para el exportador
    return {
        'fact_trips': fact_trips,
        'dim_vendor': dim_vendor,
        'dim_payment_type': dim_payment_type,
        'dim_pickup_location': dim_pickup_location,
        'dim_dropoff_location': dim_dropoff_location
    }

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
