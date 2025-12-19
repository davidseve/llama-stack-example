# bestpractices/01-BestPractices.md
# Buenas prácticas de programación con Spark

## 1. Revisar siempre el plan de ejecución de Spark en la Consola LRBA
Esto es lo más importante que se debe hacer cuando se desarrolla con LRBA.  

LRBA es un runtime de BBVA basado en Spark. **Spark es *lazy***, esto quiere decir, que cuando se aplica alguna lógica a nivel de Dataset, en Spark llamadas [transformaciones](https://spark.apache.org/docs/latest/rdd-programming-guide.html#transformations), Spark va creando un DAG interno con un plan de ejecución. Cuando se realiza una [acción](https://spark.apache.org/docs/latest/rdd-programming-guide.html#actions) (por ejemplo: escribir, un *count*, un *collect*,etc. o cualquiera que obtenga un resultado) se ejecuta todo el DAG calculado.
Si la lógica implementada no está diseñada para Spark, se puede terminar con un DAG muy complejo. 

Los pasos para ver los DAG de los *jobs*, son los siguientes: 
* Ejecutar el *job*.
* Ir a la [Consola LRBA](https://bbva-lrba.appspot.com/) (asegúrese que se ha seleccionado la región y el namespace con UUAA/entorno correctos).
* Hay que ir al menú *Execution History* y buscar la ejecución del *job* que se desea revisar. Entonces hacer clic en la flecha para ir a la página de detalle. 
* En la página de detalle, hay que seleccionar la pestaña *SPARK SQL*.
* Habrá una lista de enlaces a cada *job* del DAG. **Por favor, revisa todos los DAG**. Hay un DAG por cada acción que se ha ejecutado en el *job*.
  
Por ejemplo: el siguiente DAG es una mala práctica debido a que está abriendo el mismo fichero muchas veces, aplicándole diferentes filtros, en lugar de leerlo solo una vez y procesarlo todo junto.

![Add resource](../resources/img/bestPractices/ComplexDag.png)

## 2. Reduce el dataset al inicio
Si el origen es un fichero o una tabla muy grande, con una gran cantidad de información que no es necesario procesar, se debe filtrar antes de realizarle transformaciones o acciones.  
Existen dos formas de reducir el *dataset* y ambas pueden ser aplicadas conjuntamente.
* *Horizontal Reduce*: Seleccionando únicamente las columnas que sean necesarias.
* *Vertical Reduce*: Filtrando únicamente las filas que sean necesarias.

## 3. Descarga los registros de la base de datos a un fichero Parquet en un proceso separado 
Es una buena práctica descargar la información de la base de datos en un fichero Parquet antes de procesarla. Se debe hacer la descarga en un proceso separado.  
En *jobs* complejos, en ocasiones Spark necesita volver a realizar una *task* o *stage* anterior. Si la descarga está situada en otro proceso, se evita consultar varias veces la base de datos.  

## 4. Cachea los *datasets* antes de separar los flujos de ejecución
Si se está leyendo un *dataset* y escribiendo sus filas en varios *targets* en base a alguna condición, se obtiene como resultado final varios DAG diferentes, uno por cada *target*. Como consecuencia se leerá de origen varias veces, una por cada DAG.

### Ejemplo
Código de ejemplo sin caché:
``` java
Dataset<Row> datasetOrigin = datasetsFromRead.get("sourceAlias1");
Dataset<Row> datasetOk = datasetOrigin.filter(dataset.col("INDICADOR").equalTo("0"));
Dataset<Row> datasetError = datasetOrigin.filter(dataset.col("INDICADOR").equalTo("1"));
datasetsToWrite.put("targetFileOk", datasetOk.toDF());
datasetsToWrite.put("targetFileErrors", datasetError.toDF());
```
Si el *dataset* de origen es pequeño se puede [cachear](../utilities/spark/01-Utils.md#caching-datasets) en memoria, de esta forma no se tendrá que leer varias veces el *source*. Seguirá habiendo varios DAG, en este caso el primero coloca los datos en la caché y el resto ya los leerán de ella. 
``` java
Dataset<Row> datasetOrigin = datasetsFromRead.get("sourceAlias1");
DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
Dataset<Row> datasetOriginCached = datasetUtils.cacheDataset(filteredDataset);
Dataset<Row> datasetOk = datasetOriginCached.filter(dataset.col("INDICADOR").equalTo("0"));
Dataset<Row> datasetError = datasetOriginCached.filter(dataset.col("INDICADOR").equalTo("1"));
datasetsToWrite.put("targetFileOk", datasetOk.toDF());
datasetsToWrite.put("targetFileErrors", datasetError.toDF());
```
***NOTA:*** Esta opción esta deprecada desde la version 1.1.0. Tambien puedes consultar el siguiente [enlace](../utilities/spark/01-Utils.md#Datasets-en-caché).

## 5. Broadcast manual de datasets pequeños
Cuando se está haciendo un *join* entre dos *datasets* y uno de ellos es muy pequeño (menos de 10Mb), se puede hacer *broadcast* del *dataset* pequeño a todos los *executors*. Cada *executor* tendrá una copia completa del *dataset*. De esta forma, el *join* con el *dataset* grande será más rápido que haciendo un *join* normal.

Ejemplo:
``` java
Dataset<Row> bigDataset = datasetsFromRead.get("sourceAlias1");
Dataset<Row> smallDataset = datasetsFromRead.get("sourceAlias2");
Dataset<Row> broadcastedSmallDataset = functions.broadcast(smallDataset);
Dataset<Row> joinedDataset = bigDataset.join(broadcastedSmallDataset,bigDataset.col("COL1").equalTo(broadcastedSmallDataset.col("COL1")), "left");
```

## 6. Validación en cascada + union
En muchos casos un batch debe realizar validaciones sobre los campos del *dataset* para detectar filas inválidas y hacer dos ficheros: uno con las filas que son correctas y otro con las que tienen errores.  
Para realizarlo de forma óptima se deben seguir estos pasos:
* Si es necesario prepara el *dataset* para las validaciones(reducciones horizontales/verticales, *joins*, etc).
* Desarrolla una UDF (*Spark User Definition Function*). Pon las validaciones de cada campo en esta función. El resultado de la validación puede ser *true/false* o un código de error.
* Añade una columna al *dataset* en base al resultado de la UDF. Esta se ejecutará por cada fila. El resultado será un nuevo *dataset*, con los datos originales más la nueva columna que indica si la fila es válida o no.
* En este punto se puede considerar cachear el *dataset* resultante.
* Separar el *dataset*. Filtralo usando la nueva columna en *validRowsDataset* y *invalidRowsDataset*.
* Borrar la nueva columna y guarda el resultado de cada *dataset* en su *target*.

En lugar de usar una función UDF, si la lógica a implementar es simple, se puede considerar usar un único filtro con múltiples condiciones *OR*. También se puede usar una función *map* con toda la lógica y crear la columna de validación en ella. Otra opción es una sentencia SQL *select case when* para componer la columna de validación. Hay muchas opciones para prevenir leer el *dataset* varias veces.  

### Ejemplo

No hagas esto (código y plan de ejecución):
``` java
    @Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();

        Dataset<RowData> dataset = datasetsFromRead.get("sourceAlias1").as(Encoders.bean(RowData.class));
        Dataset<RowData> filteredDataset = dataset.filter(dataset.col("CAMPO2").equalTo("000003"));
        datasetsToWrite.put("targetAlias1", filteredDataset.toDF());
        
        Dataset<Row> myDataset = datasetsFromRead.get("sourceAlias1");
        Dataset<Row> datasetErrorsCampo1 = myDataset.filter("CAMPO1!='0182'");
        Dataset<Row> datasetErrorsCampo2 = myDataset.filter("CAMPO2=='000003'");
        Dataset<Row> datasetErrorsCampo3 = myDataset.filter("CAMPO3==''");
        Dataset<Row> datasetAllErrors = datasetErrorsCampo1.union(datasetErrorsCampo2).union(datasetErrorsCampo3);
        
        Dataset<Row> datasetOKs = myDataset.except(datasetAllErrors);

        datasetsToWrite.put("targetAliasOK", datasetOKs);
        datasetsToWrite.put("targetAliasKO", datasetAllErrors);

        return datasetsToWrite;
    }
```
El mismo *source* ha sido leído 4 veces y el DAG resultante es complejo:

![Add resource](../resources/img/bestPractices/FilterPlusUnion.png)

En su lugar, valida las tres columnas (CAMPO1, CAMPO2, CAMPO3) del *dataset* usando una función UDF3 y genera una nueva columna (CAMPO4) con el resultado de la validación:  
``` java
    @Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();

        Dataset<Row> myDataset = datasetsFromRead.get("sourceAlias1");
        Dataset<Row> datasetValidated = myDataset.withColumn(
            "CAMPO4", 
            functions.udf(
                myUDF(),
                DataTypes.StringType
            ).apply(myDataset.col("CAMPO1"), myDataset.col("CAMPO2"), myDataset.col("CAMPO3")));
        
        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> datasetValidatedCached = datasetUtils.cacheDataset(datasetValidated);

        datasetsToWrite.put("targetAliasOK", datasetValidatedCached.filter("CAMPO4=='OK'").drop("CAMPO4"));
        datasetsToWrite.put("targetAliasKO", datasetValidatedCached.filter("CAMPO4!='OK'").drop("CAMPO4"));

        return datasetsToWrite;
    }

    private UDF3<String, String, String, String> myUDF() {
        return (campo1, campo2, campo3) -> {
            String value = "OK";
            if (!"0182".equals(campo1)) value = "ERROR_CAMPO1";
            else if ("000003".equals(campo2)) value = "ERROR_CAMPO2";
            else if ("".equals(campo3)) value = "ERROR_CAMPO3";
            else value = "OK";

            return value;
        };
    }
```
Ahora, el *source* ha sido leído una sola vez.

![Add resource](../resources/img/bestPractices/UDF.png)

## 7. Orden de los joins
Cuando se realiza un *join* de *dataset*, siempre se debe colocar el *dataset* más grande en el lado izquierdo del *join*.
``` java
bigDataset.join(smallDataset);
```

## 8. Comprueba si hay executors muertos
Verifica si los *executors* del proceso han muerto. Ve a la [Consola LRBA](https://bbva-lrba.appspot.com/), al menú *Execution History*, entra en la ejecución que desea revisar y selecciona la pestaña *SPARK EXECUTOR*:
![Add resource](../resources/img/bestPractices/DeadExecutors.png)
Si el *job* LRBA ha terminado correctamente, pero tiene *executors* muertos, probablemente se esté quedando sin memoria en algún momento. Por favor, revisa el DAG, considera simplificarlo y optimizarlo con la ayuda de OCTA. Como último paso, realiza una [solicitud](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/611) para un aumento de recursos.

## 9. No reutilices jobs
Los procesos no deben reutilizarse para múltiples propósitos (realizar operaciones completamente diferentes en función de los parámetros de entrada). Este tipo de procesos son difíciles de mantener y operar.

Por ejemplo, es correcto utilizar el mismo proceso para realizar una carga inicial y sus cargas incrementales. Ambas cargas deberían realizar las mismas operaciones, pero con diferentes volumetrías y posiblemente diferentes filtros en el source (descarga total o filtrada por timestamp). Pero el *source*, la lógica y el *target* son los mismos.

Sin embargo, no se debe utilizar el mismo proceso, por ejemplo, para leer/escribir en diferentes *sources/targets* o realizar diferentes operaciones. En este caso, si necesita un aumento de recursos en la talla de su *job* LRBA, como el proceso se utiliza para múltiples propósitos, su solicitud será denegada.

## 10. Reparticionar antes de cruces, agrupaciones, agregaciones, ordenaciones...
Para las operaciones que necesitan mezclar datos (cruces, agrupaciones, agregaciones, ordenaciones), Spark necesita que los datos estén repartidos en particiones pequeñas, para poder realizar el trabajo de forma eficiente (estrategía divide y venceras!).

Spark automáticamente realiza un reparticionado de los *Dataset* que intervienen en la operación, sin embargo no siempre acierta en el número de particiones:
* Si el número de particiones es muy bajo, al trabajar con ellas, podrían no caber en memoria y darse situaciones de *OutOfMemory*.
* Si el número de particiones es muy alto, el número de tareas es muy grande y el tiempo podría verse incrementado por la sobrecarga de gestión de tareas.

Por tanto, es recomendable indicarle a Spark cómo debe de hacer el particionado con la siguiente instrucción `dataset.repartition( num_partitions,repartitionColumn)`:
* Debe de realizarse sobre todos los dataset que conforman la operación.
* La columna de reparticionado debe de ser la misma que se use en la operación.
* La cantidad de operaciones dependerá del tamaño del dataset.


# patterns/pattern-extract.md
# Descarga de información de bases de datos relacionales a BTS

Una base de datos relacional es un conjunto de información que se organiza en tablas de columnas y filas (registros). Se llama relacional, precisamente, porque los datos se ordenan en relaciones predefinidas. Un sistema de software utilizado para mantener bases de datos relacionales es un *RDBMS (Relational Database Management System)*.

*BTS (Bucket Temporary Storage)* es un servicio de **almacenamiento de objetos** que permite almacenar datos como objetos (ficheros) dentro de *buckets* utilizando *Scality S3* como persistencia.

Este patrón responde a algunos casos de uso comunes:

- Descargas completas o incrementales de datos desde bases de datos relacionales (por ejemplo: Oracle o DB2) para insertarlos en otras bases de datos relacionales (por ejemplo: Oracle) o NoSQL (por ejemplo: MongoDB o ElasticSearch).

- Descargas completas o incrementales de datos desde bases de datos relacionales (por ejemplo: Oracle o DB2) para procesar cálculos por lotes más complejos (por ejemplo: cálculos de precios, liquidaciones, conciliaciones, etc.).


## Base de datos relacionales

En este patrón es habitual indicar como parámetro de entrada si se realiza una descarga **completa** o **incremental** (descarga de registros que han sido modificados recientemente - por ejemplo: registros actualizados en base de datos en las últimas 24 horas). Para controlar la fecha a partir de la cual deben descargarse los registros incrementales, puede implementarse un mecanismo basado en un fichero o tabla de control que se actualice con la nueva fecha, ya que las descargas se ejecutan diariamente.

Es posible utilizar el *Source Builder* de diferentes formas. El más utilizado podría ser ***JdbcDatabaseNativeQuery***, que permite establecer SQL específicos en el *RDBMS* utilizando artefactos sintácticos más complejos (como *joins*).

Para el resto de los casos se puede utilizar ***JdbcPartitioned***. En este caso la sintaxis SQL a ejecutar debe ser compatible con *SparkSQL* ([ANSI Compliance](https://spark.apache.org/docs/latest/sql-ref-ansi-compliance.html)). Este constructor permite ejecutar extracciones paralelizadas contra el *RDBMS*, no siendo recomendable utilizar un nivel de paralelismo agresivo para preservar los recursos computacionales del *RDBMS* fuente. 

En este punto es importante aclarar que la parte principal del proceso se ejecuta en memoria, los filtros o predicados (la parte *WHERE* del SQL) suelen ser resueltos por la propia base de datos relacional mediante pushdown de filtros. Cuando los operadores *WHERE* se ejecutan justo después de cargar un conjunto de datos, *SparkSQL* intentará empujar el predicado *WHERE* a la fuente de datos usando una consulta SQL correspondiente (o cualquier lenguaje apropiado para la fuente de datos). 

Esta optimización se llama ***filter pushdown*** o ***predicate pushdown*** y está pensada para enviar el filtrado a la base de datos. El objetivo es aumentar el rendimiento de la consulta, ya que el filtrado se realiza a un nivel muy bajo en lugar de tratar con todo el conjunto de datos después de que se haya cargado en la memoria de Spark, lo que podría causar problemas de memoria. 

Esta optimización es especialmente beneficiosa en el caso de descargas incrementales (recuperación de registros actualizados recientemente). En este caso, en lugar de solicitar al *RDBMS* la descarga completa y el filtrado en memoria de Spark, la resolución SQL se delega en el propio *RDBMS*.


## Parquet

Las descargas se realizan en ficheros con estructura *Apache Parquet* con persistencia en el almacenamiento de objetos *BTS*. *Apache Parquet* es un formato de almacenamiento en columnas disponible para cualquier proyecto, independientemente de la elección del marco de procesamiento de datos, modelo de datos o lenguaje de programación.

Estos archivos estructurados pueden ser accedidos por procesos posteriores con el metalenguaje *SparkSQL* y los datos pueden ser accedidos por nombres de columna como otra persistencia relacional.

**NOTA:** El uso de estos ficheros es **temporal** con la intención de ser utilizados en un proceso LRBA posterior dentro de un contexto de ejecución más amplio pero siempre limitado a la ejecución por lotes del día. 


## Ejemplos

* [Ejemplos JDBC](../utilities/spark/connectors/02-JDBC.md)

* [Ejemplos BTS](../utilities/spark/connectors/01-File.md)


# patterns/pattern-join.md
# Joins de Datasets en memoria y conversión a objeto Java

Este patrón es adecuado para los siguientes casos de uso:

1.- Proceso que combina (***join***) dos *Datasets* en formato Parquet mediante igualdad de claves únicas. El resultado se almacena en una base de datos relacional o NoSQL.

2.- Proceso que combina (***join***) dos *Datasets* en formato Parquet mediante igualdad de claves únicas. El resultado se utiliza para realizar **cálculos** en un *Map* de Spark(Ejemplo: El *Dataset* de contratos se cruza con el *Dataset* de saldos y movimientos para ver el gasto medio por contrato.)
 - Los datos de origen han sido descargados a formato Parquet en BTS.
 - El resultado será generado en un fichero Parquet intermedio dentro de BTS, ya que puede ser consumido por otros procesos que a su vez realicen cálculos en base a la información generada.


La lógica de estas transformaciones se dividen en dos fases:

1. *Join* de ambos *Datasets* igualando la clave única.
<BR>

``` java        
Dataset<TDBC> ds_TDBC = dsInputTable.get("TDBC").as(Encoders.bean(TDBC.class)).alias("TDBC");
Dataset<TLRA> ds_TLRA = dsInputTable.get("TLRA").as(Encoders.bean(TLRA.class)).alias("TLRA");

// INNER JOIN two tables by pk columns
Dataset<TJOINED> ds_joined = ds_TDBC
    .join(
        ds_TLRA,
        JavaConversions.asScalaBuffer(Arrays.asList("COD_CCLIEN", "COD_BANCSB", "COD_PAIS")).seq(), 
        "inner"
    )
    .select(
        "TDBC.COD_CCLIEN", "TDBC.COD_BANCSB", "TDBC.COD_PAIS",
        "TDBC.XTI_TIPERSO", "TDBC.FEC_FALTAF", "TDBC.FEC_FMODIFIC", "TDBC.XTI_CTIPCL1", "TDBC.COD_DOCUM25",
        "TLRA.XTI_CTIPCL2", "TLRA.XTI_XFODNI", "TLRA.XSN_FOTOC", "TLRA.COD_CDNOMB", "TLRA.DES_DENOMB", "TLRA.XTI_CDOMIC"
    )
    .as(Encoders.bean(TJOINED.class));
```
2. El proceso de cálculo requiere de cada uno de los registros obtenidos en el paso anterior.

``` java
Dataset<TNEWMODEL> datasetOutput = ds_joined.map((MapFunction<TJOINED, TNEWMODEL>) joinedRow -> {
    TNEWMODEL newModel = new TNEWMODEL();
    newModel.setCOD_BANCSB(joinedRow.getCOD_BANCSB());
    newModel.setCOD_CCLIEN(joinedRow.getCOD_CCLIEN());
    newModel.setCOD_PAIS(joinedRow.getCOD_PAIS());

    String personType = joinedRow.getXTI_TIPERSO();
    
    Integer calculated = 0;
    switch (personType) {
        case "J": calculated = joinedRow.getCOD_CDNOMB() * 5; break;
        case "F": calculated = joinedRow.getCOD_CDNOMB() * 2; break;
        default: calculated = 50; break;
    }

    newModel.setXTI_TIPERSO(personType);
    newModel.setCALCULATED(calculated);
    newModel.setNOW(new Date(System.currentTimeMillis()));

    return newModel;

}, Encoders.bean(TNEWMODEL.class));
```

Se pueden utilizar [Java beans](https://en.wikipedia.org/wiki/JavaBeans) como entidades para almacenar los datos, en lugar de usar *Row.class*.


# commonoperations/01-CreateCredentials.md
# Crear Credenciales

Esta sección explica como pedir credenciales según la base de datos correspondiente.

## Bases de datos NextGen (Oracle, MongoDB y Elasticsearch)

* **Oracle:** Cuando una UUAA es registrada, el equipo IaaS Data SQL solicita las credenciales necesarias a Data Enterprise Security.

* **MongoDB and ElasticSearch:** Cuando la UUAA solicita la creación de una nueva base de datos, el equipo IaaS Data NoSQL solicita que se den de alta las credenciales a Data Enterprise Security.

Si hay algún problema con las credenciales, abrir una incidencia Helix a Data Enterprise Security.


Si se necesitan solicitar credenciales:

1. Abrir un [Helix](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/427) indicando:

* UUAA
* Deployment country [Spain, Global, Mexico]
* Database manager [Oracle, MongoDB, Elasticsearch]
* Database [BMAPX001, BMG_UUAA_CO_SUFFIX, BEL_UUAA]
* Environment [dev, int, oct, aus y pro]
* Runtime: LRBA

## DB2 

### España/Global

1. Solicitar las credenciales DB2 siguiendo esta [guía](https://docs.google.com/document/d/1e3cep0a7Q2dDrLfHNP81-f9tNRr6HMYMjdWUdROLssw/edit). 

2. Una vez se tienen los usuarios y contraseñas por cada entorno, que debe ser diferente, se debe incluir en un [passenger](https://passenger-meigas.live.es.nextgen.igrupobbva/msg) de un solo uso.

3. Abrir un [Helix](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/427) indicando:

* UUAA
* País de Despliegue [Spain, Global]
* Gestor de base de datos: DB2
* Entorno [dev, int, oct, aus y pro]
* Runtime: LRBA

4. Enviar el enlace de passenger y el Helix al buzón **Data Enterprise Security - Credentials**.

**IMPORTANTE: Esta sección puede cambiar a futuro.**

### LATAM

1. Solicitar las credenciales DB2 siguiendo los pasos de la [guía](https://docs.google.com/document/d/1FpYCRbC1w0XO59O4dTtX5FX8iKTFXiJMmC-BRWPVpHQ/edit#heading=h.n5r7l140puer). 

2. Una vez se tienen los usuarios y contraseñas por cada entorno, que debe ser diferente, se debe incluir en un [passenger](https://passenger-meigas.live.es.nextgen.igrupobbva/msg) de un solo uso.

3. Abrir un [Helix](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/427) indicando:

* UUAA
* País de Despliegue [Mexico]
* Gestor de base de datos: DB2
* Entorno [dev, int, oct, aus y pro]
* Runtime: LRBA

4. Enviar el enlace de passenger y el Helix al buzón **Data Enterprise Security - Credentials**


## Servicios Externos

Para todos los servicios externos a los que se quiera tener acceso, se tiene que crear un remedy **ALTA CREDENCIALES EN APX/LRBA NO BBDD**

1. Elegir el Entorno.

![Alta credenciales 1](../resources/img/AltaCredenciales1.png)

2. Elegir la UUAA y Console (España, Global).

![Alta credenciales 2](../resources/img/AltaCredenciales2.png)

3. Definir alias, username, password y elegir el runtime **LRBA**. **IMPORTANTE**: El alias tiene que ser el mismo que el especificado en el campo *File Name* cuando se aprovisiona el servicio externo.

![Alta credenciales 3](../resources/img/AltaCredenciales3.png)

Estas credenciales son manejadas por el equipo de RA.

## Solicitar certificados para Http Mutual TLS

Para solicitar un certificado para HTTP Mutual TLS hay que seguir los siguientes pasos:

1. **Solicita el certificado**. Dirígete a [WebRA Work](https://pkiglobal-ra.work.es.nextgen.igrupobbva/#/home) o [WebRA Live](https://pkiglobal-ra.live.es.nextgen.igrupobbva/#/home), dependiendo del entorno deseado, para solicitar el certificado. Utiliza esta [guía](https://platform.bbva.com/security-architecture/documentation/1uaeEoqiJW10SI7fdXujKkxrcT4UBjE5RhbrVY98E5QU/cryptography/certificates/webra#h.8kqp2h5lj23h) para ello.

2. **Aprovisiona el certificado en Vault**.
  
   a. Aprovisiona el certificado para LRBA con la ayuda de esta [guía](https://platform.bbva.com/security-architecture/documentation/1uaeEoqiJW10SI7fdXujKkxrcT4UBjE5RhbrVY98E5QU/cryptography/certificates/webra#h.3u3y154telvw) (Sección: Aprovisionamiento de Certificados). En el campo donde se tiene que seleccionar el producto o la disciplina, añade manualmente el valor `lrba`.

   **IMPORTANTE**: Completa el campo *File Name* con el formato `{uuaa}.{alias}.p12`. El alias es un campo libre que indica el nombre con el que se identificará al certificado en el job LRBA. [Más información](../utilities/spark/connectors/05-HTTP.md#mutual-tls-mtls)  

   b. El certificado se queda pendiente de aprobación. Para que lo aprueben, abre un ticket en [Helix](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/checkout) al siguiente grupo de soporte indicando las acciones a realizar:

   > **BU**: ARQUITECTURA **L1**: SECURITY - CRYPTOGRAPHY - EUROPA **L2**: VAULT RUNTIME - EUROPA

   c. Una vez abierto el ticket, escribe al mail [pki-crypto.global.sec-architecture.group@bbva.com](pki-crypto.global.sec-architecture.group@bbva.com) indicando que habéis abierto la solicitud Helix, añadiendo a [lrba.europe.group@bbva.com](lrba.europe.group@bbva.com) en copia. 


3. **Registra la contraseña del certificado en el Vault**. 
  
   a. Comprueba la contraseña del certificado. Este [documento](https://platform.bbva.com/security-architecture/documentation/1uaeEoqiJW10SI7fdXujKkxrcT4UBjE5RhbrVY98E5QU/cryptography/certificates/webra#h.qs7w7urfmcut) te puede servir de guía.
   
   b. Registra la contraseña del certificado en el Vault para que se den de alta las credenciales del certificado y que la arquitectura pueda acceder al mismo en runtime. Ve a la sección [*Servicios Externos*](#servicios-externos) de esta misma página para ver como hacerlo. 

   **IMPORTANTE**: Es obligatorio que el alias usado en el *Servicio Externo* sea el mismo valor especificado en el campo *File Name*, descrito en el punto anterior, cuando se aprovisiona el certificado.

**NOTA:** La clave del bot usada en [Mutual TLS builder](../utilities/spark/connectors/05-HTTP.md) debe ser **EXACTAMENTE** el alias especificado en los pasos anteriores.

## Equipos

* **Data Enterprise Security:** Responsables del manejo de las credenciales del Vault y del Portal Web (data.enterprise.security.credentials.group@bbva.com).
* **IaaS Data SQL:** Responsables del manejo de las bases de datos Oracle (iaas.datasql.es@bbva.com).
* **IaaS Data NoSQL:** Responsables del manejo de las bases de datos no relacionales MongoDB and ElasticSearch (iaas.nosql.data.es@bbva.com).
* **RA:** Junto con Data Enterprise Security, son los responsables del manejo de credenciales(contactar via Remedy ALTA CREDENCIALES EN APX/LRBA NO BBDD).
* **Cryptography:** Responsables de la infraestructura del Vault (pki-crypto.global.sec-architecture.group@bbva.com).

**NOTA:** Por favor, contacte a los diferentes grupos via Service Desk cuando sea necesario. [Support info](../Support.md)


## LRBA América

En el caso de América, puedes consultar la guía de [LRBA América](https://docs.google.com/document/d/1FpYCRbC1w0XO59O4dTtX5FX8iKTFXiJMmC-BRWPVpHQ/edit#), donde podrás obtener más detalles acerca de las actividades que se deben hacer para disponer de todo lo necesario para ejecutar procesos en LRBA.

Previo a procesos de liberación de componentes, es recomendable validar que en la ventana de instalación no estén considerados o programados procesos de actualización / mantenimiento a tablas de DB, 
estos procesos se describen en el documento [Stand in](https://docs.google.com/document/d/15GvPOYIKPBR65a0ZA5TQUohlGj7rF2kBA7Qti-IsGrg/edit#heading=h.4d34og8)


# utilities/01-LRBAProperties.md
# Propiedades LRBA

La utilidad `LRBAProperties` permite recuperar las configuraciones de despliegue dentro de los *jobs*.
Por ejemplo, un fichero procesado por un *job* puede llamarse *users-dev.csv* en el entorno DEV y *users-pro.csv* en el entorno PRO.


## Métodos

|                   Method                    |                                        Behaviour                                         |
|:-------------------------------------------:|:----------------------------------------------------------------------------------------:|
|               get(String key)               |       Recupera la variable indicada, si esta no exite la utilidad devuelve `null`.       |
| getDefault(String key, String defaultValue) | Recupera la variable indicada, si esta no existe devuelve el valor por defecto indicado. |
|           getOrThrow(String key)            | Recupera la variable indicada, si no existe lanza una excepción de tipo `LrbaException`. |

## Usando la utilidad en un job

Las diferentes configuraciones de despliegue pueden ser recuperadas mediante la clase `LRBAProperties`:

```java
@Builder
public class JobDemoLRBA extends RegisterSparkBuilder {

    private LRBAProperties lrbaProperties;
    
    public JobDemoLRBA() {
        lrbaProperties = new LRBAProperties();
    }
    
    public void setLrbaProperties(LRBAProperties lrbaProperties) {
        this.lrbaProperties = lrbaProperties;
    }
    
    @Override
    public SourcesList registerSources() {
        final String fileName = lrbaProperties.getDefault("SOURCE_FILE_NAME", "file-default-name.csv");

        // ...
    }

// ...

}
```
Los valores por defecto pueden resultar muy útiles en las pruebas sobre entorno local, ya que permiten ejecutar sin tener que dar de alta las diferentes propiedades en el entorno.

## Propiedades LRBA en Test Unitarios

Para simular el comportamiento de la clase `LRBAProperties`, hay que hacer uso de Mockito de la siguiente manera:

```java
class JobDemoLRBATest {

    private JobDemoLRBA jobDemoLRBA;
    
    private LRBAProperties lrbaProperties;
    
    @BeforeEach
    void setUp() {
        jobDemoLRBA = new JobDemoLRBA();
        
        lrbaProperties = Mockito.mock(LRBAProperties.class);
        jobDemoLRBA.setLrbaProperties(lrbaProperties);
    }
    
    @Test
    void registerSources_LRBAPropertiesSet_SourceDataBuiltProperly() {
        Mockito.when(this.lrbaProperties.getDefault("SOURCE_FILE_NAME", "file-default-name.csv")).thenReturn("file-test.csv");
        
        // continue test...
    }

}
```

*NOTA*: El ejemplo anterior que hace uso de la clase `LRBAProperties` está simpificado para únicamente mostrar esa parte del código.
Para crear unos tests consistentes hay que añadir más validaciones de tipo `Assertion.assert...`

## Declarar las configuraciones en la consola Ether.

Accede a la Consola Ether, a continuación haz click en el icono indicado.

![LRBA Properties icons](../resources/img/OpenPropertiesVariable.png)

Selecciona el entorno deseado y entra en la pestala *DEPLOYMENT CONFIGURATIONS*:

![Deployment Configuration](../resources/img/OpenDeploymentConfigurations.png)

Haz click en *ADD DEPLOYMENT CONFIG*, rellena el nombre y la descripción. El campo *Kind* debe tener el valor *lra.batch*.
Añade los parámetros necesarios en formato JSON y ya estaría, haz click *SAVE*.

![Deployment Configuration](../resources/img/CreateDeploymentConfig.png)

Una vez se han creado las configuraciones de despliegue es necesario asociarlas al *job*.
Accede al proceso que necesita las configuraciones y haz click en *deploy* seleccionando el mismo entorno que en la creación de la configuración.
Se abrirá una ventana, haz click en *DEPLOYMENT CONFIG PARAMS* y selecciona la configuración de despliegue creada. Por último haz click en *DEPLOY*.


![Select deployment configuration](../resources/img/SelectDeploymentConfig.png)

## Usar Propiedades LRBA en entorno local.

En el entorno local es posible declarar configuraciones de despliegue como variables de entorno antes de ejecutar el *job*.

Al tratarse de variables de entorno, la manera de darlas de alta depende de cada Sistema Operativo. La manera más sencilla es haciendo uso del `LRBA CLI` para ejecutar los *jobs*.

### LRBA CLI (Opción recomendada)
Hay un fichero JSON llamado `deploymentConfig.json`, está en la carpeta `local-execution` de nuestro proyecto. Las propiedades que se indiquen aquí estarán disponibles desde LRBAProperties en entorno local.
```json
{
  "SOURCE_FILE_NAME": "file-test.csv",
  "TARGET_FILE_NAME": "file-test.out.csv"
}
```
Dentro de esta misma carpeta se incluye el fichero `deploymentConfig.properties.required`, donde se puede configurar que propiedades son obligatorias para la correcta ejecución del *job* en entorno local. Cada propiedad debe ir especificada en una nueva línea.

```properties
SOURCE_FILE_NAME
TARGET_FILE_NAME
```

Si una propiedad se encuentra en el fichero `deploymentConfig.properties.required` pero no está declarada en el fichero `deploymentConfig.json`, se producirá un error de ejecución.

### Windows 10
El comando depende de si se usa `CMD` o `Power Shell`.
- CMD: `set SOURCE_FILE_NAME=users-dev.csv`
- Powershell: `$env:SOURCE_FILE_NAME = 'users-dev.csv'`

### MacOS
`export SOURCE_FILE_NAME=users-dev.csv`

### Linux
`export SOURCE_FILE_NAME=users-dev.csv`


# utilities/02-LRBAInputParameters.md
# Parámetros de entrada LRBA 

Los *jobs* de LRBA pueden recibir parámetros de entrada y estos pueden cambiar en cada ejecución.

En el caso de los parámetros de configuración, consultar el apartado de [Propiedades LRBA](./01-LRBAProperties.md).

## Uso de los parámetros de entrada

El desarrollador puede recuperar los parámetros de entrada utilizando la clase `InputParams`:

```java
@Override
public SourcesList registerSources() {
    final String executionInterval = InputParams.get("EXECUTION_INTERVAL");
    if (executionInterval == null) {
        throw new RuntimeException("Execution Interval mustn't be null");
    }
    
    // Initialize Job source...
}
```

## Test de los parámetros de entrada

Los parámetros de entrada se proveen en tiempo de ejecución. Se puede utilizar el método `InputParams.initialize(Map<String, String> inputParams)` para poder hacer un *mock*.

```java
@Test
void registerSources_InputParameters_NoException() {
    InputParams.initialize(Collections.singletonMap("EXECUTION_INTERVAL", "DAILY"));
    assertDoesNotThrow(() -> this.jobLRBADemo.registerSources());
}
```

En caso de que los parámetros no estén correctamente configurados, se puede probar fácilmente el comportamiento:

```java
@Test
void registerSources_InputParametersNotSet_ExceptionThrown() {
    InputParams.initialize(Collections.emptyMap());
    assertThrows(RuntimeException.class, () -> this.jobLRBADemo.registerSources());
}
```
**NOTA**: El *test* anterior se ha simplificado para mostrar como utilizar la clase `InputParams`.
Se deben realizar más validaciones para hacer una prueba robusta.

## Especificación de parámetros de entrada en el planificador

Dependiendo del planificador, los parámetros de entrada deberán añadirse de diferentes maneras.

### Cronos

Si se utiliza [Cronos](https://platform.bbva.com/en-us/developers/cronos/documentation/what-is), se usarán de la siguiente manera:

![Cronos input parameters](../resources/img/CronosInputParameters.png)

### Control-M

Si se utiliza [Control-M](https://platform.bbva.com/en-us/developers/orchestration/documentation/control-m/what-is-control-m), hay que seleccionar la plantilla *PLANTILLA_LRABatch*.

La variable `%%inputparameters` debe ser un JSON que contenga los parámetros como clave-valor. Por ejemplo `[{"key": "EXECUTION_INTERVAL", "value": "DAILY"}]`.


## Parámetros de entrada en el entorno local.

Para establecer los parámetros de entrada en el entorno local, se debe declarar una variable de entorno antes de ejecutar el *job*.
Por lo tanto, la forma en la que deben declararse depende del sistema operativo. Sin embargo, si se utiliza el LRBA CLI para ejecutar el *job*, se pueden declarar fácilmente.

### LRBA CLI (recomendado)

Existe un fichero JSON `inputParameters.json` en la carpeta `local-execution` del proyecto del *job* donde se pueden colocar los parámetros de la siguiente manera:

```json
{
  "INTERVALO_EJECUCIÓN": "DAILY",
  "INTERVALO_EJECUCION_CONCILIACION": "WEEKLY"
}
```

Además, en esa carpeta, hay un fichero `inputParameters.properties.required` donde se pueden declarar los parámetros de entrada obligatorios. Cada parámetro obligatorio debe ser declarado en una nueva línea:

```propiedades
INTERVALO_EJECUCIÓN
INTERVALO_EJECUCIÓN_CONCILIACIÓN
```
Si un parámetro de entrada se establece en el fichero `inputParameters.properties.required` pero no en el fichero `inputParameters.json`, se produce un error antes de ejecutar el *job*.

### Windows 10
El uso de un comando u otro depende de si se está utilizando *CMD* o *Powershell*:
- CMD: `set JSON_PARAMS='{"EXECUTION_INTERVAL": "DAILY"}'`
- Powershell: `$env:JSON_PARAMS = '{"EXECUTION_INTERVAL": "DAILY"}'`

### MacOS
`export JSON_PARAMS='{"EXECUTION_INTERVAL": "DAILY"}'`

### Linux
`export JSON_PARAMS='{"EXECUTION_INTERVAL": "DAILY"}'`


# utilities/03-LRBAApplicationContext.md
# Contexto de aplicación de LRBA 

Los *jobs* de LRBA pueden utilizar la clase *ApplicationContext*. 

Esta clase, permite almacenar información en cualquier paso y recuperarla en pasos posteriores.

## Utilizando ApplicationContext

```java
import com.bbva.lrba.context.ApplicationContext;

public class ExampleClass {

	public ExampleClass() {
		// Store information
		ApplicationContext.put("key", "value");

		// Retrieve information
		String value = ApplicationContext.get("key");
	}
}
```


# utilities/04-LRBADependencies.md
# Dependencias LRBA

La arquitectura LRBA permite dos tipos de dependencias:

- Las **dependencias incluidas**, que son dependencias que se incluyen por defecto en la arquitectura y se pueden
  utilizar directamente. No es necesario incluirlas en el pom.
- Las **dependencias externas** son dependencias revisadas por la arquitectura y que la aplicación tiene permitido
  incluirlas en su pom. Cualquier dependencia que se incluya en el pom y no pertenezca a las dependencias externas
  permitidas hará que Sonar falle.

## Dependencias incluidas

### Ejecución

|       groupId        |     artifactId      | versión | Incluída en versión de arquitectura |
|:--------------------:|:-------------------:|:-------:|:-----------------------------------:|
|      org.slf4j       |      slf4j-api      | 1.7.36  |                0.0.0                |
| com.google.code.gson |        gson         |  2.9.1  |                0.0.0                |
|   org.apache.spark   |   spark-sql_2.12    |  3.5.6  |                3.0.0                |
|   org.apache.spark   |   spark-core_2.12   |  3.5.6  |                3.0.0                |
|   org.apache.spark   | spark-catalyst_2.12 |  3.5.6  |                3.0.0                |
|    org.scala-lang    |    scala-library    | 2.12.18 |                3.0.0                |
|    org.scala-lang    |    scala-reflect    | 2.12.18 |                3.0.0                |
|     org.mongodb      |        bson         |  5.1.4  |                2.1.0                |
|  org.apache.commons  |    commons-lang3    | 3.17.0  |                2.1.2                |
|  org.apache.commons  |    commons-text     | 1.13.0  |                2.1.2                |

### Test

|      groupId      |      artifactId      | versión | Incluída en versión arquitectura |
|:-----------------:|:--------------------:|:-------:|:--------------------------------:|
| org.junit.jupiter |  junit-jupiter-api   |  5.8.2  |              0.0.0               |
| org.junit.jupiter | junit-jupiter-engine |  5.8.2  |              0.0.0               |
| org.junit.jupiter | junit-jupiter-params |  5.8.2  |              2.1.4               |
|    org.mockito    |     mockito-core     |  4.6.1  |              0.0.0               |
|    org.mockito    |    mockito-inline    |  4.6.1  |              0.3.0               |
| uk.org.webcompere |  system-stubs-core   |  2.0.1  |              0.6.0               |
| uk.org.webcompere | system-stubs-jupiter |  2.0.1  |              0.6.0               |

## Dependencias externas LRBA

El uso de dependencias externas no está permitido en los *jobs* de LRBA. Dentro del pom.xml, sólo se permiten
dependencias con groupId `com.bbva.lrba.external-modules`, que son:

| **Dependencia** | **groupId original**      | **artifact**       | **Versión dependencia** | **Incluída en versión arquitectura** |
|-----------------|---------------------------|--------------------|-------------------------|--------------------------------------|
| xstream         | com.thoughtworks.xstream  | xstream            | 1.4.20                  | 0.7.0                                |
| crypto          | com.bbva.secarq.chameleon | chameleon-sdk-core | 2.62.1                  | 2.2.0                                |
| apachePOI       | org.apache.poi            | poi                | 5.2.3                   | 2.0.0                                |

### Como utilizarlo

``` xml 
<dependency>
    <groupId>com.bbva.lrba.external-modules</groupId>
    <artifactId>{{DEPENDENCY_NAME}}</artifactId>
</dependency>
```

#### Xstream

Para incluir la dependencia *xstream* se debe hacer de la siguiente forma:

``` xml 
<dependency>
    <groupId>com.bbva.lrba.external-modules</groupId>
    <artifactId>xstream</artifactId>
</dependency>
```

#### Crypto

Para incluir la dependencia *crypto* se debe hacer de la siguiente forma:

``` xml 
<dependency>
    <groupId>com.bbva.lrba.external-modules</groupId>
    <artifactId>crypto</artifactId>
</dependency>
```

Para inicializar *CryptoWrapper* con el fin de utilizar los métodos proporcionados por su SDK:

``` java
CryptoWrapper crypto = new CryptoWrapper({BUNDLE_ID}, {NAMESPACE});
ChameleonExtendedSDKClient client = crypto.getChameleonSDKClient();
```

Para más detalles sobre las operaciones del SDK,
revisar: [Documentación SDK Chameleon](https://platform.bbva.com/securityservices-cypher/documentation/1tbkdrTP0DaOY0gGp_7DfxxTjwo3yHRnsfc3gTcgpIOI/cypher-data-masking/execution-parameters)

#### ApachePOI

Para incluir la dependencia *apachePOI* se debe hacer de la siguiente forma:

``` xml 
<dependency>
    <groupId>com.bbva.lrba.external-modules</groupId>
    <artifactId>apachePOI</artifactId>
</dependency>
```


# utilities/05-LRBAApplicationExitCode.md
# Estados y códigos de retorno en LRBA

Los *jobs* de LRBA especifican un código de retorno funcional según el estado en el que se encuentren. Los códigos de errores válidos en LRBA se encuentran entre el 0 y el 255, quedando reservados para LRBA los comprendidos entre el 128 y el 255.

A continuación se muestran cuales son los Estados y Códigos de Retorno por defecto correspondientes a los jobs de LRBA.

|     Estado     |                 Código de Retorno                  | Motivo del Estado                                                               |
|:--------------:|:--------------------------------------------------:|:--------------------------------------------------------------------------------|
|   Launching    |                        N/A                         | El job está pendiente de obtener recursos en el cluster para empezar a ejecutar |
|    Running     |                        N/A                         | El job se está ejecutando                                                       |
|    Success     | 0 (por defecto, se puede modificar funcionalmente) | La ejecución del job finaliza correctamente                                     |
|    Unknown     |                        157                         | El job finaliza porque el driver ha muerto                                      |
|     Locked     |                        251                         | El job se encuentra bloqueado / en cuarentena                                   |
|      Dead      |                        252                         | El job se muere porque su ejecución ha sobrepasado las 24 horas                 |
|  Forced Stop   |                        253                         | Se ha parado manualmente el job                                                 |
| Launcher Error |                        254                         | Error en el launcher, por validacion de params u otros errores técnicos         |
|     Failed     |                        255                         | La ejecución del job ha finalizado debido a un error aplicativo                 |



## Modificación del código de retorno funcional 

Solo está permitido el uso de códigos **que se encuentren entre 0 y 127**. En el caso de no establecer ningún
valor, se retornará el valor por defecto asociado al estado final del job.

Es posible aplicar esta funcionalidad de dos formas distintas dependiendo de las necesidades del *job*:

- Retornando un valor cuando el job finaliza y su estado final es *Success*.
- Forzando el estado final *Failed*, interrumpiendo la ejecución y
devolviendo el valor deseado en ese momento.

Se muestran ejemplos para ambos casos a continuación.

### Ejemplo de código de retorno con estado final *Success*

```java
@Override
public Map<String, Dataset<Row>> transform (Map<String, Dataset<Row>> map) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<Row> df = map.get("fileAliasParquet").union(map.get("fileAliasCsv"));
    datasetsToWrite.put("union", df);
    SuccessExitCode.setExitCode(3);
    return datasetsToWrite;
}
```

### Ejemplo de código de retorno con estado final *Failed*

```java
@Override
public Map<String, Dataset<Row>> transform (Map<String, Dataset<Row>> map) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<Row> parquet = map.get("fileAliasParquet");
    long count = parquet.count();
    if (count == 0) {
        throw new LrbaApplicationException("Error", 6);
    }
    Dataset<Row> df = parquet.union(map.get("fileAliasCsv"));
    datasetsToWrite.put("union", df);
    return datasetsToWrite;
}
```

# spark/01-Utils.md
# Utilidades
LRBA Spark proporciona una clase para **crear** y **almacenar** *datasets*. Esta clase es **DatasetUtils**. Para empezar a utilizarla, es necesario crear una instancia de la clase.

## Operaciones con Datasets
LRBA Spark no permite crear una **Sesión de Spark**. Por lo tanto, proporciona los siguientes métodos para crear nuevos *datasets*, vacíos o no, sin el uso de la Sesión de Spark.

```java
    public Dataset<Row> createEmptyDataFrame(StructType schema)
    public Dataset<Row> createEmptyDataFrame(Class<T> tClass)
    public Dataset<Row> createDataFrame(List<Row> list, StructType schema)
    public Dataset<Row> createDataFrame(List<T> list, Class<T> tClass)
    public Dataset<Row> createDataFrame(RDD<T> rdd, Class<T> tClass)
    public Dataset<Row> createDataFrame(RDD<Row> rdd, StructType schema)
    public Dataset<Row> createDataFrame(JavaRDD<T> rdd, Class<T> tClass)
    public Dataset<Row> createDataFrame(JavaRDD<Row> rdd, StructType schema)
    public Dataset<T> createEmptyDataset(Encoder<T> encoder)
    public Dataset<T> createDataset(List<T> list, Encoder<T> encoder)
    public Dataset<T> createDataset(RDD<T> rdd, Encoder<T> encoder)
    public Dataset<T> createDataset(Seq<T> seq, Encoder<T> encoder)
```

Ejemplo de código:
```java
    DatasetUtils<SomeClass> utils = new DatasetUtils<>();
    Encoder<SomeClass> encoder = Encoders.bean(SomeClass.class);
    Dataset<SomeClass> dataset = utils.createEmptyDataset(encoder);
```

## Datasets en caché
LRBA Spark permite almacenar los *datasets* en caché. Lo que hace esta operación es persistir el *dataset* utilizando el Storage **MEMORY\_ONLY\_SER**, que almacena el *dataset* recibido como un objeto serializado en la memoria de la JVM.

```java
    public Dataset<T> cacheDataset(Dataset<T> dataset)
```

## No persistir Datasets
LRBA Spark permite **des-persistir** *datasets*. Las siguientes operaciones marcan el *dataset* como no persistente y eliminan todos sus bloques de la memoria y del disco. 
Esto no anulará la persistencia de ningún dato almacenado en caché que se haya creado a partir de este *dataset*. Están disponibles los siguientes métodos:

```java
    public Dataset<T> unpersistDataset(Dataset<T> dataset)
    public Dataset<T> unpersistDataset(Dataset<T> dataset, boolean blocking)
```
Por defecto, el primer método llama al segundo con la variable *blocking* a `false`.

Bloqueo - La ejecución del proceso no continuará hasta que se haya realizado el borrado de todos los bloques.

## Registrar UDFs
LRBA Spark permite **registrar UDFs**. La siguiente operación recupera un objeto *UDFRegistration*, utilizado para registrar funciones definidas por el usuario.

Código de ejemplo para registrar una función definida por el usuario que concatena el valor de 2 columnas:
```java
    private UDF2<String, String, String> myUdf(){
        return ( s1, s2 ) -> s1 + s2;
    }
    
    DatasetUtils<SomeClass> utils = new DatasetUtils<>();
    utils.udf().register("UDF_NAME", myUdf(), DataTypes.StringType);
```

## Envío de Datasets a un API HTTP
LRBA Spark permite enviar datos de *datasets* a APIs. Para ello, es necesario implementar una instancia personalizada de la interfaz `ISparkHttpData`. Si además se requiere autenticación OAuth, las implementaciones personalizadas `SparkOAuthRequest` y `SparkOAuthResponse` son obligatorias.
A continuación, el *dataset* debe convertirse en la implementación personalizada de `ISparkHttpData`. Por último, el desarrollador debe llamar al método que realmente ejecuta las llamadas.
Si OAuth y el API existen fuera de la red interna de BBVA, se debe indicar la configuración del proxy a través de `SparkHttpConnectorParameters`.

```java
    // Transform Dataset from Dataset<UserInput> to Dataset<SparkHttpDataImpl> (SparkHttpDataImpl implements ISparkHttpData)
    final Dataset<SparkHttpDataImpl> userOutputDS = userInputDS.mapPartitions((MapPartitionsFunction<UserInput, SparkHttpDataImpl>) it -> {
        final List<SparkHttpDataImpl> sparkAPIDataList = new ArrayList<>();
        while(it.hasNext()) {
            final UserInput userInput = it.next();
            sparkAPIDataList.add(
                    new SparkHttpDataImpl(new SparkHttpRequest.SparkHttpRequestBuilder<Request>()
                            .endpoint(API_ENDPOINT)
                            .method(SparkHttpRequest.HttpMethod.POST)
                            .header("Content-Type", SparkHttpRequest.SparkContentType.JSON)
                            .body(Collections.singletonList(this.userInputRequest(userInput)))
                            .build(), null)
            );
        }
        return sparkAPIDataList.iterator();
    }, Encoders.bean(SparkHttpDataImpl.class));

    // Instantiate OAuth data (SparkOAuthRequest extends SparkOAuthRequest, SparkOAuthResponseImpl extends SparkOAuthResponse)
    final SparkOAuthData<SparkOAuthRequestImpl, SparkOAuthResponseImpl> sparkOAuthData = new SparkOAuthData.SparkOAuthDataBuilder<SparkOAuthRequestImpl, SparkOAuthResponseImpl>()
            .uri(URI.create(Transformer.OAUTH_TOKEN_ENDPOINT))
            .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
            .request(new SparkOAuthRequestImpl())
            .responseClass(SparkOAuthResponseImpl.class)
            .authInHeader(false)
            .method(SparkHttpRequest.HttpMethod.POST)
            .contentTypeToken(SparkHttpRequest.SparkContentType.WWW_FORM_URLENCODED)
            .tokenExpiredStatusCode(401)
            .build();

    // Execute API calls
    final SparkHttpConnector<Request, Response, SparkHttpDataImpl> sparkHttpConnector = new SparkHttpConnector<>();
    final Dataset<SparkHttpDataImpl> resultDS = sparkHttpConnector.executeWithOAuth(userOutputDS, sparkOAuthData, Response.class, SparkHttpDataImpl.class, new SparkHttpConnectorParameters.SparkHttpConnectorParametersBuilder()
                .sparkProxy(new SparkProxy({PROXY_BASIC_CREDENTIALS_KEY}, ProxyData.ProxyType.BUSINESS))
                .build());
```

**IMPORTANTE**: Al utilizar esta utilidad, es obligatorio que la clase *transformer* implemente `Serializable`. Además, si se quiere enviar un contenido binario byte[], es necesario añadir la cabecera `Content-Type` con el valor `application/octet-stream`.

La ventaja que esta utilidad proporciona sobre *[HTTP REST Target](connectors/05-HTTP.md)* es que es posible ejecutar tareas adicionales sobre el *dataset* resultante.

Por ejemplo, si el desarrollador desea almacenar peticiones HTTP API fallidas, es posible filtrar las respuestas cuyo código de estado >= 400 para su posterior procesamiento.
Si la solicitud no puede ejecutarse por *timeout* o conexión denegada, el código de estado devuelto es 0.
El motivo se devolverá como una cadena JSON. Por ejemplo `{"error": "HTTP Timeout Error"}`. Dependiendo de la clase indicada para la respuesta, la utilidad intentará parsearla o devolverla como String.

## Test de integración

La utilidad LRBA Test te ayuda en la creación de tests de integración para el *transformer*. Sólo está disponible en tests y no debe utilizarse en código normal.

La clase de test debe extender `LRBASparkTest`:
```java
class TransformerTest extends LRBASparkTest {
    // ...
}
```

`LRBASparkTest` se encarga de crear el contexto Spark para los tests de integración.
Además, proporciona dos métodos de utilidad:

```java
    protected final <T> Dataset<Row> targetDataToDataset(List<T> targetData, Class<T> cls)
    protected final <T, U> List<T> datasetToTargetData(Dataset<U> dataset, Class<T> cls)
```
- `targetDataToDataset` permite al desarrollador transformar una `List` de objetos cuya clase es `T` en un `Dataset<Row>` que contenga todos esos objetos.
- `datasetToTargetData` permite transformar al desarrollador un `Dataset` de cualquier tipo en una `List` de objetos cuya clase es `T`.

## Mock de las variables de entorno en los tests

A veces, es necesario hacer un mock de las variables de entorno de la arquitectura en las pruebas.  
Para ello se ha añadido la librería *[System Stubs](https://github.com/webcompere/system-stubs/blob/main/system-stubs-jupiter/README.md)* y su integración con JUnit.

### Como utilizarlo

Antes de utilizar objetos *System Stubs* dentro de un test JUnit 5, debemos añadir la extensión a nuestra clase de test:
```java

@ExtendWith(SystemStubsExtension.class)
class EnvironmentVariablesJUnit5 {
	// tests
}
```
Entonces, podemos crear un campo en la clase de prueba para que JUnit 5 lo gestione por nosotros. Lo anotamos con `@SystemStub` para que la extensión sepa que debe activarlo:

```java
@SystemStub
private EnvironmentVariables environmentVariables;
```
Aquí no hemos proporcionado ninguna construcción del objeto *stub*, la extensión construye uno por nosotros.  
Ahora podemos utilizar el objeto para ayudarnos a establecer variables de entorno dentro de uno de nuestros tests:

```java
@Test
void givenEnvironmentCanBeModified_whenSetEnvironment_thenItIsSet(){
		environmentVariables.set("ENV","value1");

		assertThat(System.getenv("ENV")).isEqualTo("value1");
		}
```

Si quisiéramos proporcionar las variables de entorno que se aplican a todos los tests desde fuera del método de test, podemos hacerlo dentro de un método `@BeforeEach` o podemos utilizar el constructor de `EnvironmentVariables` para establecer nuestros valores:

```java
@SystemStub
private EnvironmentVariables environmentVariables=
		new EnvironmentVariables()
		.set("ENV","value1")
		.set("ENV2","value2");
```

Para más información, consulte la documentación oficial de la biblioteca *[System Stubs Jupiter](https://github.com/webcompere/system-stubs/blob/main/README.md)*.


# spark/02-DatasetInlineQueries.md
# Dataset Inline Queries
En ciertas ocasiones se necesita completar un dataset de entrada con información de alguna BBDD, 
por ejemplo buscar datos en una tabla en base a identificadores que se tienen en un dataset de entrada. 
Ahora mismo esto solo se puede hacer descargando la tabla completa, generando dos datasets y cruzando sus datos 
pudiendo ocasionar problemas de descarga de tablas o generando un plan de ejecución muy grande que no sea manejable.

Con *Dataset inline queries* se pretende dar la capacidad de lanzar **queries independientes**, de tipo **SELECT**, a la BBDD por cada fila
de un dataset evitando consumir ArrayList en memoria. Esta capacidad se ha creado de forma que se integra con la 
función **flatMap** del API dataset de Spark la cual requiere de un **iterador** como respuesta, 
siendo Spark quien gestiona los elementos del iterador para generar un dataset.

Esta funcionalidad va a estar disponible para las siguientes BBDD NextGen:
- Oracle
- ElasticSearch
- MongoDB
- Couchbase

En cada una de ellas se va a seguir el mismo método para hacer las queries, pero cada una de ellas tiene sus particularidades
como podrían ser el formato de la query, el tipo de conexión, etc. Para cada una se tendrá que implementar una interfaz con los
métodos necesarios para poder hacer la query y el mapeo de los resultados a un objeto de salida, indicar el *serviceName* y el *searchValue*.
Después se dará una clase estática por cada gestor para hacer la query dentro del flatmap y devolver el iterador con los resultados. 
Un ejemplo genérico de como se haría sería el siguiente:

```java
Dataset<OracleData> oracleResults = datasetEdades.flatMap((FlatMapFunction<MyBean, OracleData>) searchValue -> JdbcIterableQuery.createQuery(
                new MyJdbcHelper(),
                serviceName,
                searchValue), Encoders.bean(OracleData.class));
```

**Nota**: Estas consultas están pensadas para realizarse sobre datasets pequeños, ya que si se lanzan sobre datasets grandes puede ser que el rendimiento no sea el esperado.

## Oracle
Estas consultas se realizan mediante el driver JDBC de Oracle. Por ello se proporciona la interfaz ***IJdbcIterableQueryHandler*** para implementar 
la lógica de la consulta y el mapeo de los resultados a un objeto de salida mediante el tratamiento de los **ResultSet**.

```java
void setSearchValue(I searchValue);
String getQuery();
void prepareBindVariables(PreparedStatement preparedStatement) throws SQLException;
O processResultSet(ResultSet resultSet);
boolean processNoData();
```

Para realizar la consulta se utiliza el método estático ***JdbcIterableQuery.createQuery*** que recibe como parámetros el objeto que implementa la interfaz
***IJdbcIterableQueryHandler***, el *serviceName* y el *searchValue*. Este método devuelve un iterador de objetos mapeados
a la clase de salida que se ha indicado en el método.

Para un ejemplo más detallado de como implementar la interfaz y como lanzar la consulta se puede realizar el *codelab* de *Oracle Inline Queries*.

## Couchbase
Para realizar estas consultas se utiliza el SDK Java de Couchbase. De cara al usuario se proporciona la interfaz ***ICouchbaseIterableQueryHandler*** para implementar
la lógica de la consulta y el mapeo de los resultados a un objeto de salida mediante el tratamiento de un **Map<String, Object>** que contiene el nombre de los campos y su valor asociado.

```java
void setSearchValue(I searchValue);
String getQuery();
Map<String, Object> getQueryParameters();
O processResultDocument(Map<String, Object> document);
boolean processNoData();
```

En el método ***getQuery*** se debe devolver la consulta en formato N1QL añadiendo parámetros de búsqueda en el formato **$paramName**. Un ejemplo de consulta sería el siguiente:

```sql
SELECT * FROM myCollection WHERE name = $name AND age = $age
```

El método ***getQueryParameters*** devuelve un **Map<String, Object>** con los parámetros de búsqueda que se van a utilizar en la consulta sin añadir el símbolo **$**. 

```java
return Map.of("name", searchValue.getName(), "age", searchValue.getAge());
```

Para realizar la consulta se utiliza el método estático ***CouchbaseIterableQuery.createQuery*** que recibe como parámetros el objeto que implementa la interfaz
***ICouchbaseIterableQueryHandler***, el *serviceName* y el *searchValue*. Este método devuelve un iterador de objetos mapeados
a la clase de salida que se ha indicado en el método.

Para un ejemplo más detallado de como implementar la interfaz y como lanzar la consulta se puede realizar el *codelab* de *Couchbase Inline Queries*.

## MongoDB
Para realizar estas consultas se utiliza el SDK Java de MongoDB. Se proporciona la interfaz ***IMongoIterableQueryHandler*** para implementar
la lógica de la consulta y el mapeo de los resultados a un objeto de salida mediante el tratamiento de un objeto de tipo **Document** que contiene el nombre de los campos y su valor asociado.

```java
void setSearchValue(I searchValue);
String getCollection();
String getQueryType();
Document getFindFilter();
List<Document> getAggregatePipeline();
O processResult(Document document);
boolean processNoData();
```
En el método ***getCollection*** se debe devolver el nombre de la colección sobre la que se va a realizar la consulta.

```java
return "myCollection";
```
En el método ***getQueryType*** se debe devolver el tipo de consulta que se va a realizar. Los valores posibles son **FIND** o **AGGREGATE**.

```java
return "FIND";
```
En el método ***getFindFilter*** se debe devolver un objeto de tipo **Document** con los filtros de búsqueda que se van a utilizar en la consulta de tipo **FIND**. Un ejemplo sería lo siguiente:

```java
return new Document("age", searchValue.getAge())
            .append("name", searchValue.getName());
```
En el método ***getAggregatePipeline*** se debe devolver una lista de objetos de tipo **Document** con los pasos que se van a utilizar en la consulta de tipo **AGGREGATE**. Un ejemplo sería lo siguiente:

```java
public List<Document> getAggregatePipeline() {
    Document match = new Document("$match", new Document("ciudad", this.ciudad));
    Document group = new Document("$group", new Document("_id", "$ciudad")
            .append("sum", new Document("$sum", 1)));

    return List.of(match, group);
}
```
Para realizar la consulta se utiliza el método estático ***MongoIterableQuery.createQuery*** que recibe como parámetros el objeto que implementa la interfaz
***IMongoIterableQueryHandler***, el *serviceName* y el *searchValue*. Este método devuelve un iterador de objetos mapeados
a la clase de salida que se ha indicado en el método.

Para un ejemplo más detallado de como implementar la interfaz y como lanzar la consulta se puede realizar el *codelab* de *MongoDB Inline Queries*.

## ElasticSearch
Para realizar estas consultas se utiliza el SDK Java de ElasticSearch. De cara al usuario se proporciona la interfaz ***IElasticIterableQueryHandler*** para implementar
la lógica de la consulta y el mapeo de los resultados a un objeto de salida mediante el tratamiento de un **Map<String, Object>** que contiene el nombre de los campos y su valor asociado.

```java
    /**
 * Set search value for the query.
 *
 * @param searchValue Search value to be set.
 */
void setSearchValue(I searchValue);

/**
 * Retrieves the query to be executed.
 *
 * @return The query as a string.
 * <p>
 * Example:
 * <pre>
 * <code>
 * """
 * {
 *   "query": {
 *     "bool": {
 *       "must": [
 *         {
 *           "match_phrase": {
 *             "cuisine": {
 *               "query": "{{cuisine_param}}"
 *             }
 *           }
 *         },
 *         {
 *           "match_phrase": {
 *             "city": {
 *               "query": "{{city_param}}"
 *             }
 *           }
 *         }
 *       ]
 *     }
 *   }
 * }
 * """
 * </code>
 * </pre>
 */
String getQuery();

/**
 * Get the elastic index
 *
 * @return the elastic index
 */
String getIndex();

/**
 * Gets the parameters for the query.
 *
 * @return Map of parameters to Bind the query.
 * <p>
 * Example:
 * <pre>
 *     <code>
 *         Map.of("cuisine_param", "Contemporary", "city_param", "San Francisco");
 *     </code>
 * </pre>
 */
Map<String, Object> getMapBindVariables();

/**
 * Processes each document returned by the query.
 *
 * @param document Each document returned by the query.
 * @return Processed document as an object.
 */
O processResultDocument(Map<String, Object> document);

/**
 * Processes the result of the query when no data is returned.
 *
 * @return `true` if empty result set should be processed, `false` otherwise.
 */
boolean processNoData();
```

En el método ***getQuery*** se debe devolver la consulta en formato JSON que será ejecutada en modo *search template*. Esto permite crear una consulta parametrizable donde las variables se pasarán entre dobles llaves.
Un ejemplo de consulta sería el siguiente:

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match_phrase": {
            "Period": "{{year_param}}"
          }
        },
        {
          "match_phrase": {
            "company": "{{company_param}}"
          }
        }
      ]
    }
  }
} 
```

*Aviso:* 

Es importante destacar que por defecto el cliente java de elastic pagina los resultados de la consulta con un tamaño de página de 10 elementos.
Esto se puede customizar con el atributo *size*. 

Ejemplo:

```java
@Override public String getQuery() {
    return """
                  {
                     "query": {
                       "bool": {
                         "should": [
                           {
                             "match_phrase": {
                               "Period": "{{year_param}}"
                             }
                           },
                           {
                             "match_phrase": {
                               "company": "{{company_param}}"
                             }
                           }
                         ]
                       }
                     },
                     "size": 5
                   }    
            """;
```
También se pueden usar las estrategias:
* from + size. (No viable para conjuntos de resultados >10.000 documentos)
* search_after
  Para más información referirse a la documentación oficial de elastic search.

El método ***getMapBindVariables*** devuelve un **Map<String, Object>** con los parámetros de búsqueda que se van a utilizar en la consulta.

```java
return Map.of("year_param", searchValue.getYear(), "company_param", searchValue.getCompany());
```

El método ***getIndex*** devuelve el indice de elastic sobre el que se va a realizar la consulta.
```java
return "i_lrba_test";
```

# lrba_docs/FAQs.md
# Preguntas Frecuentes

Índice
- [Codificación de caracteres](#codificación-de-caracteres)
- [Programación con fechas](#programación-con-fechas)
- [Compartir datos](#compartir-datos) 
- [Developer Experience](#developer-experience)
- [Orquestación](#orquestación)
- [Misceláneo](#misceláneo)
- [Buenas Prácticas](#buenas-prácticas)

## Codificación de caracteres

### Codificación de caracteres en LRBA

La Arquitectura LRBA está basada en Java, que acepta y maneja codificación Unicode.

Por otro lado, no todas las bases de datos con las que trabaja LRBA son Unicode. Eso quiere decir que **NO** todos los caracteres son válidos en ellas. En esta [web](https://www.compart.com/en/unicode/charsets/) se pueden comprobar qué sets de caracteres son válidos para cada una de las normas de codificación de los charset.

Por ejemplo, DB2 y Oracle usan codificación no-Unicode, mientras que Percona, Elastic y Couchbase sí que tienen codificación Unicode.

Además, LRBA genera ficheros en Unicode (UTF-8) y espera que los ficheros entrantes también tengan esa codificación.

### Codificación de caracteres en DB2 España

En DB2, los datos se encuentran grabados en la codificación [IBM284](https://www.compart.com/en/unicode/charsets/IBM284). Sin embargo, la base de datos muestra en sus metadatos que la codificación es [IBM500](https://www.compart.com/en/unicode/charsets/IBM500). Es decir, los metadatos NO reflejan la correcta codificación con la que están grabados los datos.
Esto implica que cualquier programa cliente de JDBC, ODBC... que intente hacer una lectura, interpretará que el charset es IBM500. Y procesará incorrectamente los caracteres que no coinciden entre [IBM284](https://www.compart.com/en/unicode/charsets/IBM284) e [IBM500](https://www.compart.com/en/unicode/charsets/IBM500)

Por otro lado, Java utiliza internamente Unicode (UTF-16), donde hay representación de todos los caracteres que existen en todo el mundo.

Los drivers se encargan de hacer las interpretaciones de IBM500 a UTF-16. Debido a que inicialmente, los datos en DB2 están mal grabados en IBM284, la interpretación que hará Java es incorrecta tal y como hemos explicado antes, al intentar convertir a IBM500.

Para solucionarlo, es necesario que en DB2 se genere una vista con una función *translate* de IBM284 a IBM500, para que DB2 entregue los bytes de salida como se espera.

### Escritura de ficheros con acentos

No está permitido escribir ficheros con acentos ya que sistema de ficheros no lo soporta.

## Programación con fechas

### Oracle Date no es equivalente a un Date Lógico

En Oracle el tipo Date contiene año, mes, día, horas, minutos y segundos. En este [link](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Data-Types.html#GUID-7B72E154-677A-4342-A1EA-C74C1EA928E6), en la tabla *Table 2-1 Built-In Data Type Summary* se encuentra la definición. Debido a esto, su representación por defecto en JDBC es `java.sql.Timestamp`. En la documentación del [driver Oracle JDBC (Mapping SQL DATE Data type to Java)](https://docs.oracle.com/en/database/oracle/oracle-database/19/jjdbc/JDBC-reference-information.html#GUID-FCB7E652-4532-47AF-9783-B7E2B6ADA41C) se explica el motivo y cómo modificar el comportamiento por defecto (`mapDateToTimestamp=false`).

En la siguiente [documentación de Spark (aún en preview de la versión 4.0)](https://spark.apache.org/docs/4.0.0-preview1/sql-data-sources-jdbc.html#mapping-spark-sql-data-types-from-oracle) explican que Spark por defecto mapea Oracle DATE con Spark `TimestampType`. También explican como usar la propiedad JDBC para que el mapeo sea a `DateType`.

Si se quiere cambiar este comportamiento, en el job de LRBA se debe modificar el Source añadiendo manualmente el método `addOption` con el valor `oracle.jdbc.mapDateToTimestamp=false`. [Más información](utilities/spark/connectors/02-JDBC.md#basic).

### Filtros Pushdown de fechas

Los filtros pushdown en Apache Spark son una optimización que permite que ciertas operaciones de filtrado se realicen directamente en la base de datos en lugar de en Spark. Esto puede mejorar significativamente el rendimiento al reducir la cantidad de datos que se transfieren desde la base de datos a Spark y al aprovechar las capacidades de procesamiento de la base de datos.

A continuación, proponemos diferentes maneras de hacerlo con ejemplos:

1. Utilizando el método `query` del Source Builder. Para ello habría que construir una query de la siguiente manera:

- Si es Date
```
SELECT * FROM alias WHERE columnName > TO_DATE('2024-01-01', 'yyyy-MM-dd') AND columnName < TO_DATE('2025-01-01', 'yyyy-MM-dd')
```
- Si es Timestamp
```
SELECT * FROM alias WHERE columnName > TO_TIMESTAMP('2024-01-01 00:00:00.000', 'yyyy-MM-dd HH:mm:ss.SSS') AND columnName < TO_TIMESTAMP('2025-01-01 00:00:00.000', 'yyyy-MM-dd HH:mm:ss.SSS')
```

2. Utilizando el método `filter` sobre un Dataset:

- Si es Date
```
dataframe.filter(col("columnName").leq(date_format(lit("2025-01-01T00:00:00.000+0200"), "yyyy-MM-dd'T'HH:mm:ss.SSSZZ")));
```

- Si es Timestamp
```
dataframe.filter(col("columnName").gt(to_timestamp(lit("2024-01-01"), "yyyy-MM-dd")));
```

En este caso, si el gestor es Elastic, se tiene que establecer la propiedad `es.mapping.date.rich` a `false`. En LRBA, se puede utilizar el método `useRichDateObject` para definirla. [Más información](utilities/spark/connectors/04-Elastic.md#basic)

3. Utilizando la [query nativa en Elastic (DSL)](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html#_querying):

Para ello habría que introducir la query utilizando el método `addCustomElasticHadoopConfig` en el Source Builder. En la clave habría que introducir `es.query` y en el valor:

```
{"range": {"columnName": {"gte": "2024-01-01T00:00:00.000+02:00", "format":"strict_date_optional_time_nanos"}}}
```

Como en el caso anterior, se tiene que establecer la propiedad `es.mapping.date.rich` a `false`. En LRBA, se puede utilizar el método `useRichDateObject` para definirla. [Más información](utilities/spark/connectors/04-Elastic.md#basic)

## Compartir datos

### No funciona la compartición de ficheros habiendo dado permisos a la UUAA

Para que un fichero pueda ser compartido entre UUAAs en LRBA se tiene que cumplir:
* El job de LRBA que escribe el fichero en BTS debe hacerlo con [visibilidad compartida](utilities/spark/connectors/01-File.md#bts).
* Actualmente, sólo pueden ser compartidos ficheros generados por  un Job LRBA. Por tanto, quedan descartados aquellos que, por ejemplo, provengan de transferencias DataX.
* Las UUAAs que quieran consumir estos ficheros deben pertenecer a la misma geografía de la UUAA generadora de los mismos.

### Permisos cruzados entre datos de diferentes geografías

El consumo de datos está limitado a datos provenientes de la misma geografía tanto para BTS como para Bases de Datos.

## Developer Experience

### No puedo ver trazas y logs en Atenea

Si no puedes ver trazas y logs en Atenea, revisa la documentación de este [enlace](developerexperience/05-ReadingJobLogs.md) y sigue los pasos que se indican. Seguramente no estén metiendo los filtros mrId en algún punto.

### Build inestable en el step Sonar Coverage

Revisa que los tests de la build hayan pasado correctamente y no den error.

## Orquestación

### Permisos en los Namespaces de Cronos

Si no tienes permisos en los namespaces de Cronos, el Solution Architect de la UUAA debe habilitar el uso de Cronos en los TechSpecs a través de la Consola Ether, como se indica en la [documentación de Cronos](https://platform.bbva.com/cronos/documentation/1P_7BzBROaA3PqUy79TLa4tACUL0zmuHiP2ryKec1ZbM/other-considerations)

## Misceláneo

### Mensajes de error en LRBA CLI

Si el CLI te devuelve algun de estos mensajes:

```
Cannot retrieve config file from BitBucket check your BitBucket token: Unauthorized download. Check your config to confirm that your Bitbucket token is correct and has not expired
```

```
Unauthorized download. Check your config to confirm that your Artifactory Api Key is correct and has not expired
```

es porque te ha caducado el token de acceso a Bitbucket y/o a Artifactory. Por favor, renueva los tokens correspondientes y ejecuta [`lrba config`](developerexperience/01-HowToWork.md#configuraciones) para modificar los valores y que el LRBA CLI vuelva a funcionar correctamente.

### Obtención de credenciales de Vault para certificados HTTP con Mutual TLS

Si se produce un error como el que se muestra a continuación, puede deberse a varios motivos:
```
com.bbva.lrba.exception.LrbaException: Can not obtain vault secret with secret key {path/to/credential}. Status: 404. Body: {"errors":[]} "
```
1. El alias del certificado no es el correcto. Revisa que el valor introducido en el alias del Builder es el correcto. [Más información](utilities/spark/connectors/05-HTTP.md#mutual-tls-mtls).
2. El certificado no está aprovisionado en Vault. En el segundo punto de este [enlace](commonoperations/01-CreateCredentials.md#solicitar-certificados-para-http-mutual-tls), se explica cómo aprovisionar el certificado en Vault.
3. La contraseña del certificado no está aprovisionada en Vault. En el tercer punto de este [enlace](commonoperations/01-CreateCredentials.md#solicitar-certificados-para-http-mutual-tls), se explica cómo aprovisionar la contraseña certificado en Vault.

   **NOTA**: Si cuando se pide aprovisionar la contraseña en el Vault se hace en el país incorrecto, el proceso tampoco funcionará por el mismo motivo. Vuelve a este [enlace](commonoperations/01-CreateCredentials.md#solicitar-certificados-para-http-mutual-tls) y sigue las instrucciones para aprovisionarla correctamente.

### Diferencias entre los diferentes estados de error de LRBA

- **Dead**: por defecto los jobs en LRBA sólo pueden ejecutarse por un máximo de 24 horas en el cluster. Si se sobrepasan las 24 horas se fuerza la terminación del job.

- **Unknown**: el driver del job ha muerto. Esto implica que hay una sobrecarga de los recursos asignados al driver debido a una codificación deficiente del job (Por ejemplo: un broadcast o un collect con demasiados datos). Subir la talla del job no va a cambiar el resultado, hay que recodificar el job siguiendo las [buenas prácticas](#buenas-prácticas) que se detallan en esta sección.

- **Failed**:
  - La ejecución del job ha finalizado debido a un error aplicativo: de código o de acceso a base de datos. Si es este el caso, revisa el motivo y soluciona el problema recodificando el job para que no vuelva a suceder.
  - Los ejecutores se mueren por falta de recursos (memoria o disco). Revisa [esta sección](LRBA-Sizes.md#errores-asociados-con-memoria) de la documentación para proceder.
  - Error técnico/comunicaciones. En este caso, revisa nuestra [página de Soporte](Support.md#soporte) para proceder.

### Borrados en base de datos

Para hacer un borrado de datos en Oracle de manera puntual, no es necesario enviar el Dataset con todos los campos de la tabla al Target de borrado, bastaría con enviar sólo los campos por los que identificar los registros a borrar, por ejemplo la Primary Key (PK).

Para cualquier otro tipo de borrados masivos de base de datos, como pudieran ser truncados totales de tablas, truncados de particiones, borrados completos de indices o colecciones, se deben utilizar las utilidades que proporciona BBDD (DBUtils) y que se ejecutan a través del ShellScriptLauncher de APX.

### Hacer rollback en Base de datos después de una excepción en el Job

Si se producen problemas en el job, este se ha parado y se ha realizado cambios en BBDD, **NO** se puede hacer rollback en base de datos, se debe de ejecutar de nuevo el job.

Sólo en caso de Oracle (al ser un gestor transaccional), la BBDD hará rollback autómatico del último bulk de datos.

### Mover ficheros con wildcard

Desde la [versión 2.0.0](ReleaseNotes.md#v201) se permite realizar movimientos de ficheros con wildcard. Todos los ficheros deben de tener el mismo formato.

## Buenas Prácticas

Para información relacionada con las buenas prácticas, se recomienda consultar:
- [La documentación de LRBA](bestpractices/01-BestPractices.md)
- [La documentación del Equipo de OCTA](https://docs.google.com/document/d/11KoEMstpAPTAPfV5OtPRAoHpoPlnIsWJnn7WC1hbJ0w/edit?tab=t.0)




