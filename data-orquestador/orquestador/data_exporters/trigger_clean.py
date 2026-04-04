if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

from mage_ai.orchestration.triggers.api import trigger_pipeline
from datetime import datetime

@data_exporter
def trigger_next_step(*args, **kwargs):
    """
    Dispara el pipeline de limpieza automáticamente tras el éxito de Raw.
    Absorbe los datos upstream en *args para no romper la firma de la función.
    """
    pipeline_uuid = 'capa_clean_v1'
    
    print(f"Iniciando trigger para {pipeline_uuid} a las {datetime.now()}")
    
    # Dispara el pipeline usando la API interna de Mage
    trigger_pipeline(
        pipeline_uuid,
        variables={},           
        check_status=False,     
        error_on_failure=True   
    )
    
    print("Señal de orquestación enviada con éxito.")