# quickstart/01-WhatIsLRBA.md
# ¿Qué es LRBA?

*Lightweight Runtime Architecture for Batch* o LRBA es un *runtime* de arquitectura Ether para implementación de procesos de negocio por lotes o *batch* llegando a manejar grandes *datasets* con Spark y que complementa otros motores ya existentes dentro de Ether como APX Batch.

Los principios básicos de LRBA son los siguientes:

- Construida para ser ejecutada sobre los *building blocks* disponibles dentro del ámbito IaaS Nextgen (x86) y en concreto sobre la plataforma de **contenedores PaaS**.
- **Modelo de ejecución ligero** en cuanto arquitectura y apoyándose en *frameworks* del mundo con código abierto específicos (Spark) para ejecución de procesos.
- *Framework* que facilita la ejecución paralela, escalabilidad, y uso intensivo de memoria.  
- **Securización** de acceso a datasources.
- Experiencia de desarrollo amigable: 
    - Integración con herramientas Ether (consola, ecs-cli, stacker) para crear y desplegar *jobs* sencillamente.
    - Integración con el planificador Ether.  
    - Monitorización, control de errores y trazabilidad integrado en **Atenea**.
- Procesos de coexistencia de datos entre bases de datos operacionales (Ether y Legacy) con lógica de transformación simple.
- Implementación de operativas de negocio que incluyen fuentes de datos de origen y destino de bases de datos operativas y volumétricas que ayudan al procesamiento paralelo y en memoria.
- Simplificación de desarrollos *batch* a través de aplicaciones simples (solo **SQL para ETL**) o métodos de aplicación (Spark API) con *datasets*.
- La configuración de acceso a los gestores de bases de datos y otras persistencias como BTS (Epsilon está deprecado) son transparentes al desarrollo de procesos aplicativos.


# quickstart/concepts.md
# Conceptos

La ejecución de los *jobs* LRBA se basa en un **modelo de ejecución orquestado por la arquitectura**. El programa principal de la arquitectura en tiempo de ejecución gestiona el flujo de procesamiento de los *jobs*.

La arquitectura LRBA Spark se basa en el **framework Apache Spark** para el acceso a la persistencia. Las aplicaciones desarrolladas bajo LRBA utilizarán el framework Spark para implementar las operaciones sobre los datos.

En cuanto al procesamiento de datos, uno de los conceptos más importantes es el **dataset**.
Un *dataset* es una colección de **datos distribuidos** que ya tiene una estructura y reside en la memoria del proceso Spark.
Un *job* LRBA Spark siempre accede y transforma los datos a través de estos objetos *dataset*. Apache Spark proporciona un [API de *dataset*](https://spark.apache.org/docs/latest/api/java/index.html?org/apache/spark/sql/Dataset.html) (Algunos métodos API no están permitidos en LRBA).

La conexión con la ubicación física de los datos, con todo lo que ello implica (descubrimiento, seguridad, ...) se gestiona íntegramente mediante la arquitectura. Cada *source* o *target* de datos debe tener asignado un alias LRBA interno.

## Código job LRBA Spark

Un *job* LRBA tiene dos clases Java principales:

- Clase ***JobSparkBuilder***: Declara los *sources* y *targets* de datos del *job* LRBA Spark y el uso de la  clase *Transformer*. Esta declaración abstrae en gran medida la ubicación de la persistencia física. Dependiendo del tipo de persistencia, la declaración define el nombre de una tabla en una base de datos relacional, o un archivo en una persistencia de archivos/objetos.

- Clase ***Transformer***: Implementa la transformación de datos o la lógica de negocio.

![alt text](../resources/img/concepts.png)

## Fases de ejecución de un job LRBA Spark

El proceso de ejecución LRBA tiene diferentes fases:
1. **Setup**: Configurar el ecosistema de Spark. Esta fase es implementada por la arquitectura y no requiere código de aplicación específico. 
2. **Prepare read**: La arquitectura prepara los accesos a las fuentes de datos utilizando cada origen declarado en la clase *JobSparkBuilder*. Además, la arquitectura vincula cada fuente de datos con el **alias del origen** declarado por la aplicación en la clase *JobSparkBuilder*.  
3. **Prepare Transformation**: Preparación del plan de ejecución de Spark (**DAG**) basado en el código de la aplicación y los datos obtenidos en la fase anterior. Es la única fase que utiliza la clase *Transformer*. Este código accede a cada conjunto de datos utilizando el alias de la fuente anterior. Asimismo, el código de la aplicación debe generar los *datasets* de salida de esta fase asignándoles un ***target* alias**. Esta salida son los datos que se utilizarán en la siguiente fase.
4. **Prepare write**: La arquitectura valida la salida de las transformaciones y los accesos a los *targets* utilizando cada ***target* alias** declarado en la clase *JobSparkBuilder*. Por último, los vincula con la persistencia correspondiente. 
5. **Execute**: Spark realiza la ejecución del **plan de ejecución (DAG)** que se ha preparado en las fases anteriores.


# gettingstarted/01-LRBASpark.md
# LRBA Spark

## Primeros Pasos

Antes que puedes usar el LRBA tenga en cuenta:
1. El arquitecto de la solución activa el uso de **LRBA** y **Cronos**.
2. Abrir el ticket en Helix [Aprovisionamiento de UUAA](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/734). 
Esto permite el aprovisionamiento técnico de una UUAA para que sea capaz de trabajar con el LRBA: BTS + aplicación *Appengine* + *monitored resources*.
3. Comprueba la [sección de credenciales](../../commonoperations/01-CreateCredentials.md) para ver si aplican al *job*.

## Job LRBA
### Scaffold (generación del código del Job)

Usando el siguiente diagrama, la herramienta *coder* generará un *job* basico y creará el repositorio apropiado para el proyecto adecuado.

#### Consola Ether

#### Nuevo Job

Vaya a [LRBA Ether console APP](https://bbva-ether-console-front.appspot.com/app/LRBA/25276/esp/25279) y pulse en *Add resource*

![Add resource](../../resources/img/AddResource.png)

Después, seleccione *LRA.BATCH* en el tipo

![Resource type](../../resources/img/CreateResourceType.png)

Seleccione, *Create new Batch Program*

![Resource type](../../resources/img/CreateNewBatchProgram.png)

Después, indique el tipo *JSPRK* y el nombre del *job*.

![Create job](../../resources/img/CreateJob.png)

Finalmente, pulse en *Create Resource* y después de un momento, el *job* creado puede ser encontrado en Bitbucket en el debido repositorio y proyecto.

![Create job](../../resources/img/CreateJobResourceInfo.png)

#### Versionado de Jobs

Normalmente, el componente será versionado generando nuevas *releases* en el mismo repositorio. Si es necesario crear un nuevo repositorio para la misma funcionalidad, es posible generar una nueva versión con su propio repositorio. 

De la misma manera que creamos *jobs*, seleccione *Add Resource* en la Consola Ether, elige *LRA.BATCH* y después de eso, pulse en *Link existing Program|Major version to a new Batch Program Version* y seleccione *Create New Version* del *job* deseado.

![Select Component to Version](../../resources/img/SelectComponentToVersion.png)

En la siguiente pantalla pulse *Next*.

![Version Component](../../resources/img/VersionComponent.png)

Finalmente, selecciones *Create Resource*

![Create Job Version](../../resources/img/CreateJobVersion.png)

### Desarrollar el Job

#### Estructura de Projecto

Después de generar el código inicial, un paquete similar a: `com.bbva.[UUAA].[COUNTRY].jsprk.[JOBNAME].v[JOBVERSION]` es creado. Dentro, hay un par de clases: `Job[JOBNAME]Builder.java` and `Transformer.java`

##### Job[JOBNAME]Builder

Esta clase configura el *Job*. Ahí, el desarrollador debe registrar los orígenes de datos, los destinos y la transformación.

- `registerSources()` permiete al desarrollador añadir uno o más orígenes de datos. Actualmente, los orígenes soportados son:
    - Ficheros ([BTS & Epsilon](../../utilities/spark/connectors/01-File.md))
    - Base de datos relacional ([Oracle & DB2](../../utilities/spark/connectors/02-JDBC.md))
    - Base de datos no relacional ([MongoDB](../../utilities/spark/connectors/03-MongoDB.md) & [ElasticSearch](../../utilities/spark/connectors/04-Elastic.md))

  Cada origen de datos tiene un alias asociado.

- `registerTargets()` es muy parecido al anterior método. Permite al desarrollador añadir uno o mas destinos de datos.
  Los destinos soportados actualmente son los mismos que los orígenes además de [SparkApiConnector](../../utilities/spark/connectors/05-HTTP.md). Al igual que los orígenes, los destinos también tienen que tener un alias asociado.

- `registerTransform()` permite modificar los datos provenientes de los orígenes antes de almacenarlos en los destinos.
  Una clase que contiene toda la logica de negocio asociada con el *job* puede ser especificada or instanciar un *Transformer* SQL que contenga la consulta que modifique los datos asociados al alias dado:
  `TransformConfig.SqlStatements.builder().addSql("sourceAlias1", "TRANSFORM DATA SQL").build();`

Todos los *builders* que permiten al desarrollador conectarse a diferentes orígenes de datos tienen tres campos en común:
- `alias`: el alias que el origen/destino tiene. Será usado por los *Transformers*
- `physicalName`: nombre de la tabla o colección donde los datos serán leídos o escritos.
- `serviceName`: nombre del servicio que ha sido ya creado en el inventario lógico

Puede encontrar más información sobre como conectar a los diferentes tipos de *datasources* aquí: [Spark connectors](../../utilities/spark/connectors)

##### Transformer

Esta clase configura la lógica de negocio relativa al *job* en el método `transform(Map<String, Dataset<Row>> map)`. Si son usadas sentencias SQL para transformar datos, esta clase puede ser eliminada.

Por ejemplo, el desarrollador puede querer calcular algunos valores basados en los datos provenientes de varios *Datasets*.

Este método recibe un `Map<String, Dataset<Row>>`. La clave de cada mapa es el alias que se ha indicado previamente en los *sources*. El valor asociado es el *dataset* para ese específico *source*.

Entonces, cada *dataset* puede ser modificado uniéndolos, añadiéndoles nuevas columnas, etc.

Finalmente, el método devuelve un `Map<String, Dataset<Row>>`. Este mapa es muy similar al explicado anteriormente. Sin embargo, en este caso cada clave del mapa es el alias del *target* donde el *dataset* va a ser almacenado y cada valor es el *dataset* que va a ser almacenado con su alias.

Hay un caso específico cuando puede ser devuelto `null`. Actualmente, esto sólo es aceptado si hay un **sólo origen** y un **sólo destino**. Además, ambos deben tener el **mismo alias**. Esa forma que no tiene transformación de datos sólo almacena datos que viene de un origen a un destino dado.

#### Ciclo de vida del *Builder*

Los métodos mencionados arriba `registerSources()`, `registerTransform()` y `registerTargets()` que el usuario ha implementado en la clase `Job[JOBNAME]Builder` son ejecutados de forma *lazy* en el paso que lo requiera.  
Estos métodos *register* son la primera interacción de los pasos *Prepare read*, *Prepare Transformation* y *Prepare write*.  
Este comportamiento permite usar información obtenida en los pasos anteriores en los métodos *register* y pasárselo a esos métodos a través del [ApplicationContext](../../utilities/03-LRBAApplicationContext.md).    
Por ejemplo, es posible fijar un nombre de archivo dinámico basado en los datos de entrada. Para más información: [File connector](../../utilities/spark/connectors/01-File.md)


# quickstart/persistences-usage.md
# Usos de la persistencia

LRBA permite usar las siguientes persistencias:

## Bucket temporary storage (BTS - S3)
Este almacenamiento se apoya físicamente en las funcionalidades proporcionadas por IaaS Storage a través de la tecnología *Scality Ring*. Esta tecnología proporciona una solución de almacenamiento de objetos con una interfaz S3 nativa y con todas las funcionalidades. *Scality S3 Connector* es un almacenamiento de objetos compatible con AWS S3 para aplicaciones empresariales S3 con *multi-tenancy* seguro y de alto rendimiento.

Este tipo de tecnología cubre la necesidad de almacenamiento temporal (archivos intermedios entre *jobs*) para procesos *batch* en LRBA.

El uso principal de este tipo de almacenamiento será proporcionar a los procesos de aplicación un lugar para intercambiar datos entre procesos. 

Algunos ejemplos son:
- Procesos *batch* que periódicamente descargan datos de tablas *RDBMS* y, posteriormente, los persisten en este almacenamiento temporal para ser leídos por otros procesos *batch* de la misma UUAA (por ejemplo: cargar datos a otros gestores).

- Procesos *batch* de aplicaciones complejas que necesitan dividir la lógica en etapas sucesivas (por ejemplo: un proceso genera un fichero con productos de clientes, un segundo proceso aplica comisiones a esos productos y genera otro fichero y finalmente un tercer proceso lee el segundo fichero y lo carga en la base de datos).

Se parte de los siguientes supuestos:

- Sólo habrá una ruta BTS para cada UUAA, región física (work-01, work-02, live-01, etc.), greografía (es, co, mx, etc.) y entorno lógico (dev, int, etc.) (por ejemplo: `bts-work-01-es-bc/dev/{UUAA}`).
El proceso *batch* de la aplicación podrá leer y escribir en su propio BTS y entre diferentes ámbitos funcionales (UUAA). El uso de Epsilon para esta funcionalidad está **deprecado**. 
- No será necesario gestionar estos buckets desde las áreas de aplicación: ni creación ni administración de credenciales.
- El tipo de objetos serán ficheros en formato *Parquet*.


## Epsilon Buckets - interfaces de datos (DEPRECADO)

Epsilon es un Servicio Ether de *Object Storage* que permite guardar datos como objetos (ficheros) dentro de *buckets*. Aprovechando uno de los beneficios de ser un servicio de Ether, cada *bucket* se adjunta con un *backend* y un almacenamiento.

El principal uso de este tipo de almacenamiento será permitir que las aplicaciones intercambien interfaces de datos como objetos (ficheros) dentro de *buckets* entre **diferentes arquitecturas o plataformas (Datio, Mainframe, Nextgen/LRBA...)** o **dentro de la plataforma LRBA entre diferentes aplicaciones (UUAA)**.

Algunos ejemplos son:
- Una determinada aplicación necesita implementar un proceso *batch* LRBA para cargar datos en una base de datos (por ejemplo: MongoDB) pero los datos de origen están en la plataforma Datio. Desde la plataforma Datio los datos de entrada estarán disponibles en un *bucket* de Epsilon, y el proceso LRBA los consumirá desde allí.
- Una determinada aplicación (UUAA1) necesita implementar un proceso *batch* LRBA que genere el modelo de datos de los clientes del banco. La información de los clientes se extrae de una tabla del mainframe DB2 de la propia UUAA1, pero para completar la información de los clientes necesita acceder a datos de tablas corporativas también en DB2 pero propiedad de otra UUAA2. La aplicación UUAA2 tendrá que implementar un proceso LRBA para descargar sus tablas DB2 y generar una interfaz de datos (fichero Parquet) en BTS y éste será consumido desde los procesos *batch* LRBA de UUAA1.

## Bases de datos relacionales

Actualmente, las siguientes bases de datos relacionales pueden ser utilizadas directamente desde LRBA:

- DB2 en Mainframe
- Oracle Nextgen

Los usos principales serán:
- Extracciones completas o incrementales de datos de tablas para su posterior procesamiento o carga en otras persistencias. La lógica SQL de extracción debe limitarse a SQL simples (filtrado de registros por marca de tiempo) que extraigan datos al almacenamiento temporal en BTS para preservar los recursos computacionales de estas bases de datos normalmente con actividad transaccional de otras arquitecturas críticas.
- Carga de datos en modo *upsert* (*insert* si el registro no existe en el destino, *update* si el registro existe en el destino).

## Bases de datos NoSQL

Actualmente, las siguientes bases de datos NoSQL pueden ser utilizadas directamente desde LRBA:
- MongoDB Nextgen
- ElasticSearch Nextgen

El principal uso de estas bases de datos por parte de LRBA será la carga de datos de otras bases de datos.


# lrba_docs/DeploymentCalendar.md
# Calendario de despliegues

## 3.0.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 14/07/2025 | 28/07/2025 |
| Global  | 14/07/2025 | 28/07/2025 |
| America | 21/07/2025 | 04/08/2025 |

## 2.3.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 14/07/2025 | 28/07/2025 |
| Global  | 14/07/2025 | 28/07/2025 |
| America | 21/07/2025 | 04/08/2025 |

## 2.2.1

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 23/06/2025 | 03/07/2025 |
| Global  | 23/06/2025 | 03/07/2025 |
| America | 26/06/2025 | 09/07/2025 |

## 2.2.0

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 09/06/2025 | TBD  |
| Global  | 09/06/2025 | TBD  |
| America | 12/06/2025 | N/A  |

## 2.1.4

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 08/04/2025 | 22/04/2025 |
| Global  | 08/04/2025 | 22/04/2025 |
| America | 09/04/2025 | 06/05/2025 |

## 2.1.3

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 21/03/2025 | N/A  |
| Global  | 21/03/2025 | N/A  |
| America | 01/04/2025 | N/A  |

## 2.1.2

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 19/03/2025 | N/A  |
| Global  | 19/03/2025 | N/A  |
| America |    N/A     | N/A  |

## 2.0.6

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 19/02/2025 | 25/02/2025 |
| Global  | 19/02/2025 | 25/02/2025 |
| America | 20/02/2025 | 05/03/2025 |

## 2.0.5

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 18/02/2025 | N/A  |
| Global  | 18/02/2025 | N/A  |
| America |    N/A     | N/A  |

## 2.0.4

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 28/01/2025 |    N/A     |
| Global  | 28/01/2025 |    N/A     |
| America | 30/01/2025 | 05/02/2025 |

## 2.0.3

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 21/01/2025 | N/A  |
| Global  | 21/01/2025 | N/A  |
| America | 23/01/2025 | N/A  |

## 2.0.2

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 17/12/2024 | 14/01/2025 |
| Global  | 17/12/2024 | 14/01/2025 |
| America | 20/12/2024 | 27/01/2025 |

## 2.0.1

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 10/12/2024 | N/A  |
| Global  | 10/12/2024 | N/A  |
| America | 20/12/2024 | N/A  |

## 1.1.3

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 24/10/2024 | 25/10/2024 |
| Global  | 24/10/2024 | 25/10/2024 |
| America | 15/11/2024 | 21/11/2024 |

## 1.1.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 17/09/2024 | 03/10/2024 |
| Global  | 17/09/2024 | 03/10/2024 |
| America | 26/09/2024 | 10/10/2024 |

## 1.0.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 18/06/2024 | 09/07/2024 |
| Global  | 18/06/2024 | 09/07/2024 |
| America | 15/08/2024 | 04/09/2024 |

## 0.14.1

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 21/05/2024 | 23/05/2024 |
| Global  | 21/05/2024 | 23/05/2024 |
| America | 31/05/2024 | 17/06/2024 |

## 0.14.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 12/03/2024 | 09/04/2024 |
| Global  | 12/03/2024 | 09/04/2024 |
| America | 12/04/2024 | 08/05/2024 |

## 0.13.0

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 16/11/2023 | 20/01/2024 |
| Global  | 16/11/2023 | 20/01/2024 |
| America | 20/02/2024 | 10/04/2024 |

## 0.12.1

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 13/09/2023 |    TBD     |
| Global  | 13/09/2023 |    TBD     |
| America | 20/09/2023 | 18/10/2023 |

## 0.12.0

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 12/09/2023 | N/A  |
| Global  | 12/09/2023 | N/A  |
| America |    N/A     | N/A  |

## 0.11.1

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 27/06/2023 | 11/07/2023 |
| Global  | 27/06/2023 | 11/07/2023 |
| America | 06/07/2023 | 19/07/2023 |

## 0.11.0

|  País   |    Work    | Live |
|:-------:|:----------:|:----:|
| España  | 13/06/2023 |  NA  |
| Global  | 13/06/2023 |  NA  |
| America | 14/06/2023 |  NA  |

## 0.10.4

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 25/04/2023 | 09/05/2023 |
| Global  | 25/04/2023 | 09/05/2023 |
| America | 10/05/2023 | 07/06/2023 |

## 0.10.3

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 18/04/2023 |    N/A     |
| Global  | 18/04/2023 |    N/A     |
| America |    N/A     | 19/04/2023 |

## 0.10.2

|  País   |    Work    |    Live    |
|:-------:|:----------:|:----------:|
| España  | 23/03/2023 | 10/04/2023 |
| Global  | 23/03/2023 | 10/04/2023 |
| America | 29/03/2023 | 19/04/2023 |

## 0.10.1

|  País  |    Work    | Live |
|:------:|:----------:|:----:|
| España | 16/03/2023 | N/A  |
| Global | 16/03/2023 | N/A  |

## 0.10.0

|  País  |    Work    | Live |
|:------:|:----------:|:----:|
| España | 16/03/2023 | N/A  |
| Global | 16/03/2023 | N/A  |

## 0.9.5

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 20/02/2023 | 23/02/2023 |
| Global | 20/02/2023 | 23/02/2023 |

## 0.9.4

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 19/02/2023 | 19/02/2023 |
| Global | 19/02/2023 | 19/02/2023 |

## 0.9.3

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 02/02/2023 | 07/02/2023 |
| Global | 02/02/2023 | 07/02/2023 |

## 0.9.2

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 09/01/2023 | 10/01/2023 |
| Global | 09/01/2023 | 10/01/2023 |

## 0.9.1

|  País  |    Work    | Live |
|:------:|:----------:|:----:|
| España | 13/12/2022 | N/A  |
| Global | 13/12/2022 | N/A  |

## 0.9.0

|  País  |    Work    | Live |
|:------:|:----------:|:----:|
| España | 01/12/2022 | N/A  |
| Global | 01/12/2022 | N/A  |

## 0.8.1

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 06/10/2022 | 10/10/2022 |
| Global | 06/10/2022 | 10/10/2022 |

## 0.8.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 15/09/2022 | 27/09/2022 |
| Global | 15/09/2022 | 27/09/2022 |

## 0.7.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 16/06/2022 | 05/07/2022 |
| Global | 16/06/2022 | 05/07/2022 |

## 0.6.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 24/03/2022 | 06/04/2022 |
| Global | 24/03/2022 | 06/04/2022 |

## 0.5.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 28/02/2022 | 10/03/2022 |
| Global | 28/02/2022 | 10/03/2022 |

## 0.4.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 13/01/2022 | 20/01/2022 |
| Global | 13/01/2022 | 20/01/2022 |

## 0.3.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 01/12/2021 | 08/12/2021 |
| Global | 01/12/2021 | 08/12/2021 |

## 0.2.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 28/10/2021 | 04/11/2021 |
| Global | 28/10/2021 | 04/11/2021 |

## 0.1.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 15/09/2021 | 22/09/2021 |
| Global | 15/09/2021 | 22/09/2021 |

## 0.0.0

|  País  |    Work    |    Live    |
|:------:|:----------:|:----------:|
| España | 31/05/2021 | 07/06/2021 |
| Global | 31/05/2021 | 07/06/2021 |


# lrba_docs/LRBA-Sizes.md
# Adjudicación de Tallas y Recursos LRBA 

## Tallas
Los *jobs* de Spark del LRBA lanzan un *Pod Driver* y varios *Pod Executors*. El *Pod Driver* es el orquestador del *Spark DAG (Directed Acyclic Graph)* y los *executors* están a cargo de la realización de todas las tareas sobre los *datasets*.<br />
Cada *driver/executor* es un *Pod* de *Kubernetes*, por lo que necesita una asignación de CPU+Memoria+Disco. La reserva de estos recursos es hecha de acuerdo a la siguiente tabla:<br />

<br />

|       Talla LRBA           |             Num Executors             | JVM<br />Memoria | Memoria Límite Pod<br />(JVM+Off-Heap) | spark-local-dir<br />DiskSize |
|:--------------------------:|:-------------------------------------:|:----------------:|:--------------------------------------:|:-----------------------------:|
|         standalone         |                   -                   |    1,5 GiB       |                2,1 GiB                 |               -               |
|       spark-default        | DynamicAllocation:<br />1 min / 4 max |      1 GiB       |                1,5 GiB                 |            10 GiB             |
|     spark-default-pvc      | DynamicAllocation:<br />1 min / 4 max |      1 GiB       |                1,5 GiB                 |            20 GiB (ampliable) |
|   spark-high-paralellism   |                   8                   |      1 GiB       |                1,5 GiB                 |            10 GiB             |
| spark-high-paralellism-pvc |                   8                   |      1 GiB       |                1,5 GiB                 |            20 GiB (ampliable) |
|     spark-high-memory      |                   6                   |      6 GiB       |                6,6 GiB                 |            20 GiB             |
|   spark-high-memory-pvc    |                   6                   |      6 GiB       |                6,6 GiB                 |            32 GiB (ampliable) |

<br />

***NOTA:*** Todos los jobs se crean con la talla `spark-default` sin embargo en casos donde los jobs requieren de menos recursos se recomienda bajar la talla a `standalone`.  

## Detalle de Recursos
* **Spark-local-dir Disksize**: Es el espacio de disco necesitado por Spark para realizar algunas operaciones como: *shuffle, cache, spills,* etc. El disco es reservado como *emptyDir de Kubernetes*, por lo que se usa el espacio de disco de la VM subyacente.
	* **Shuffle**: El *dataset* entero es escrito a disco para realizar operaciones que necesitan combinar datos (*joins, group by*, etc).
	* **Cache**: El *dataset* entero es escrito a disco cuando el usuario realiza una operación de persistencia en disco sobre el dataset.
	* **Spill**: Usado por Spark cuando la memoria RAM del ejecutor está completa y necesita evacuar ciertos objetos.
* **JVM Memory**: Spark divide la *jvm-heap-memory* en diferentes particiones de memoria:
	* **Reserved**: 300 MiB. Usada internamente por Spark para estructuras internas.
	* **User Memory**: `(JVM - 300 MiB) x 40%` para ser usados por el programa del usuario: *beans*, memoria asignada a funciones *dataset.map*, acumulación de operaciones *bulk* hacia bases de datos, *UDF*, etc.
	* **Spark Memory**: `(JVM - 300 MiB) x 60%` para ser usados por Spark para la ejecución de las tareas.
* **Pod Memory**: Se necesita asignar memoria fuera de la JVM (usada por el sistema y las librerías nativas) debido a que los *executors* son lanzados dentro de un *Pod* de *Kubernetes*. Por lo que, el límite de la memoria del *Pod* es la suma de la memoria JVM y de la reserva *Off-Heap*.

<br />

## Errores asociados con memoria
Cuando un programa excede cualquier límite, los siguientes errores pueden ocurrir (en términos de *task*, no de traza de error del *job*):
* **`java.lang.OutOfMemoryError: Java heap space`**: Normalmente, sucede cuando el límite de memoria del usuario es sobrepasado, por lo que la lógica de negocio del programa no está bien diseñada. Revise sus asignaciones de memoria a *bean/list/map*, reduzca *bulkSizes*, la lógica de los *UDFs*, etc.
* **`ExecutorLostFailure (executor # exited caused by one of the running tasks) Reason: The executor with id # exited with exit code 137 (SIGKILL, possible container OOM)`**: Ocurre cuando todos los procesos han excedido el límite de memoria del *Pod*. Normalmente, ocurre cuando el tamaño de las tareas del *job* es muy grande. Puede resolverse haciendo un `dataset.repartition` por la columna sobre la que se está operando. Revise el apartado de [buenas prácticas](bestpractices/01-BestPractices.md).

### Errores asociados con spark-local-dir
* **`ExecutorLostFailure (executor # exited caused by one of the running tasks) Reason: [...] Usage of EmptyDir volume "spark-local-dir-1" exceeds the limit "1Gi"`**: Ocurre cuando el límite de disco *spark-local-dir* se sobrepasa, hay mucho *shuffle*, *cache*, *spill*, etc. Intente reducir el tamaño de los *datasets* (verticalmente y horizontalmente), incremente el número de particiones, marcar los *datasets* como no persistentes, etc.
* **`Job aborted due to stage failure: Task 15 in stage 4.0 failed 4 times, most recent failure: Lost task 15.3 in stage X (TID 33) (X.X.X.X executor X): java.io.IOException: No space left on device`**: Sucede cuando el límite de tamaño del espacio *spark-local-dir* configurado con PVC (*Persistent Volume Claim*) es excedido.


# Criterios de asignación de tallas y recursos

## spark-high-paralelism

Los criterios de asignación de esta talla son los siguientes:

- Es un proceso simple, pero debido a su alta volumetría necesita trabajar con más paralelismo para reducir tiempos cuando:
	- El proceso sale de la ventana de ejecución.
	- El proceso está en una migración muy larga.
- El proceso es lineal (solo usa maps) considerándolo como un **Fase-map**.
- Se cumplen las buenas prácticas.
- La necesidad está bien justificada.

## spark-high-memory

Los criterios de asignación de esta talla son los siguientes:

- Se identifica una gran cantidad de **Spill** a disco en las fases de exchange.
- Se cumplen las buenas prácticas.
- La necesidad está bien justificada.
- Realizar un correcto reparticionado de datos en las tareas antes de las fases de **exchange** de datos.

NOTA: Si las particiones son muy grandes, razón de que el proceso esté haciendo spill se puede optar por realizar un **repartition** para evitar spill.


# Volúmenes grandes de datos

Cuando se pretenda trabajar con volúmenes grandes de datos, se recomienda lo siguiente:

- Lectura de datos en secuencial, esto quiere decir:
	-  No usar joins, sorts, groupby, etc, considerando un **Fase-map**.
-  Cuando es necesario el cruce de información (**exchange**) y por lo tanto, hacer **shuffle** lo importante es tener identificada la cantidad de disco que se necesita y realizar un particionado adecuado para evitar el spill.
-  Si se identifica que el proceso está siendo afectado por el **exchange/shuffle** a causa de la falta de memoria, es cuando se puede asignar una talla con más memoria.
-  Si el destino es una BBDD, es importante no saturarla, por lo tanto, el disco y la memoria no serán un factor relevante a considerar y un alto paralelismo pudiera tornarse contraproducente.
	-  Es fundamental también considerar los siguientes factores:
		-  Frecuencia de commit
		-  Deshabilitar índices


# Fase-map  y Fase-reduce

## Fase-reduce

Para aplicar esa transformación/acción son necesarios todos los elementos del dataset. Ejemplos:
- Contar el nº de elementos del dataset.
- Ordenar el dataset.
- Eliminar duplicados.
- Agrupar y agregar.
- Joins de ficheros

En este caso es necesario que spark tenga en su poder los datasets enteros: primero en disco, generando particiones de exchange y luego en memoria cruzando particiones entre sí.

## Fase-map

Aplica la misma transformación/acción sobre cada elemento del dataset de forma unitaria. Es como si cada elemento del dataset viviera en el map de forma independiente.
Ejemplo:
- Transformar un campo en mayúsculas.
- Multiplicar un campo por dos.
- Leer un registro de la entrada.
- Escribir un registro en la salida

Este caso **NO necesita ni memoria ni disco, es 100% lineal** y el dato de entrada fluye por los maps hasta la salida de forma independiente al resto de registros

# Incremento de disco

Se realiza comúnmente un incremento de disco cuando las operaciones de reduce, conlleven la escritura de particiones de exchange muy grandes y no quepan en el límite por defecto (son procesos que suelen fallar en stages de Shuffle Write).



# lrba_docs/ReleaseNotes.md
# Release Notes

## Versiones desplegadas

| LRBA Spark |     Work      | Live  |
|:----------:|:-------------:|:-----:|
|   Global   | 2.3.0 & 3.0.0 | 2.2.1 |
|   Spain    | 2.3.0 & 3.0.0 | 2.2.1 |
|  America   |     2.2.1     | 2.2.1 |

## Versiones de arquitectura

### v3.0.0
#### Cambios
- Se actualiza la arquitectura a **Spark 3.5.6**:
  - Un job que se ha compilado con esta versión LRBA o superior se ejecutará con Spark 3.5.6.
  - Los jobs que se han compilado con versiones anteriores de LRBA se ejecutarán con Spark 3.3.4.
  - Cualquier job que se quiera compilar tendrá que tener como versión de LRBA 3.0.0 o superior.
  - Para mas consultar el documento [LRBA MultiSpark Release](https://docs.google.com/document/d/1psfpLDQJ8GMoK4GiSUiNyiCFyUUxm4_URiPZvGQX5yU/edit?usp=sharing)
- Se sube la versión de Scala a la 2.12.18.
- Se elimina la versión 3 del conector de MongoDB, todos los jobs pasan a ejecutarse con la versión 10.4.0.
- Se permite el uso de queries inline contra Couchbase, para más información consultar [Queries inline](utilities/spark/02-DatasetInlineQueries.md).
- Se actualiza el conector de Couchbase a la versión 3.5.2.
- Añadir al `Upsert Target` de Couchbase la posibilidad de especificar el campo de id del dataset mediante `idField`. Para más detalles sobre este cambio, consulte: [Couchbase](utilities/spark/connectors/06-Couchbase.md).
- Activar los PushDown de agregaciones en Couchbase.
- Actualizar el Target JDBC Transactional para modificar la firma del método `write` en `JdbcTransactionWriterHandler`, que ahora recibe un `Map<String, Object>` en lugar de `InternalRow`. Para más detalles sobre este cambio, consulte: [JDBC](utilities/spark/connectors/02-JDBC.md#transactional).
- Actualizar el Source Http para implementar el método `get` de la clase `HttpRequestReaderHandler`.
Se elimina la necesidad de que los consumidores implementen el método get en la clase hija ApiProvider, ya que ahora está implementado en HttpRequestReaderHandler.
Para más detalles sobre este cambio, consulte: [HTTP](utilities/spark/connectors/05-HTTP.md#Implementar la clase `HttpReaderRequestHandler`)..
- Actualizar la versión del AWS Java SDK a la 1.12.367.

### v2.3.0
#### Cambios
- Se actualiza la versión del conector de Couchbase a la 3.3.6.

### v2.2.1
#### Cambios
- Se permite leer mediante inline queries usando impersonación de UUAAs.
- Se añade la validación del hostname al conectar al DB2 mediante mTLS.

### v2.2.0
#### Cambios
- Se actualiza la versión SDK Chameleon a la 2.62.1.
- Mejorada la forma de escritura de ficheros. Mientras dura el proceso de escritura, los ficheros primero se escribirán en un path temporal cuyo formato es {runId}/{physicalName} hasta que finalice su escritura. Una vez finalizada, se moverá el fichero al path final donde el formato no contendrá el {runId} especificado anteriormente. Con esta mejora, en el DAG se podrá visualizar el nombre del fichero final que se va a escribir y no un .tmp con un uuid autogenerado.
- Modificar el código de retorno funcional del estado `ForceStop` y añadir el estado `Launcher Error`. Para mas información consultar [Código de retorno funcional](utilities/05-LRBAApplicationExitCode.md).
- Se permite realizar queries inline contra Oracle, Elasticsearch y MongoDB mediante la iteración de los datasets. Para más información consultar [Queries inline](utilities/spark/02-DatasetInlineQueries.md).
- Actualización de la version de ElasticSearch de 8.4.1 a 8.10.0.
- Se cambia el método de autenticación con el DB2 a mTLS.

### v2.1.4
#### Cambios

- Se añade el método `Encoders.row()` para sustituir el uso de `RowEncoder.apply()` para facilitar la compatibilidad con Spark 3.5 cuando se actualice la Arquitectura.
- Se añade dependencia `junit-jupiter-params` como test.
- Se corrige el uso de InputParams en los test unitarios.

### v2.1.3
#### Cambios

- Añadir la dependencia `spark-core` como test.
- Detectar `alias` de datasets con puntos (no permitido a partir de Spark 3.5).
- Corregir mensaje de error en el conector Jdbc con campos nulos.
- Corregir dependencias scala con el conector couchbase.
- Fecha cabecera GL01 en hora local del pod y timezone.

### v2.1.2
#### Cambios

- Se habilita en la historificación el uso de nombres dinámicos de tablas por patrón de fecha. Para mas información consultar [Historificacion. Uso de nombres dinámicos de tablas](utilities/historificacion/02-HowItWorks.md#uso-de-nombres-dinámicos-de-tablas-por-patrón-de-fecha)
- Se habilita la escritura de ficheros binarios con el conector de tipo [File](utilities/spark/connectors/01-File.md)
- Mejorada la forma de escritura de ficheros. Mientras dura el proceso de escritura, los ficheros primero tendrán un nombre temporal hasta que finalice su escritura. Esto minimiza la probabilidad de error cuando hay procesos leyendo un fichero, que, por otro lado, se está sobreescribiendo.
- Se habilita la opción de que la arquitectura cambie el lenguaje de las cabeceras de BEA a GL01
- ~~Se actualiza la arquitectura a Spark 3.5.4.~~
- ~~Se sube la versión del conector de Couchbase a la 3.5.2.~~
- Se actualiza el *driver* de MongoDB a la versión 5.1.4 y el *mongo-spark-connector* a la versión 10.4.0.
- Se sube la versión del conector de Cobrix a la 2.8.0.
- ~~Se sube la version de scala a la 2.12.18~~
- Se permite configurar la ruta de instalación del CLI. Para más información consultar [CLI](developerexperience/01-HowToWork.md)
- Actualizadas las imágenes base de la arquitectura para utilizar una RHEL UBI 9.4.
- ~~Se depreca el uso de `RowEncoder.apply()` al ser una clase del optimizador interno `catalyst`. Se tiene que cambiar su uso por `Encoders.row()`.~~
- ~~Se bloquea en Sonar el uso del optimizador interno de Spark `spark.sql.catalyst`.~~
- Se permite el uso de la operación Update en el conector JDBC. Para más información consultar [Update](utilities/spark/connectors/02-JDBC.md#Update).
- Se añaden las librerías `commons-lang3` y `commons-text` a las [dependencias incluidas en la arquitectura](utilities/04-LRBADependencies.md#Dependencias-incluidas).
- Se depreca el uso de `commons-lang` en favor de `commons-lang3`.
- Se realizan validaciones sobre los inputParams de los jobs debiendo de ser todos de tipo String.

### v2.0.6
#### Cambios

- Solucionar un error con la combinación de parámetros `deleteFile` e `ignoreMissingFiles`.

### v2.0.5
#### Cambios

- Solucionar un error que no permitía un correcto borrado y movimiento de ficheros con el uso de wildcards en el `physicalName`.

### v2.0.4
#### Cambios

- Forzar visibilidad privada al escribir ficheros en el inbox de otra UUAA.

### v2.0.3
#### Cambios

- Borrar ficheros de los bucket de las deadletters de BEA mediante el parámetro `deleteFile`.

### v2.0.2
#### Cambios

- Crear los pods ejecutores de los jobs en la misma AZ que el driver asociado.

### v2.0.1
#### Cambios

- Habilitación de la lectura de ficheros binarios con el conector de tipo File, para más información consultar la documentación del [conector](utilities/spark/connectors/01-File.md)
- Se sube la versión del conector de Couchbase a la 3.3.5.
- Añadir Couchbase Partitioned Source. Para más detalles sobre este cambio, consulte: [Couchbase](utilities/spark/connectors/06-Couchbase.md).
- Se añade un nuevo Target JDBC Transactional. Para más detalles sobre este cambio, consulte: [JDBC](utilities/spark/connectors/02-JDBC.md).
- Se permite mover y borrar ficheros de BTS tras su procesamiento mediante el uso de Wildcards.
- Se permite la opción de ignorar ficheros creados posteriormente al arranque del job.
- Se incluye el módulo externo `Apache POI`, consulte [Dependencias externas](utilities/04-LRBADependencies.md)
- Se añade el conector GRPC BEA para publicar eventos en BEA. Para más detalles sobre este cambio, consulte: [GRPC BEA](utilities/spark/connectors/07-BEA.md).
- Se permite el uso de configuración personalizada para el conector spark de [JDBC](utilities/spark/connectors/02-JDBC.md)
- Se incluye la funcionalidad para la lectura y procesamiento de las [deadlletters de BEA](utilities/spark/connectors/01-File.md).

### v1.1.3
#### Cambios

- Se corrige un error que hacía que algunas contraseñas de couchbase se expusiesen en los logs.
- Se corrige un error que afectaba al conector http usando la autentiación oauth con proxy.

### v1.1.0
#### Cambios

- Se permite enviar binarios a través del conector HTTP REST Target añadiendo la cabecera `Content-Type` con el valor `application/octet-stream`. Para más detalles sobre este cambio, consulte: [HTTP REST Target](utilities/spark/connectors/05-HTTP.md).
- Se añade el conector Couchbase para leer, escribir y borrar en colecciones de Couchbase. Para más detalles sobre este cambio, consulte: [Couchbase](utilities/spark/connectors/06-Couchbase.md).
- Se soluciona un error que impedía usar el conector de lectura HTTP con Proxy. 
- Habilitado el uso de los métodos persist y unpersist del API dataset de Spark.
- Deprecado de los métodos cacheDataset y unpersistDataset de la clase DatasetUtils.
- Actualizacion de la arquitectura a Java 17:
  - Todos los procesos (nuevos y viejos) se ejecutarán siempre sobre una JVM version 17.
  - Modificación pipeline aplicativo: maven corre sobre Java 17 y pasar calidad contra Sonar 9.
  - Los nuevos proyectos con pom-parent >= 1.1.x se compilarán a bytecode java 17
  - Los antiguos proyectos con pom-parent <= 1.0.x se seguirán compilando a bytecode java 11
  - Actualizado el lrba-cli para trabajar internamente con una jvm+jdk java 17
  - Para cargar un proyecto en un IDE local, es necesario que el IDE apunte a una jvm+jdk java 17
  - El VisorBTS se ejecuta sobre java 17
- Se permite la escritura en el bucket de otra UUAA en función de los permisos de impersonación entre UUAA.
- Liberada Arquitectura de Historificación, en modo PoC para aplicaciones seleccionadas.
- El FileWatcher BTS ahora admite wildcards (*, ?) en el nombre del fichero que se está vigilando.

### v1.0.0
#### Cambios

- En el inventario BTS (disponible en la Consola de LRBA), solo aparecerán entradas históricas correspondientes a ficheros de los últimos 60 días.
- Actualizadas las imágenes base de la arquitectura para utilizar una RHEL UBI 8.8.
- Se permite el uso del Update para el conector de [ElasticSearch](utilities/spark/connectors/04-Elastic.md)
- Habilitación de la lectura de ficheros Json con el conector de tipo File, para más información consultar la documentación del [conector](utilities/spark/connectors/01-File.md)

### v0.14.1
#### Cambios

- Se depreca la clase SparkHttpData por incompatibilidades con la versión 3.4 de Spark y se incluye la interfaz [ISparkHttpData](utilities/spark/01-Utils.md#envío-de-datasets-a-un-api-http) en su lugar.

### v0.14.0
#### Cambios

- Se permite el uso de SinglePartitionPartitioner para el conector de MongoDB. Para más detalles sobre este cambio, consulte [SinglePartitionPartitioner](utilities/spark/connectors/03-MongoDB.md) 
- Se permite el uso de secuencias en el conector JDBC, [Sequence](utilities/spark/connectors/02-JDBC.md#sequence).
- Se permite especificar un código de retorno funcional. Los números disponibles son del 0 al 127 ambos incluídos. Consulte [Código de retorno funcional](utilities/05-LRBAApplicationExitCode.md)
- Permitir el uso de la propiedad `docsPerPartition` para generar particiones con el número de documentos establecidos al momento de leer de Elastic.
- Subir versión SDK Chameleon a la 2.54.0.
- Controlar errores de Vault en el entrypoint de la arquitectura.
- Se actualiza la arquitectura a Spark 3.3.4.
- Se permite el uso de configuración personalizada para el conector spark de [ElasticSearch](utilities/spark/connectors/04-Elastic.md). 
- Se actualiza la trazabilidad para consumo de db2.
- Permitir lecturas API HTTP. Para más detalles sobre este cambio, consulte el conector [HTTP](utilities/spark/connectors/05-HTTP.md).
- Se actualiza el LRBA CLI, permitiendo elegir la versión con la que se quiere ejecutar el job.

### v0.13.0

- Se actualiza la imagen de arquitectura para incluir jq.
- Se modifica la arquitectura para que haga uso de la nueva clave del inventario físico "location".
- Se modifica el entrypoint para que las peticiones al vault tengan 3 reintentos con un delay de 60 segundos.
- Se permite usar la función `ignoreMissingFiles` en ficheros de otras UUAAs.

### v0.12.2
#### Cambios

- Se guarda el applicationId de Spark para poder leer correctamente el Spark History con la talla spark-standalone.

### v0.12.1
#### Cambios

- Se corrige error en las validaciones de permisos en el target Http.
- Se corrige error en las validaciones de permisos cuando se escribe en Epsilon.
- Se añade un log para conocer qué versión del conector de MongoDB está usando el proceso.

### v0.12.0
#### Cambios

- Se actualiza el *driver* de MongoDB a la versión 4.8.2 y el *mongo-spark-connector* a la versión 10.1.1.   
  Se sigue manteniendo la versión anterior del conector 3.0.2. La versión utilizada por defecto es la 10.1.1 y se permite solicitar que 
  un job concreto se ejecute con la versión 3.0.2, mientras se revisa y se adapta a la nueva versión.   
  Por favor, revise la [guía de migración](utilities/spark/connectors/03-MongoDB.md#guía-de-migración-a-la-nueva-versión-del-conector-de-mongodb) para adaptar un job a la nueva versión de MongoDB.
- Se migra la imagen del pipeline aplicativo a Artifactory VDC.
- Se añade el comando `version` al CLI.
- Utilizar informe de cobertura de Jacoco en formato XML en Sonar.
- Se permite eliminar despliegues.
- Se corrige el error que impedía ignorar en lectura ficheros de UUAAs diferentes a la de ejecución.

### v0.11.2
#### Cambios
Adaptar la función `moveFilePath` del *File Builder* a los Buckets unificados por ámbito Fresno.

### v0.11.1
#### Cambios
- Marcha atrás del *driver* MongoDB a 4.0.5 y *mongo-spark-connector* a 3.0.2. 
- Se ha corregido un error por el cual al usar repartitionColumn con humanReadable y aquel tiene "/" en el campo no funcionaba correctamente.


### v0.11.0
#### Cambios

- Añadida la posibilidad de bloquear *jobs* en caso de que sean peligrosos para el clúster.
- Habilitadas las operaciones de borrar y mover añadiendo las propiedades `deleteFile` y `moveFilePath` en el *File Builder*.
- Creada nueva configuración *spark-standalone*.
- Migrado LRBA CLI de Bitbucket y Artifactory Stocks a Bitbucket y Artifactory VDC.
- Añadida la UUAA al servicio lógico desde el campo `uuaaOwner` del inventario lógico. Si no existe, se infiere del nombre del servicio.
- Actualizar *driver* MongoDB a 4.8.2 y *mongo-spark-connector* a 10.1.1.
- Modificado *CryptoWrapper* para hacerlo serializable.
- Añadida la capacidad de reparticionar datos añadiendo propiedades `repartitionColumn` en el *File Target Builder*.
- Los *sources* de Elastic pueden ser configuradas para evitar el parseo de fechas y recuperarlas como valores primitivos.
- Actualizadas las imágenes base de la arquitectura para utilizar una RHEL UBI 8.6.
- Añadido un step final para cerrar *SparkSession*.
- Refactorizado el contexto de trazabilidad para adaptarlo a las nuevas características.
- Cortar acceso por *proxy-noauth* al *bucket* de la caché de Jenkins VDC.
- Se ha corregido un error por el cual se ignoraban opciones de lectura que se le pueden indicar al *builder* de texto plano.
- Se elimina el acceso a Epsilon para el entorno de Desarrollo.


### v0.10.4
#### Cambios
- Se modifica la función `ignoreMissingFiles` para permitir *wildcards*.

### v0.10.3
#### Cambios
- Se modifica *ElasticDeleteTargetBuilder* para permitir el borrado de registros en los que el id y el *routing field* son diferentes.

### v0.10.2
#### Cambios
- Se han implementado reintentos en las solicitudes de Vault.
- Se han aumentado los tiempos de espera de Epsilon.
- Se ha reducido el intervalo de comprobación del estado del *job* desde Control-M.

### v0.10.1
#### Cambios
- Se ha corregido la excepción *NoSuchMethodError* que se producía con el método *routingField* en *ElasticUpsertTargetBuilder*.

### v0.10.0
#### Cambios

- Actualizar la versión del módulo externo `Crypto`, consulte [Dependencias externas](utilities/04-LRBADependencies.md)
- Conector Epsilon deprecado, utilice el servicio [BTS](https://platform.bbva.com/lra-batch/documentation/9229695829655935d63f723e3b92fb97/lrba-architecture/utilities/spark/connectors/files-connector#content3) en su lugar.
- Evitar que los *jobs* que se detienen forzosamente se guarden con el estado *FAILED*.
- Modificado el registro de errores de permisos del servicio para clarificarlo.
- Gestión de errores cuando se ejecuta una parada forzada.
- Se añade una validación para comprobar que el nombre de servicio asignado en el constructor es correcto.
- Permitir el uso de opciones de archivo Spark en el *File Builder*. Para más detalles sobre este cambio, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Permitir controlar el error en la lectura de archivos ausentes. Para más detalles sobre este cambio, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Modificado el Visor BTS para permitir la carga de archivos. Para más detalles sobre este cambio, consulte:  [Subir archivo](developerexperience/06-BTSVisor.md).
- Etiquetar archivos BTS y persistir todos los metadatos asociados a cada archivo BTS pertenece a *HTTP REST target*.
- Permitir el uso de la propiedad `bulkSizeMB` en el Elastic *Target Builder*. Para más detalles sobre este cambio, consulte: [Elastic](utilities/spark/connectors/04-Elastic.md).
- Control del tiempo de espera de Elastic mediante una variable de entorno.
- Corregido un error que se produce con el *classpath* de módulos externos.
- Alinear el acceso al Vault de configuración.

### v0.9.5
#### Cambios

- Corregida la forma en la que la arquitectura obtiene los permisos de impersonación.

### v0.9.4
#### Cambios

- Migración a Artifactory VDC.

### v0.9.3
#### Cambios

- Se ha corregido la forma de etiquetar los archivos de salida.

### v0.9.2
#### Cambios

- Se ha corregido el modo en que Spark actualiza las credenciales de Hadoop AWS para acceder a BTS.
- Se actualiza el LRBA CLI, que permitirá generar los ficheros de configuración para acceder a los diferentes almacenamientos.

### v0.9.1
#### Cambios

- Reduce el TTL de los archivos en la configuración de BTS `fileAvailability`. Valor por defecto: 3 días.

### v0.9.0
#### Cambios

- Actualización del conector Epsilon de 1.5.0 a 1.7.0.
- Actualización del conector Cobrix de 2.5.0 a 2.5.1.
- Actualización del controlador ojdbc11 de 21.6.0.0.1 a 21.7.0.0.
- Actualización del conector spark de ElasticSearch de 7.17.5 a 8.4.1.
- Añadida propiedad `spark.archives` para subir archivos comprimidos a los *executors*.
- Modificada la propiedad `spark.files` para propagar recursos binarios a los *executors*.
- Añadida la lógica para controlar donde se escribe el *spark-history*.
- Permitir el uso de la propiedad `fileVisibility` en el *FileBuilder*.
- Añadido el campo `schema` en el builder para forzar el esquema al leer de MongoDB.
- Comprobación del estado final de un *job*.
- S3 Magic Committer habilitado por defecto.
- Añadido UUAA a las propiedades de *job* *span*.
- Reducido a 10 el *bulkSize* mínimo para operaciones JDBC, MongoDB y Elastic.
- Habilitado el puerto de depuración en la interfaz de línea de comandos de LRBA.
- Reducir el número de *namespaces* en *Kubernetes*.  
    * Antes: uno por aplicación, país y entorno.  
    * Después: uno por país y entorno.
- El tipo de volumen *K8S* utilizado hasta ahora en *spark-local-dir* ha sido de tipo *emptyDir*.
  A partir de ahora, PVC (Persistent Volume Claim) será el tipo de volumen utilizado, con el fin de proporcionar más capacidad de almacenamiento.
- Permitir la partición por fecha en el Conector JDBC.
  Para más detalles sobre este cambio, consulte la sección *Particionado* aquí: [JDBC](utilities/spark/connectors/02-JDBC.md).

### v0.8.1
#### Cambios

- Corregido error que bloqueaba el cierre correcto de *jobs* k8s.

### v0.8.0
#### Cambios

- Permitir el uso de la propiedad `fileAvailability` en el File Builder.
  Para más detalles sobre este cambio, consulte: [File](utilities/spark/connectors/01-File.md).
- Disponibilizar la integración SDK Crypto lanzar CryptoWrapper.
  Para obtener más información sobre este cambio, consulte: [External Dependencies](utilities/04-LRBADependencies.md).
- Se ha actualizado la arquitectura a Spark 3.3.0.
- Permitir el uso de la propiedad `semaasHeaders` en el HTTP REST Target. Para más detalles sobre este cambio, consulte: [HTTP API](utilities/spark/connectors/05-HTTP.md).
- Permitir el uso de la propiedad `addElasticFieldAsArray` en el Elastic Reader. Para más detalles sobre este cambio, consulte: [Elasticsearch](utilities/spark/connectors/04-Elastic.md).
- Cambiar Artifactory a S3 como repositorio binario en tiempo de ejecución.
- Limitar el tamaño de emptyDir en k8s.
- Actualización de la imagen `ubi8/ubi-minimal` de 8.2 a 8.4.
- Eliminar `XStream` como dependencia de arquitectura, las aplicaciones pueden importarlo como se describe en [External Dependencies](utilities/04-LRBADependencies.md)
- Eliminar la colección Mongodb `c_lrba_buffer_status` no utilizada.
- Actualice los controladores de la base de datos y la versión de los conectores.

### v0.7.0
#### Cambios

- Se permite utilizar los métodos `Dataset.repartition` y `Dataset.coalesce`
- Permitir añadir dependencias externas, consulte [External Dependencies](utilities/04-LRBADependencies.md).
- Se permite registrar UDFs en Spark SQL, consulte [Utils](utilities/spark/01-Utils.md).
- El conector MongoDB permite combinar o reemplazar documentos en operaciones upsert.
  Para más detalles sobre este cambio, consulte la sección *Upsert* aquí: [MongoDB](utilities/spark/connectors/03-MongoDB.md).
- Reducido a 25 el bulkSize mínimo para operaciones JDBC, MongoDB y Elastic.
- Añadidos métodos opcionales en FileTarget: fileAvailability, informationContentType y fileVisibility.
  Para obtener más detalles sobre cómo utilizarlos, y los valores de campo disponibles consulte cada constructor de destino aquí: [Ficheros](utilities/spark/connectors/01-File.md).
- Etiquetar ficheros BTS y persistir en Mongo todos los metadatos asociados a cada fichero BTS.
- Controlar si una UUAA tiene permiso para persistir ficheros públicos en BTS.
- Hacer disponible la librería Objenesis para corregir errores de serialización.
- Establecer GZIP como compresor de Parquet por defecto.
- Registrar la consulta eliminada para el objetivo de eliminación JDBC.
- Permitir certificados generados a través de WebRA en el *HTTP Connector*. Para más detalles sobre este cambio, consulte: [Crear credenciales](commonoperations/01-CreateCredentials.md).
- El formato de las credenciales en el *HTTP Connector* ha sido modificado. Para más detalles sobre este cambio, consulta: [*HTTP Target*](utilities/spark/connectors/05-HTTP.md).


### v0.6.0
#### Cambios

- Eliminadas funcionalidades OC 3.11.
- Añadido el método `getOrThrow` a `LRBAProperties`.
  Para más detalles sobre este cambio, consulte: [LRBAProperties](utilities/01-LRBAProperties.md).
- Añadir Cobol Source.
  Para más detalles sobre este cambio, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Añadir utilidad para simular variables de entorno en las pruebas.
  Para más detalles sobre su uso, consulte: [Utilidades](utilities/spark/01-Utils.md).
- Añadir configuración de proxy para las llamadas REST de la API.
  Para más detalles sobre este cambio, consulte: [HTTP](utilities/spark/connectors/05-HTTP.md) y [Utilidades](utilities/spark/01-Utils.md).
- Admite autenticación mTLS para llamadas REST de API.
  Para más detalles sobre este cambio, consulte: [HTTP](utilities/spark/connectors/05-HTTP.md).

### v0.5.0
#### Cambios

- Se ha actualizado la arquitectura a Spark 3.2.1.
- Se ha mejorado la captura de errores JDBC. Si una escritura JDBC falla, la arquitectura imprime un log con la clave primaria de la fila errónea.
- El método `registerSteps` de la clase abstracta `RegisterSparkBuilder` ha sido declarado `final` para evitar errores.
- Añadir objeto de destino de base de datos para establecer *bulkSize* personalizado para una operación.
- URL de Elastic en archivo de inventario físico contiene el protocolo (http, https o Elastic).
- Aplicar política de reintentos al descargar jar desde Artifactory.
- Cambios internos en el conector epsilon debido a que Spark v3.2.1 asigna nuevos nombres a archivos temporales en operaciones de escritura.

### v0.4.0
#### Cambios

- Renombra el campo de filtro de MongoDB *Upsert*. Antes era `addPkField` y ahora es `addQueryKey`.
  Para más detalles sobre este cambio, consulte la sección *Upsert* aquí: [MongoDB](utilities/spark/connectors/03-MongoDB.md).
- Renombrar el método *HTTP REST Target builder vaultPath* a *credentialsKey*. Ahora sólo es obligatorio especificar la última parte de la ruta. Para más detalles sobre este cambio, consulte: [*HTTP Target*](utilities/spark/connectors/05-HTTP.md).
- Añadir *File Source* de texto plano.
  Para más detalles sobre este cambio, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Preservar los espacios en blanco en los archivos CSV a través de Spark.
  Para más detalles sobre cómo utilizarlo, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Modificar el formato de algunos campos en el evento de contexto de trazabilidad.
- Se ha configurado la memoria disponible para la JVM en la fase de pruebas y se ha incrementado en los pipeline workers.
- Se añade la gestión de errores de timeout cuando se utiliza el *HTTP REST Target*.
  Para más detalles sobre este cambio, consulte: [*HTTP Target*](utilities/spark/connectors/05-HTTP.md).

### v0.3.0
#### Cambios

- Añadir Spark *test utilities*.
  Para más detalles sobre cómo utilizarlas, consulte: [*Utilidades*](utilities/spark/01-Utils.md).
- Cambiar el ciclo de vida de los builders. Ahora es perezoso, lo que permite utilizar la información obtenida en el paso anterior. Por ejemplo, es posible establecer un nombre de archivo dinámico basado en una fuente de datos de entrada. Para más detalles sobre cómo utilizarlo, consulte: [LRBASpark](quickstart/gettingstarted/01-LRBASpark.md) y [Ficheros](utilities/spark/connectors/01-File.md).
- Añadir contexto de trazabilidad con información de fuentes de entrada/salida.
- Definir formato de variables de entorno de arquitectura.
- Detectar errores en la descarga del JAR de la aplicación.
- Unificar CAs del banco y del sistema.

### v0.2.0
#### Cambios

- Añadir target de fichero texto plano.
  Para más detalles sobre su uso, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Añadir human-readable en archivos CSV y de texto plano para escribir un único archivo sin partición.
  Para más detalles sobre cómo utilizarlo, consulte: [Ficheros](utilities/spark/connectors/01-File.md).
- Poner a disposición la biblioteca [*XStream*](https://x-stream.github.io/) para serializar objetos a XML y viceversa.

### v0.1.0
#### Cambios

- Añadir el método [unpersist()](https://spark.apache.org/docs/latest/api/java/org/apache/spark/sql/Dataset.html#unpersist--) en *DatasetUtils*.
  Para más detalles sobre cómo usarlo, consulte: [Spark Utils](utilities/spark/01-Utils.md) - sección *No persistir Datasets*.
- Añadir conector *HTTP REST API* que permite ejecutar llamadas utilizando Spark *Dataset*.
  Para más detalles sobre cómo utilizarlo, consulte: [Conector HTTP](utilities/spark/connectors/05-HTTP.md).
- Trazabilidad Epsilon E2E. Es posible habilitarla, pero hay que hacerlo manualmente ya que genera mucho ruido en Atenea.
  Para habilitarla, abra un [Jira](Support.md) al equipo LRBA.

### v0.0.0
#### Cambios

Versión inicial LRBA Spark que incluye los conectores a BTS, Epsilon, DB2, Oracle, MongoDB y Elasticsearch.


# lrba_docs/Training.md
# Formación



## [TechU](https://bbva-techuniversity.appspot.com/bootcamp/LRBA_DEV_ES)

Contamos con un curso especializado de desarrollo de Jobs aplicativos disponible en la plataforma de TechU, que capacita a los usuarios para obtener conocimientos en:

- Apache Spark
- Diseño y desarrollo de Jobs aplicativos LRA Batch
- LRA Batch y Development Experience
- Planificación de un Job
- Monitoreo y Análisis de Jobs aplicativos mediante LRBA console

## [Codelabs](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/)

En la sección de Codelabs, contamos con una variedad de laboratorios que permiten a los usuarios comprobar como se realizan algunas de las configuraciones, desde las más básicas a las más complejas, en un job de LRBA.

