from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from pandas import DataFrame
from os import path
import pandas as pd
import math 
import gc 

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_postgres(urls, **kwargs) -> None:
    schema_name = 'raw' 
    table_name = 'raw' 
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    tamano_chunk = 100000 
    
    primera_insercion = True

    for url in urls:
        print(f"Procesando archivo: {url}")
        try:
            
            df_temp = pd.read_parquet(url)
            df_temp.columns = df_temp.columns.str.lower()
            
            total_filas = df_temp.shape[0]
            num_chunks = math.ceil(total_filas / tamano_chunk)
            
            inicio = 0
            fin = tamano_chunk

            with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
                for i in range(num_chunks):
                    
                    df_chunk = df_temp.iloc[inicio:fin].copy()
                    
                    
                    df_chunk = df_chunk.astype(str)
                    
                    politica_insercion = 'replace' if primera_insercion else 'append'
                    
                    loader.export(
                        df_chunk,
                        schema_name,
                        table_name,
                        index=False,
                        if_exists=politica_insercion, 
                    )
                    
                    print(f"    - Chunk {i+1}/{num_chunks} insertado correctamente.")
                    
                    inicio = fin
                    fin += tamano_chunk
                    es_primera_insercion = False 
                    
                    
                    del df_chunk
                    gc.collect()

            print(f"Éxito cargando mes completo: {url}\n")
            
            
            del df_temp
            gc.collect() 
            
        except Exception as e:
            import traceback
            print(f"❌ Error crítico al procesar {url}:")
            print(f"   Traceback completo:")
            traceback.print_exc()
            print("─" * 60)

from mage_ai.orchestration.triggers.api import trigger_pipeline

@data_exporter
def trigger_clean_process(df, *args, **kwargs):
    # Esto dispara el pipeline de limpieza si el de raw termina con éxito
    trigger_pipeline(
        'capa_clean_v1', 
        variables={},
        check_status=False,
    )
    return df # Retornamos el dataframe solo por consistencia        