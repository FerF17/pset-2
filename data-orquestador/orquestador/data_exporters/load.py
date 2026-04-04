from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from pandas import DataFrame
from typing import Dict
from os import path

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_postgres(data_dict: Dict[str, DataFrame], **kwargs) -> None:
    """
    Template for exporting data to a PostgreSQL database.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#postgresql
    """
    schema_name = 'clean'  # Specify the name of the schema to export data to
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
        for table_name, df_table in data_dict.items():
            print(f"Exportando tabla {table_name} al esquema {schema_name}...")
            
            loader.export(
                df_table,
                schema_name,
                table_name,
                index=False,  # No exportamos el índice de pandas como columna
                if_exists='replace',  # Permite reejecución idempotente 
            )
