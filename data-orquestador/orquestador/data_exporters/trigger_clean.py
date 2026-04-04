from mage_ai.orchestration.triggers.api import trigger_pipeline
from datetime import datetime

if 'custom_exporter' not in collections:
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def trigger_next_step(df, *args, **kwargs):
    """
    Dispara el pipeline de limpieza automáticamente tras el éxito de Raw.
    """
    # El primer argumento es el UUID exacto de tu pipeline de destino
    pipeline_uuid = 'capa_clean_v1'
    
    print(f"Iniciando trigger para {pipeline_uuid} a las {datetime.now()}")
    
    trigger_pipeline(
        pipeline_uuid,
        variables={},          
        check_status=False,     
        error_on_failure=True   # Falla este bloque si no puede disparar el siguiente
    )

    return df