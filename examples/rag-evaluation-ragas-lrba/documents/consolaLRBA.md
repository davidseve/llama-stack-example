# Consola LRBA
## Funcionalidades de la Consola LRBA

La Consola LRBA (Lightweigh Runtime Batch Architecure) es principalmente una herramienta que permite:
- ver las estadísticas de las ejecuciones de los jobs.
- monitorizar los Jobs que se están ejecutando en el cluster.
- consultar los Jobs que están desplegados en la Arquitectura para poder ejecutarse y su configuración.
- consultar la metadata de los objetos o ficheros almacenados en BTS.
- consultar la metadata de los objetos o ficheros almacenados en Historificación o Archive.
- crear o consultar las impersonaciones que puede hacer una UUAA sobre el bucket de BTS de otra UUAA.

De manera general, en la consola se puede elegir la Región y el Namespace de ejecución que se quiere consultar.
* Las regiones disponibles son:
    - work-01 y live-01 para el tenant de Europa (en el que se encuentra el país de España y el Tenant Global)
    - work-02 y live-02 para el tenant de América (en el que se encuentran los países de México, Colombia, Perú, Argentina y Venezuela)

- La URL de acceso es la siguiente: https://bbva-lrba.appspot.com/.

- Nota: De momento el namespace de consulta en la Consola LRBA se hace utilizando el namespace de la aplicación que es diferente al namespace de ejecución. La construcción del namespace es de dos maneras diferentes: {país}.{uuaa}.{appId}.{entorno} o {uuaa}.{país}.{entorno}.


## 1. Estadísticas Generales**

* Proporciona una visión consolidada del estado general de las ejecuciones en el entorno.
* Incluye indicadores clave de rendimiento (KPIs) y tendencias históricas. 
* Muestra:
    - número de ejecuciones
    - número de ejecuciones correctas y fallidas
    - el tiempo de ejecución en media por día
    - una lista del los 10 jobs más ejecutados ordenados por el número de ejecuciones
    - una gráfica con el porcentaje de ejecuciones correctas y fallidas

## 2. Historial de Ejecuciones**
* Muestra el historial de ejecuciones del mismo día en que se está consultado por defecto.
* También permite consultar ejecuciones pasadas con sus estados, tiempos y resultados.
* Ofrece filtros por:
    - nombre del job
    - versión del job
    - run ID, que es el ID con el que se ejecuta el job en el cluster
    - status que puede ser SUCESS; FAILED; RUNNING; LAUNCHING; FORCED STOP; UNKNOWN; LOCKED
    - talla de ejecución: spark-default, spark-standalone, spark-high-memory, spark-high-parallelism
    - priority class, que indica la prioridad de la ejecución del job. cuanto mayor sea el número de la priority class, mayor es la prioridad de ejecución.
    - y la fecha de ejecución

* Adicionalmente, se puede entrar a ver el detalle de cada uno de los jobs ejecutados. En este caso, se podrá consultar:
    - Alguna metadata como:
        - el namespace de ejecución
        - el run Id
        - el path del artefacto JAR que se está ejecutando
        - la versión de la Arquitectura con la que se está ejecutando
        - la prioridad
        - la versión del job
        - la configuración de la aplicación para su ejecución
        - la fecha de inicio
        - la fecha de fin
        - el tiempo de ejecución
        - el código de retorno
        - los parámetro de entrada
        - la configuración de la aplicación.
    - Por otro lado, en la zona inferior se puede consultar la información almacenada en el Spark History con respecto al job en cuestión. Hay 5 pestañas que contienen la siguiente información:
        - LRBA Steps, que se compone de los pasos que realiza el job cuando se ejecuta. Estos son: Setup Spark, Prepare Read, Prepare Transform, Prepare Write, Execute y Shutdown Spark.
        - Spark Job, que contiene la lista de trabajos (jobs) lanzados por la aplicación. Para cada job muestra:
            - ID del job.
            - Estado (Éxito o error).
            - Tiempo de ejecución.
            - Número de tareas (tasks) por estado (completadas, fallidas, etc.).
            - DAG (grafo) del job que muestra las etapas y dependencias visualmente.
        - Spark Stages, que muestra detalles por etapa (stage) dentro de los jobs. La información por stage que muestra es:
            - ID de la etapa.
            - Tipo de etapa (Shuffle Map / Result).
            - Tiempo de ejecución.
            - Número de tareas y distribución de tiempos.
            - Métricas de rendimiento (tiempo de CPU, bytes leídos/escritos, shuffle, etc.).
            - Posibilidad de ver estadísticas por tarea individual.
        - Spark Executors, que muestra información detallada de cada ejecutor:
            - Dirección IP.
            - Memoria y núcleos asignados.
            - Métricas: tareas completadas, tiempo total de CPU, I/O, uso de memoria.
            - Comparación entre ejecutores para detectar desequilibrios.
        - Spark SQL
            - Detalles de cada consulta SQL ejecutada.
            - Planes lógico y físico.
            - Métricas de ejecución (tiempos, número de filas, etc.).
            - Árbol del plan de ejecución (similar a EXPLAIN).
        - Error trace, que sólo aparece cuando existe un error. Esta pestaña muestra el error ocurrido en tiempo de ejecución.

## 3. Jobs**

* Se muestra el listado de Jobs que están desplegados en la Arquitectura.
* Ofrece filtros como:

* Para cada job se puede ver:
    - El nombre
    - La prioridad
    - La configuración para su ejecución
    - El tipo de job
    - Un enlace a las ejecuciones del job en la sección del historico de ejecuciones.
    - Además, hay un botón "+" que te permite ver:
        - Un listado de las versiones del job que se han desplegado
        - Un enlace a las ejecuciones de la versión del job en la sección del historico de ejecuciones.
        - Un botón de detalles que te permite consultar:
            - La versión del job
            - El path donde se encuentra almacenado el JAR
            - El país de despliegue
            - El entorno de despliegue
            - El tipo de job
            - La configuración para su ejecución
            - La configuración de la aplicación
    
## 4. BTS Inventory**

* Ofrece un inventario de los objetos y recursos disponibles creados por los procesos LRBA comunes.
* Ofrece filtros como:
    - Nombre del fichero
    - Tipo de fichero (csv, parquet, dat o txt)
    - Disponibilidad (1 día, 3 días, 7 días, 31 días)
    - Visibilidad (Public, Private, Group Shared)
    - Tipo de Información (Non Protected Data, Personal Identification, Fraud Enablers, Secrets and Keys, Sensitive Personal Data, Internal Use)
    - Fecha de inserción en BTS

* Se encuentra una tabla en la que se muestra:
    - Nombre del fichero
    - Tipo de fichero
    - Tamaño (formateado a B, KB, MB, GB, etc)
    - Disponibilidad
    - Visibilidad
    - Estado (Activo o Expirado en función de los días transcurridos desde su inserción)
    - Tipo de Información
    - Un botón por cada fichero que te permite consultar la siguiente metadata:
        - Nombre del fichero
        - Namespace de Ejecución
        - Tipo de fichero
        - Disponibilidad
        - Visibilidad
        - Estado (Activo o Expirado en función de los días transcurridos desde su inserción)
        - Tipo de Información
        - Nombre del Job que ha creado el fichero
        - Run ID del Job que ha creado el fichero
        - Fecha de inserción en BTS
        - Tamaño de fichero
        - Estructura (o esquema) del fichero.

## 5. Archive Inventory**

* De funcionalidad similar al BTS Inventory, ofrece un inventario de los objetos y recursos creados por los procesos de historificación especificamente.
* Ofrece filtros como:
    - Tipo de gestor de base de datos (oracle, mongodb, elasticsearch, couchbase)
    - Servicio (Identificador del gestor de origen)
    - Nombre de la entidad (tabla o colección del gestor de origen)
    - Fecha de inserción en los buckets de Historificación (o Archive)
    - Años en los que expira el fichero (sus valores van del 1 a 10, este valor depende del entorno)   

* Se encuentra una tabla en la que se muestra:
    - Tipo de gestor de base de datos 
    - Servicio
    - Nombre de la entidad
    - Fecha de inicio del período historificado
    - Fecha de fin del período historificado
    - Expiración en años
    - Un botón por cada fichero que te permite consultar la siguiente metadata:
        - Nombre del fichero
        - Servicio
        - Tipo de gestor de base de datos 
        - Nombre de la entidad
        - Nombre de la columna utilizada para filtrar en la utilidad de Historificación
        - Fecha de inicio del Período de Historificación
        - Fecha de fin del período historificado
        - Fecha de archivado (fecha de ejecución de la utilidad de historificación)
        - Expiración en años
        - Fecha de expiración de los datos archivados
        - Tipo de fichero
        - Versión de Parquet utilizada para archivar
        - Versión de Spark utilizada para archivar
        - Tamaño de fichero
        - Esquema del fichero.
        - Sólo si el gestor de base de datos es mongo se muestra el "Esquema DDL" introducido en la utilidad de historificación en Cronos.


## 6. Impersonation**

* Gestiona las funcionalidades de ejecución en representación de otras aplicaciones, para poder acceder a sus ficheros de BTS.
* Sólo los Tech Leaders de las UUAAs (o aplicaciones) pueden realizar cambios en esta sección.
* Hay un botón "+ New Impersonation Config" que te permite añadir una nueva configuración. Se abre una pantalla en la que se pide introducir:
    - La UUAA a la que se le quiere dar permisos de Impersonación.
    - El modo de impersonación, siendo posible seleccionar:
        - RO (Read Only)
        - WO (Write Only)
        - RW (Read and Write)
* De manera general, se muestra una tabla con la lista de impersonaciones que tiene habilitada la aplicación. En esa lista se muestra:
    - Tipo de gestor al que se puede acceder
    - UUAA (o aplicación) a la que se le da permisos de impersonación
    - Modo de impersonación
    - Visibilidad de lectura 
    - Alcance de la escritura
    - Y finalmente dos botones que permiten al Tech Leader editar o eliminar la configuración establecida.

