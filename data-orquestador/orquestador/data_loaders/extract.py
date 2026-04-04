import pandas as pd
import gc  # Garbage Collector
from sqlalchemy import create_engine
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from os import path

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_data(*args, **kwargs):
    """
    Template code for loading data from any source.

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your data loading logic here
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
    urls = []
    

    for year in range(2025, 2022, -1):

        for month in range(12, 0, -1):
            
            urls.append(base_url.format(year=year, month=month))
            
    print(f"Total de URLs generadas para extracción: {len(urls)}")
    print(urls)

    return urls


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'