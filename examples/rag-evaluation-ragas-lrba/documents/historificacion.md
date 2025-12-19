# historificacion/01-WhatIsHistorificacion.md
# ¿Qué es Historificación?

La *Historificación* se trata de:
1. **El movimiento de un periodo antiguo de datos** desde un gestor de alto rendimiento y elevado coste, **a otro de bajo rendimiento y coste**. 
2. **Este nuevo gestor pasa a tener el dato maestro** correspondiente a periodos antiguos y poco accedidos.
3. **Sin posibilidad de retorno** al gestor original (no es backup)
4. **Por un tiempo limitado** (hasta 10 años).
5. Sobre el nuevo gestor se deben de ofrecer **capacidades offline de consulta y procesamiento**.

LRBA proporciona una utilidad que permite la historificación de datos de una base de datos *NextGen* para almacenarlos en un archivo a largo plazo.

La utilidad de historificación está basada en la Arquitectura de LRBA, y su configuración permite seleccionar automáticamente los datos que se quieren almacenar a largo plazo. 

# Empezar a utilizar la utilidad de Historificación

En este caso, la utilidad de Historificación estará gobernada por el Equipo de LRBA. Para solicitar el acceso a la ejecución de la utilidad, se deberá proporcionar la siguiente información por cada servicio que se quiera archivar:

- País
- Entorno
- Gestor de Base de Datos 
- Service Name
- Tabla/Colección
- Período de Historificación
- Número de Períodos a Conservar en BBDD
- Fecha del Primer Dato a Historificar
- Tamaño Medio de Registro
- Símbolo
- Número Medio de Registros por Período de Historificación
- Ocupación de Tabla/Colección en Origen
- Símbolo
- Período de Retención
- Fecha Primera Planificación Historificación
- Previsión de Crecimiento (%)
- Justificación

Una vez se recopile toda esta información se deberá enviar en un documento utilizando esta [plantilla](https://docs.google.com/spreadsheets/d/1P6X6XMY8KPabjALj4jaXe3ddx607EWbQQo43J0kch8c) al buzón de *lrba.europe.group* o *lrba.america.group* dependiendo del país del aplicativo.

# historificacion/02-HowItWorks.md
# Cómo funciona el proceso de Historificación
La utilidad de historificación, en base a los parámetros de ejecución, se encarga de calcular el período de datos que se quiere almacenar en el archivo. El almacenamiento de datos en el archivo se hace de manera ordenada en base a gestor, base de datos, tabla y fechas que comprende el período almacenado (día, mes o año) para que el procesamiento offline de datos sea más sencillo en caso de que sea necesario. Cabe destacar, que la utilidad de historificación **NO BORRA** los datos que se quieren historificar. Si se quieren borrar se deben utilizar las herramientas disponibles para cada gestor.

Por otro lado, se debe tener en cuenta que la utilidad de historificación trabaja con *períodos*, entre los que nos encontramos: 
- Período "vivo" es aquel en el que se encuentra la fecha actual de ejecución de la utilidad de historificación. Este período **SE DESCARTA** del cálculo de períodos a mantener en base de datos.
- Período/s a mantener en Base de Datos son aquellos que el aplicativo desea conservar en el gestor (adicional al período vivo).
- Período a historificar es el período inmediantamente anterior al número de períodos que se quieren mantener en base de datos y el período vivo.
- Período/s ya historificados son aquellos períodos que se consideran anteriores al período que se quiere archivar.

![alt text](../../resources/img/HistorificacionPeriodos.png)

En conclusión, si un aplicativo desea historificar deberá tener en cuenta principalmente cuantos períodos desea mantener en base de datos. Además, deberá considerar que el período vivo no forma parte en el cálculo de los períodos a mantener en base de datos.

Tomemos como referencia la imagen anterior, en la que hay:
- 1 período vivo
- 4 períodos a mantener en base de datos
- 1 período a historificar
- ≥ 4 períodos ya historificados

Pongamos por ejemplo que se ejecuta la utilidad de historificación el 4 de Febrero de 2024, y que se desean conservar 4 períodos en base de datos. En este caso, se esperaría:

| Período de Historificación | Período Vivo | Período/s a mantener en BBDD | Período a historificar | Período/s ya historificados | 
|:-------------:|:-------------:|:-------------:|:-------------:|:-------------:|
| Día | 4 de Febrero de 2024 | 31 de Enero de 2024, 1, 2, 3 de Febrero de 2024 | 30 de Enero de 2024 | ≤ 29 de Enero de 2024 |
| Mes | Febrero de 2024 | Octubre, Noviembre y Diciembre de 2023 y Enero de 2024 | Septiembre de 2023 | ≤ Agosto 2024 |
| Año | 2024 | 2020, 2021, 2022, 2023 | 2019 | ≤ 2018|

# ¿Cómo configurar la utilidad de Historificación?

La utilidad de Historificación sólo se podrá configurar a través del planificador [*Cronos*](https://platform.bbva.com/cronos/documentation/1vbxGe22lksmJr6WFRp7MjJ8yYLjtit7PCl0ZdKVTTm4/what-is). Una vez se crea un nuevo Job, selecciona Tasks y añade una nueva tarea de LRBA Archiving que se puede encontrar bajo la sección Services.

![alt text](../../resources/img/HistorificacionCronosJob.png)

En la imagen anterior se encuentran los parámetros necesarios para ejecutar una Tarea de tipo Historificación en Cronos para el gestor de bases de datos Oracle. Aunque está seleccionado el gestor de Oracle, los parámetros que se muestran son comunes a todos los gestores:

| Campo |     | Valor del campo | Descripción | 
|-------|-----|-----------------|-------------|
| Service | Obligatorio | Oracle, MongoDB o Elasticsearch | Gestor de base de datos |
| Service Name | Obligatorio | {PROVIDER}.{UUAA}.BATCH | Nombre del servicio que se va a archivar |
| Physical Name | Obligatorio | {SCHEMA}.{ENTITY} | Nombre de la entidad del servicio que se va a archivar. {SCHEMA} cuando el origen de los datos sea Oracle|
| Filter Column Type | Obligatorio | DATE, TIMESTAMP, NONE | Tipo de la columna de filtro de fecha |
| Filter Column Name | Obligatorio en caso de COLUMN_TYPE != NONE | | Nombre de la columna de fecha que se utilizará como filtro de la entidad. En caso de COLUMN_TYPE==NONE es ignorado |
| Information Type Classification | Obligatorio | NON PROTECTED DATA, PERSONAL IDENTIFICATION, FRAUD ENABLERS, SECRETS AND KEYS, SENSITIVE PERSONAL DATA o INTERNAL USE | Clasificación de los datos que se van a almacenar  |
| Execution Date | Obligatorio | DATE: Fecha con formato DD/MM/YYYY. MACRO: Utilizando el valor {{ ds }} para que la fecha se corresponda con la fecha de planificación. | Indica la fecha de momento de ejecución (diferente de la fecha de planificación) |
| Period Time Unit | Obligatorio | DAY, MONTH, YEAR | Unidad de tiempo que se seleccionará como el período de tiempo que se archivará |
| Periods to Keep in Database | Obligatorio | ≥ 0 | Número de períodos, basado en la unidad de tiempo del período, que se mantendrá en la base de datos |
| Years to Keep in Archive | Obligatorio | 1 - 10 | Número de años que los datos archivados se almacenarán. En Entornos Previos, el número máximo de años es 1.|

Adicionalmente, para MongoDB y Elasticsearch existen parámetros adicionales que hay que completar:

| Gestor | Campo |     | Descripción | 
|--------|-------|-----|-------------|
| MongoDB | SparkSQL DDL Schema | Obligatorio | Esquema de la colección de mongoDB en formato DDL de SparkSQL. Ejemplo: `COLUMN1 STRING NOT NULL, COLUMN2 INT, COLUMN3 STRUCT<SUBCOLUMN1: INT, SUBCOLUMN2: DOUBLE>, COLUMN4 ARRAY<STRING>`. [Más información](https://spark.apache.org/docs/latest/sql-ref-datatypes.html)|
| Elasticsearch | Retrieve Metadata | Obligatorio | Habilitando esta opción, la utilidad almacenará los metadatos de la tabla |
| Elasticsearch | Use Rich Date Object | Obligatorio | Habilitando esta opción, el proceso transformará los campos de tipo fecha en *RichDateObjects*, en lugar de *String* o *Long* |
| Elasticsearch | Add Elastic Field As Array | Opcional | El campo indicado en está propiedad se tratará como array |
| Elasticsearch | Routing Field | Opcional | Especifica el RoutingField del documento |
| Elasticsearch | Shard Preference  | Opcional | Especifica si se consultan datos en un nodo específico de Elastic |

# Uso de nombres dinámicos de tablas por patrón de fecha
Esta funcionalidad permite el uso de nombres dinámicos de tablas, colecciones o índices usando un patrón de fecha. Se rige por las siguientes reglas:

1. Se habilita dicha funcionalidad incluyendo en el **Physical Name** un patrón de fecha válido encerrado entre #{}.

   Se considera un formato válido aquel aceptado por el formateo de [DateTimeFormatter](https://docs.oracle.com/javase/8/docs/api/java/time/format/DateTimeFormatter.html).
   Ejemplo: **i_uuaa_my_data_#{yyyy_MM}**.
   
   El valor que se infiere en la consulta será el resultado de aplicar sobre el **Physical Name** la sustitución del rango de fechas del periodo formateado al patrón de fecha definido.
   
2. Se ha añadido un tipo **NONE** al **Filter Column Type**. Si Filter Column Type viene informado a NONE, tiene las siguientes implicaciones:
   1. No se añade la clausula WHERE a la consulta SQL. Por tanto se leerá por completo el set de datos de la base de datos de origen.
   2. El atributo FILTER_COLUMN pasa a ser opcional y en caso de informase es ignorado.

3. Validaciones de la utilidad entre los atributos **Physical Name** y **Period Time Unit**:

   1. Si el patrón de fecha introducido es anual, el Period Time Unit podrá ser *YEAR*, *MONTH* o *DAY*.
   2. Si el patrón de fecha introducido es mensual, el Period Time Unit podrá ser *MONTH* o *DAY*.
   3. Si el patrón de fecha introducido es diario, el Period Time Unit sólo podrá ser *DAY*.

# ¿Cómo consultar qué hay en el archivo?

Dependiendo del tipo de consulta que se quiera realizar se dispone de:
- Una sección en la Consola LRBA, denominada Archive Inventory, en la que se muestra un listado de todos los datos almacenados: gestor, base de datos, tabla, período de archivo, fecha de archivación...
- Por otra parte, si se desea consultar los datos historificados, se podrá utilizar la nueva versión del *VisorBTS*, *VisorBTS 2.0* (disponible próximamente), para realizar consultas sobre los datos historificados.

# ¿Cómo se realiza el procesamiento offline de los datos archivados?

En cuanto al procesamiento offline de datos, no existe una utilidad específica para ello, esta se realizará a través de un job de LRBA. 

La lectura de datos desde el archivo de datos se realiza de manera similar a la que se puede realizar con el BTS. Es por ello, que el Source Builder para consultar los datos historificados también se contruye así:

```java
{YOUR_INVENTORY_SERVICE_NAME} = unarchive.{UUAA}.BATCH
{YOUR_PHYSICAL_NAME} = {YOUR_FILE_NAME}.parquet
```

La ruta del objeto historificado (*YOUR_FILE_NAME*), se puede encontrar en la sección de Archive Inventory en los detalles de objeto historificado. La ruta sigue el siguiente esquema: `{GESTOR}/{PHYSICAL_DATABASE}/{PHYSICAL_NAME}/{INIT_PERIOD_DATE}_{END_PERIOD_DATE}.parquet`


En este caso, debido a cómo guarda los datos la utilidad de historificación, el objeto que se lee siempre está en formato parquet. Para más información, se puede consultar la [documentación del conector de Ficheros](https://platform.bbva.com/lra-batch/documentation/9229695829655935d63f723e3b92fb97/arquitectura-lrba/utilidades/spark/conectores/fichero) para jobs LRBA.

# Aspectos a tener en cuenta

* La utilidad de historificación **NO BORRA** los datos en origen, serán los aplicativos los encargados de eliminar los datos mediante las utilidades correspondientes de los gestores de base de datos donde se encuentran sus datos.

* No se permite el borrado de datos en el archivo de datos.

* El valor del campo *Execution Date* puede ser configurado de manera automática o manual para seleccionar el *momento de ejecución*.
  - En el caso de que la configuración sea automática utilizando la macro disponible, el *momento de ejecución* será el marcado por la fecha en la que se está ejecutando la malla de Cronos.
  - Por otro lado, si se utiliza la configuración manual, el *momento de ejecución* de la utilidad será la fecha definida en este campo por el usuario. Este caso es idóneo para ejecuciones fallidas. Para ello, bastaría con rellenarlo con la fecha de ejecución en la que la utilidad falló. 

* El valor seleccionado en Period Time Unit también define la unidad de período de tiempo que consta del número de períodos que se mantienen en Base de Datos, definidos en el valor Periods to Keep in Database. Por tanto, si el valor en Period Time Unit es MONTH, los datos se mantendrán en base de datos X meses, siendo X el valor introducido en Periods to Keep in Database.

* No se permite la archivación de un período que contenga otro (o parte de otro) ya historificado. Para evitar duplicidad en los datos, la utilidad se encarga automáticamente de verificar si el período que se va a archivar ya se encuentra archivado. 

* El valor configurado que se asigna en la unidad de período de tiempo de historificación, deberá ser el mismo elegido en la malla del planificador, es decir, que si se desea historificar utilizando como unidad de período de tiempo el valor *DAY*, el planificador deberá estar configurado para ejecutarse de manera diaria, en el caso de *MONTH* de manera mensual y en el caso de *YEAR* de manera anual. 

* Se permite la utilización de nombres dinámicos de tablas por patrón de fecha y que su período de historificación sea diferente al período que contenga el índice, tabla o colección. Para ello, habría que informar los campos Filter Column Type y Filter Column Name con la información correspondiente al campo de fecha que se quiere utilizar para historificar. 
*Nota: Se deben tener en cuenta las validaciones entre los campos *Physical Name* y *Period Time Unit, descritas anteriormente para su correcta configuración*.*

* Se permite cambiar la unidad de período de tiempo de historificación. Si un aplicativo desea cambiar la manera en la que sus datos se almacenan en el archivo, lo podrá hacer, pero debe tener en cuenta cuándo realiza este cambio, ya que:
  - puede darse el caso en el que intente archivar de nuevo datos que ya se encuentran archivados.
  - o que se deje algún período de datos sin archivar.

