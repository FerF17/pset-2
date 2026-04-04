# Laboratorio 2
### Fernando Escobar - NYC Taxi Data Engineering Pipeline

Este repositorio contiene la implementación de una arquitectura de datos robusta para el procesamiento de grandes volúmenes de datos históricos de la **NYC Taxi & Limousine Commission (TLC)**. El proyecto se centra en la orquestación de flujos de trabajo (pipelines), el modelado dimensional y la contenedorización mediante Docker.

## 1. Visión General del Proyecto

El objetivo es transformar datos crudos de viajes de taxi en Nueva York (abarcando un periodo de 3 años) en una estructura de datos optimizada para analítica avanzada y modelado predictivo.

### Objetivos Técnicos:
* **Orquestación:** Uso de **Mage.ai** para la gestión de DAGs (Directed Acyclic Graphs).
* **Ingestión (EL):** Extracción masiva de archivos fuente y carga en un *staging area* en PostgreSQL.
* **Transformación y Modelado (T):** Implementación de un **Modelo Dimensional (Star Schema)** para separar hechos de dimensiones.
* **Infraestructura:** Despliegue mediante **Docker Compose** para garantizar la reproducibilidad.

---

## 2. Arquitectura de Datos



El sistema sigue un patrón **ELT (Extract, Load, Transform)** estructurado en dos fases críticas:

### Fase 1: Pipeline de Ingestión (Raw Layer)
* **Fuente:** Archivos Parquet/CSV de la NYC TLC (3 años de datos).
* **Lógica:** Extracción asíncrona y carga por lotes (batch) en el esquema `raw`. 
* **Estrategia:** Se prioriza la integridad de los datos originales sin transformaciones pesadas para permitir el *re-processing* sin re-descarga.

### Fase 2: Pipeline de Transformación (Clean/Analytics Layer)
* **Modelado:** Aplicación de lógica de limpieza (manejo de nulos, outliers en costos y coordenadas).
* **Esquema:** Generación de un **Star Schema** en el esquema `clean`:
    * **Fact Table:** `fact_trips` (Métricas granulares de viajes).
    * **Dimensions:** `dim_pickup_location`, `dim_locationdim_dropoff_location`, `dim_vendor`, `dim_payment_type`.

---

## 3. Orquestación y Automatización (Triggers)

Para garantizar la consistencia atómica del flujo de datos y cumplir con el paradigma "Event-Driven", ambas tuberías operan de forma automatizada evitando carreras lógicas (*race conditions*):

* **Ingestión Periódica (`capa_raw`):** Se configuró un `Schedule Trigger` con frecuencia mensual (`@monthly`) que actúa como el punto de entrada (Entrypoint) simulando la ingesta periódica de los nuevos lotes de datos que publica la TLC.
* **Dependencia Lógica (`capa_clean_v1`):** La capa de transformación *jamás* se ejecuta basándose en un horario arbitrario. Se implementó un trigger programático vía API (`trigger_pipeline` de Mage) en un bloque de Python al final de la capa Raw. Este bloque evalúa el estado del proceso *Upstream* y, si y solo si los datos fueron cargados exitosamente en PostgreSQL, emite una señal que arranca el pipeline de limpieza.
---

## 4. Stack Tecnológico

| Componente | Tecnología | Rol |
| :--- | :--- | :--- |
| **Orquestador** | Mage.ai | Gestión de pipelines, monitoreo y ejecución de bloques Python/SQL. |
| **Base de Datos** | PostgreSQL | Almacenamiento relacional para capas Raw y Clean. |
| **Lenguaje** | Python 3.x | Lógica de extracción (Pandas/Requests) y limpieza. |
| **Contenedores** | Docker & Docker Compose | Aislamiento del entorno y dependencias. |

---

## 5. Estructura del Modelo Dimensional

A diferencia de una tabla plana, este proyecto implementa un diseño orientado a **OLAP (Online Analytical Processing)**:

* **Hechos ($Fact$):** Contiene las claves foráneas a las dimensiones y las métricas cuantitativas (distancia, montos, propinas).
* **Dimensiones ($Dimensions$):** Tablas de referencia para filtrar y agrupar (contexto temporal, geográfico y de categorización).

> **Nota Académica:** Este enfoque reduce la redundancia y optimiza el rendimiento de las consultas SQL complejas (agregaciones) en comparación con el procesamiento sobre archivos crudos.

---

## 6. Configuración y Ejecución

### Requisitos Previos
* Docker y Docker Compose instalados.
* Mínimo 4GB de RAM asignados a Docker (debido al volumen de datos de 3 años).

### Pasos para el despliegue

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/FerF17/pset-2.git](https://github.com/FerF17/pset-2.git)
    cd pset-2
    ```

2.  **Levantar el entorno:**
    ```bash
    docker-compose up -d
    ```

3.  **Acceder a las interfaces:**
    * **Mage UI:** `http://localhost:6789`
    * **PostgreSQL:** `localhost:5432` (User: `email`, Pass: `password`, DB: `ny_taxi`)

4. **Ejecución de Pipelines:**
    * **Inicio del Flujo:** Dentro de Mage, ejecutar el pipeline **`capa_raw`** (manualmente o vía trigger programado).
    * **Automatización:** **No es necesario ejecutar manualmente `capa_clean_v1`.** El sistema detectará la finalización exitosa de la carga cruda y disparará automáticamente la fase de transformación analítica. 

---

## 7. Consideraciones de Ciencia de Datos

### Supuestos y Limpieza:
* **Manejo de Outliers:** Se filtran viajes con distancia cero o negativa y aquellos con montos totales inconsistentes ($Total Amount < 0$).
* **Consistencia Temporal:** Se validan que las fechas de *drop-off* sean posteriores a las de *pick-up*.

### Limitaciones del Análisis:
1.  **Entorno Local:** El procesamiento está limitado por la capacidad de cómputo del host. Para una implementación en producción (Enfoque Aplicado), se recomendaría el uso de **Cloud Storage (S3/GCS)** y un Data Warehouse como **BigQuery o Snowflake**.
2.  **Particionamiento:** Actualmente, los datos se cargan en tablas completas. En una fase siguiente, se debería implementar particionamiento por `tpep_pickup_datetime`.

---

## 8. Enfoque Académico vs. Aplicado

* **Académico (Tesis/Lab):** Este proyecto demuestra la capacidad de normalizar datos y estructurar un flujo de trabajo reproducible siguiendo principios de ingeniería de software. Se enfoca en la **correctitud del modelo relacional**.
* **Aplicado (Industria):** En un entorno de producto, este pipeline incluiría validaciones de calidad de datos automáticas (Great Expectations), CI/CD para los DAGs y monitoreo de costos de cómputo.

---
**Desarrollado por:** [Fernando Escobar]
**Programa:** Maestría en Ciencia de Datos - USFQ.