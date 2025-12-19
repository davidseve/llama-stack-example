# 01-ReadTransformWriteFilesLocal/01-Introduction.md
# 1. Introducción

## ¿Qué es LRBA Spark?

LRBA Spark es una implementación de LRBA para manejar grandes conjuntos de datos. El **ámbito de uso** de esta nueva arquitectura incluye:

* Aplicación de procesos de datos entre **bases de datos operacionales** (Ether y Legacy) con lógica de transformación simple.

* Implementación de una **lógica operacional de negocio** que incluye fuentes de datos de origen y destino de bases de datos operacionales y volumetrías para dar soporte en paralelo y procesos en memoria.

LRBA Spark ofrece:

* Simplificación del desarrollo batch mediante aplicaciones sencillas (sólo SQL para ETL) o métodos de aplicación (Spark API) con *datasets*.

* El acceso a la configuración de los **gestores de bases de datos** y otras persistencias (buckets de Epsilon que estan DEPRECADOS o BTS) es transparente para el desarrollo de aplicaciones.

# 01-ReadTransformWriteFilesLocal/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
[El CLI de LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) ayuda a generar el código fuente, construir el *job*, probarlo y ejecutarlo en un entorno local. Lo único que se necesita es acceso al terminal del sistema.

# 01-ReadTransformWriteFilesLocal/03-Example.md
# 3. Ejemplo

## Introducción

En este ejemplo se desarrolla un *job* local con las siguientes tareas:

1. Leer dos archivos de entrada `.csv` con los siguientes datos:

***local-execution/files/input1.csv***
```csv
ENTIDAD,DNI,NOMBRE,TELEFONO
0182,000001,John Doe,123-456
0182,000002,Mike Doe,123-567
0182,000003,Paul Doe,123-678
```

***local-execution/files/input2.csv***
```csv
DNI,EMAIL
000001,johndoe@gmail.com
000002,mikedoe@gmail.com
000003,pauldoe@gmail.com
```

Ya existe un archivo de ejemplo en el proyecto en *local-execution/files*. Para poder seguir el ejemplo, modifique los archivos con la información anterior.

2. Hacer un *join* de ambos ficheros para el usuario con `DNI=000003`.

3. Escribe el resultado de la *join* en un archivo.


## Configuración de ejecución

1. [Descargar LRBA CLI](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5)

2. Ejecutar y configurar LRBA CLI.

![alt text](resources/Config.png)

![alt text](resources/ConfigCli.png)

3. Crear un *job* con LRBA CLI. Es importante tener un **nombre de job** descriptivo.

![alt text](resources/CreateJob.png)

![alt text](resources/JobCreated.png)

NOTA: Este sería un ejemplo en local, para el resto de *jobs* ir a [Dev Experience](https://platform.bbva.com/lra-batch/documentation/6928421ec69d4458184f61b9f1a493e6/lrba-architecture/developer-experience/ether-console-development).

## Desarrollo

1. Abrir un IDE. 
2. Configurar el IDE con la JDK y el `settings.xml` de Maven ubicado en la carpeta `/.lrba_cli`.
3. Importar proyecto.
4. Implementación

### Source

- Añadir un *source* para cada archivo de entrada.
- Añadir un alias para cada *source*.
- Añadir el nombre del servicio definido para el entorno local.
- Añadir un filtro SQL y solo obtener el usuario con `DNI='000003'`.

La clase *JobCodelabBuilder.java* sería:

```java
@Override
public SourcesList registerSources() {
	return SourcesList.builder()
		.add(Source.File.Csv.builder()
			.alias("sourceAlias1")
			.serviceName("local.logicalDataStore.batch")
			.physicalName("input1.csv")
			.sql("SELECT * FROM sourceAlias1 WHERE DNI='000003'")
			.header(true)
			.delimiter(",")
			.build())
		.add(Source.File.Csv.builder()
			.alias("sourceAlias2")
			.serviceName("local.logicalDataStore.batch")
			.physicalName("input2.csv")
			.sql("SELECT * FROM sourceAlias2 WHERE DNI='000003'")
			.header(true)
			.delimiter(",")
			.build())
		.build();
}
```

### Transform

- Unir dos archivos utilizando la columna DNI. Se guardará en el mapa con el alias `join` para poder utilizarlo posteriormente en el *target* como alias.

La clase *JobCodelabBuilder.java* sería:

```java
@Override
	public TransformConfig registerTransform() {
		return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
	}
```

La clase *Transformer.java* sería:
```java
@Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
        Dataset<Row> datasetUpdated = datasetsFromRead.get("sourceAlias1")
                .join(datasetsFromRead.get("sourceAlias2"), "DNI");
        datasetsToWrite.put("join", datasetUpdated);
        return datasetsToWrite;
    }
```

### Target

- Escribir en el fichero *local-execution/files/output.csv* el resultado final de la *join* de ambos ficheros con el alias obtenido en el paso anterior.

La clase *JobCodelabBuilder.java* sería:

```java
@Override
	public TargetsList registerTargets() {
		return TargetsList.builder()
				.add(Target.File.Csv.builder()
						.alias("join")
						.serviceName("local.logicalDataStore.batch")
						.physicalName("output/output.csv")
						.header(true)
						.delimiter(",")
						.build())
				.build();
	}
```

### Probar el job

Recomendamos encarecidamente utilizar la clase de utilidad `LRBASparkTest` que LRBA proporciona para probar el *job*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_InputData_ResultDatasets() {
		// InputSource1, InputSource2 and JoinOutput classes must be instantiated according to the expected inputs and outputs.

        final InputSource1 input11 = new InputSource1();
        // Fill sourceAlias1 fields
        final InputSource1 input12 = new InputSource1();
        // Fill sourceAlias1 fields
        final InputSource2 input21 = new InputSource2();
        // Fill sourceAlias2 fields
        final InputSource2 input22 = new InputSource2();
        // Fill sourceAlias2 fields

        final Dataset<Row> inputDS1 = this.targetDataToDataset(Arrays.asList(input11, input12), InputSource1.class);
        final Dataset<Row> inputDS2 = this.targetDataToDataset(Arrays.asList(input21, input22), InputSource2.class);
        final Map<String, Dataset<Row>> resultDSMap = this.transformer.transform(new HashMap<>(Map.of("sourceAlias1", inputDS1, "sourceAlias2", inputDS2)));
        final Dataset<Row> userOutput = resultDSMap.get("join");

        assertNotNull(userOutput);

        final List<JoinOutput> joinOutputList = this.datasetToTargetData(userOutput, JoinOutput.class);
        this.validateJoinOutputList(joinOutputList);
    }

    private void validateJoinOutputList(final List<JoinOutput> joinOutputList) {
        assertNotNull(joinOutputList);
		// Validate expected number of output objects
        assertEquals(2, joinOutputList.size());

        final JoinOutput joinOutput1 = joinOutputList
                .stream()
                .filter(joinOutput -> joinOutput
                        ...)
                .findFirst().orElse(null);
        assertNotNull(joinOutput1);
        // Validate joined object
    }

}
```

Para obtener más información sobre la utilidad de pruebas LRBA, consulte la sección *Test de integracion de jobs* en [LRBA Utils](../../utilities/spark/01-Utils.md).

## Ejecución

1. Ejecutar el proyecto con LRBA CLI.

![alt text](resources/Run.png)

![alt text](resources/SelectRunVersion.png)


Con este comando se realiza la compilación.

![alt text](resources/Build.png)


A continuación se inicia la ejecución del proceso.

![alt text](resources/Execution.png)


## Resultado


Es importante tener en cuenta que todos los archivos creados por Spark se particionan para:
- Trabajar con conjuntos de datos más pequeños.
- Realizar operaciones de lectura/escritura en paralelo.

El directorio de salida (*local-execution/files/output*) y el nombre asignado al fichero de salida se utilizan cuando se requiere mostrar un archivo escrito por Spark (como el ejemplo mostrado en este *codelab*). Los archivos en este directorio son:

- Un fichero llamado `\_SUCCESS` que indica que la escritura del fichero CSV ha finalizado con éxito.

- Varios ficheros `.csv`, en función del número de particiones que se considere tener, que serán los datos resultantes.

- Un archivo `.crc` para cada `.csv`,que es un control que Spark utiliza para saber que el contenido de los datos es correcto.

Como puede verse en la imagen, se realiza una unión de ambos ficheros para el usuario con `DNI='000003'`, resultando un único fichero con todos los campos.

![alt text](resources/Result.png)


# ¡Es tu turno para crear tus propios *jobs*!

# 02-DB2-BTS-ORACLE/01-Introduction.md
# 1. Introducción

Este *codelab* muestra el ciclo completo de DB2 a Oracle a través de BTS.
Se divide en 3 procesos principales.
* El primero lee de DB2 y escribe en BTS.
* El segundo lee de BTS, transforma los datos y los guarda de nuevo en BTS.
* Por último, lee desde BTS y escribe en Oracle.

# 02-DB2-BTS-ORACLE/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## Aprovisionamiento de UUAA y conexión a DB2 y Oracle

Este ejemplo no es un *job* que vayamos a ejecutar localmente. Su objetivo es guiar a los desarrolladores en la implementación de un *job* que se ejecute en el clúster.
Por este motivo, el primer requisito es que la UUAA del desarrollador esté previamente aprovisionada. Si no es así, abra una solicitud al equipo de soporte de LRBA.
También es obligatorio, disponer de conexión y permisos de lectura y escritura en tablas DB2 y Oracle. Si no es así, abre una incidencia a DaaS Security.

Vaya a la [página de soporte](https://platform.bbva.com/lra-batch/documentation/ee7143fa4ee75a4859bbc2a2b78dfe1b/lrba-architecture/support) para saber como abrir solicitudes o incidencias a los equipos mencionados.


# 02-DB2-BTS-ORACLE/03-Example.md
# 3. Ejemplo

## Introducción

En este ejemplo, desarrollaremos 3 *jobs* diferentes.

Para cada uno, necesitamos crear una nueva estructura base.

Después, sigue este *codelab* para implementar cada *job*.

Por último, despliegue todos los *jobs* implementados.


## Job DB2 a BTS

### Crear estructura base del job

1- Crear la estructura base del *job* utilizando [esta guía](https://platform.bbva.com/lra-batch/documentation/6928421ec69d4458184f61b9f1a493e6/lrba-architecture/developer-experience/console-ether-development).

2- Después, ve al enlace de bitbucket del *job* y clónalo en local.

3- Ábrelo con tu IDE preferido y modifica el código como te recomendamos en las siguientes secciones.


### Declarar Source

- Añadir un *source* JDBC para cada tabla a leer de DB2.
- Añadir un alias para cada *source* JDBC.
- Añadir un *physical name* perteneciente a la tabla que quieres leer. Recuerda la sintaxis **schema.nombre_tabla**.
- Añadir el *service name* definido para conectarse a la base de datos DB2. Recuerda la sintaxis `db2.{UUAA}.BATCH`.
- Añadir una SQL si se necesita filtrar los datos (opcional).

**IMPORTANTE**: Para este ejemplo usamos el tipo de *builder* JDBC.Basic, [ir a la documentación](https://platform.bbva.com/lra-batch/documentation/fa5ae005c0f461cd97f39721d1ce962f/lrba-architecture/utilities/spark/connectors/jdbc-connector-rdbms-persistence#content5) para otro tipo de constructores.

El método *registerSources* de la clase *JobCodelabBuilder.java* sería:

```java
@Override
public SourcesList registerSources() {
        return SourcesList.builder()
            .add(Source.Jdbc.Basic.builder()
                .alias("db2Source")
                .physicalName("SCHEMA.TABLE_NAME")
                .serviceName("db2.YOUR_UUAA.BATCH")
                .sql("SELECT * FROM db2Source")
                .build())
            .build();
        }
```

### Declarar Target

- Añadir un *target* de tipo File Parquet.
- Añadir un alias para el *target*.
- Añadir un *physical name* para identificar el nombre del fichero de salida.
- Añadir el *service name* definido para la conexión a BTS. Recuerda la sintaxis **bts.{UUAA}.BATCH**.

El método *registerTargets* en la clase *JobCodelabBuilder.java* sería:

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.File.Parquet.builder()
                .alias("btsTarget")
                .physicalName("db2downloadeddata.parquet")
                .serviceName("bts.LRBA.BATCH")
                .build())
            .build();
        }
```

### Declarar Transform

- En la clase *JobCodelabBuilder.java* no modificar el método *registerTransform* que está por defecto.
- Ir a la clase *Transformer.java* y modificar el método *transform* con el siguiente bloque de código.

```java
@Override
	public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {
		Dataset<Row> dataset = map.get("db2Source");
		map.put("btsTarget", dataset);
		return map;
	}
```


## Job BTS a BTS

Este *job* lee el fichero guardado con el *job* anterior, y otro archivo Parquet. 

Posteriormente, el *job* transforma los datos con la unión de ambos ficheros. 

Finalmente, el *job* crea un nuevo fichero y lo guarda de nuevo en BTS.

### Crear estructura base del job

1- Crear la estructura base del *job* utilizando [esta guía](https://platform.bbva.com/lra-batch/documentation/6928421ec69d4458184f61b9f1a493e6/lrba-architecture/developer-experience/console-ether-development).

2- Después, ve al enlace de bitbucket del *job* y clónalo en local.

3- Ábrelo con tu IDE preferido y modifica el código como te recomendamos en las siguientes secciones.


### Declarar Source

- Añadir un *source* de tipo *File* Parquet para leer el fichero *db2downloadeddata* del BTS.
- Añadir un alias para el *source File* Parquet.
- Añadir *db2downloadeddata.parquet* como *physical name* utilizado para identificar el fichero de entrada para leer.
- Añadir el *service name* definido para el almacenamiento BTS de la UUAA. Recuerda la sintaxis `bts.{UUAA}.BATCH`.
- Añadir una SQL si se necesita filtrar los datos (opcional).

El método *registerSources* en la clase *JobCodelabBuilder.java* sería:

```java
@Override
public SourcesList registerSources() {
        return SourcesList.builder()
            .add(Source.File.Parquet.builder()
                .alias("inputFile")
                .physicalName("db2downloadeddata.parquet")
                .serviceName("bts.YOUR_UUAA.BATCH")
                .sql("SELECT * FROM inputFile")
                .build())
            .add(Source.File.Parquet.builder()
                .alias("anotherInputFile")
                .physicalName("another_file.parquet")
                .serviceName("bts.YOUR_UUAA.BATCH")
                .sql("SELECT * FROM anotherInputFile")
                .build())
            .build();
        }
```

### Declarar Target

- Añadir el *target* de tipo *File* Parquet.
- Añadir un alias para el *target*.
- Añadir un *physical name* para identificar el nombre del fichero de salida.
- Añadir el *service name* definido para la conexión con BTS. Recuerda la sintaxis `bts.{UUAA}.BATCH`.

El método *registerTargets* en la clase *JobCodelabBuilder.java* sería:

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.File.Parquet.builder()
                .alias("outputFile")
                .physicalName("transformedData.parquet")
                .serviceName("bts.LRBA.BATCH")
                .build())
            .build();
        }
```

### Declarar Transform

- En la clase *JobCodelabBuilder.java* no modificar el método *registerTransform* que está por defecto.
- Ir a la clase *Transformer.java* y modificar el método *transform* con el siguiente bloque de código.

```java
@Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {
        Dataset<Row> dataset1 = map.get("inputFile");
        Dataset<Row> dataset2 = map.get("anotherInputFile");
        Dataset<Row> transformedDS = dataset1.union(dataset2);
        map.put("outputFile", transformedDS);
        return map;
    }
```


## Job BTS a Oracle

### Crear estructura base del job

1- Crear la estructura base del *job* utilizando [esta guía](https://platform.bbva.com/lra-batch/documentation/6928421ec69d4458184f61b9f1a493e6/lrba-architecture/developer-experience/console-ether-development).

2- Después, ve al enlace de bitbucket del *job* y clónalo en local.

3- Ábrelo con tu IDE preferido y modifica el código como te recomendamos en las siguientes secciones.


### Declarar Source

- Añadir un *source* de tipo *File* Parquet para leer el fichero *transformedData* del BTS.
- Añadir un alias para el *source File* Parquet.
- Añadir *transformedData.parquet* como *physical name*, utilizado para identificar el fichero de entrada para leer.
- Añadir el *service name* definido para el almacenamiento BTS de la UUAA. Recuerda la sintaxis `bts.{UUAA}.BATCH`.
- Añadir un SQL si se necesitan datos para filtrar (opcional).

El método *registerSources* en la clase *JobCodelabBuilder.java* class sería:

```java
@Override
public SourcesList registerSources() {
        return SourcesList.builder()
            .add(Source.File.Parquet.builder()
                .alias("transformedFile")
                .physicalName("transformedData.parquet")
                .serviceName("bts.YOUR_UUAA.BATCH")
                .sql("SELECT * FROM transformedFile")
                .build())
            .build();
        }
```

### Declarar Target

- Añadir un *target* del tipo Jdbc Insert.
- Añadir un alias para el *target*.
- Añadir el *physical name* perteneciente a la tabla que quieres modificar. Recuerda la sintaxis `schema.nombre_tabla`.
- Añadir el *service name* definido para la conexión con Oracle. Recuerda la sintaxis `oracle.{UUAA}.BATCH`.

El método *registerTargets* en la clase *JobCodelabBuilder.java* sería:

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.Jdbc.Insert.builder()
                .alias("oracleTraget")
                .physicalName("SCHEMA.TABLE_NAME")
                .serviceName("oracle.LRBA.BATCH")
                .build())
            .build();
        }
```

### Declarar Transform

- En la clase *JobCodelabBuilder.java* no modificar el método *registerTransform* definido por defecto.
- Ir a la clase *Transformer.java* y modificar el método *transform* con el siguiente bloque de código.

```java
@Override
	public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {
		Dataset<Row> dataset = map.get("transformedFile");
		map.put("oracleTraget", dataset);
		return map;
	}
```


## Ejecutar el job en el clúster

1 - Hacer push del código de cada *job* a Bitbucket.

2 - Ejecutar el *job* en el clúster en orden. 
* Primero, *Job* DB2 a BTS.
* Segundo, *Job* BTS a BTS.
* Por último, *Job* BTS a Oracle.
Para ello, despliegue el *job* siguiendo [esta guía](https://platform.bbva.com/lra-batch/documentation/6928421ec69d4458184f61b9f1a493e6/lrba-architecture/developer-experience/console-ether-development).



# 03-ExecuteAPICalls/01-Introduction.md
# 1. Introducción

**API** es el acrónimo de **Application Programming Interface**, que es un intermediario de *software* que **permite que dos aplicaciones se comuniquen entre sí**.
Cada vez que se utiliza una aplicación como la de BBVA, se envía un mensaje o se consulta el tiempo online, se está usando una API.  

LRBA permite ejecutar llamadas a API usando la funcionalidad y el paralelismo de Spark.  

En este ejemplo se verá como usar el target HTTP para realizar llamadas a una API en una ejecución local.  
El propósito de este *codelab* es entender que clases se deben implementar para realizar peticiones a API y guardar sus respuestas, por lo que para simplificarlo, se usará una API simulada que no requiere autenticación ni *proxy*.

# 03-ExecuteAPICalls/02-Prerequisites.md
# 2. Prerrequisitos

## IDEs de Java

Eclipse es un IDE código abierto. Se puede descargar de aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).  
IntelliJ IDEA es otro IDE, con una versión gratuita que puede ser usada. Se puede descargar de aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## CLI de LRBA

[El CLI de LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) ayuda a generar el código fuente, compilar los *jobs*, ejecutar los tests y ejecutar el *job* en un entorno local. Solo se necesita acceso a la terminal del sistema.

## Fichero CSV

Hay que crear un fichero CSV `person-data.csv` en la carpeta `local-execution/files`.  
El contenido debe ser el siguiente:  

```csv
id,firstName,lastName,email,phone
1,Daniella,Adamec,dadamec0@delicious.com,474-596-0584
2,Rudd,Parfett,rparfett1@amazon.com,383-143-9946
3,Antoine,Franscioni,afranscioni2@apple.com,363-112-4100
4,Bennett,Pitson,bpitson3@storify.com,803-547-5449
5,Barron,Dunne,bdunne4@unicef.org,836-712-0236
6,Doti,Rubinshtein,drubinshtein5@ameblo.jp,678-634-6530
7,Suzanna,Silwood,ssilwood6@wp.com,625-196-9681
8,Leonardo,Golsworthy,lgolsworthy7@dedecms.com,996-539-6575
9,Rodrigo,Tytler,rtytler8@furl.net,417-229-7826
10,Corabel,McFeat,cmcfeat9@dailymotion.com,233-514-4082
11,Bree,Siggers,bsiggersa@godaddy.com,190-314-6522
12,Nomi,Hatz,nhatzb@usatoday.com,534-403-1270
13,Philipa,Bernon,pbernonc@bluehost.com,478-353-4348
14,Anatollo,Pennock,apennockd@devhub.com,185-196-9581
15,Neville,Meaton,nmeatone@usgs.gov,713-671-8576
16,Adaline,Mossop,amossopf@spiegel.de,556-597-3940
17,Fredric,Jeannot,fjeannotg@intel.com,270-107-9061
18,Kaleb,Zupo,kzupoh@craigslist.org,918-121-7044
19,Tabbie,Watson-Brown,twatsonbrowni@europa.eu,775-483-1697
20,Mitchel,MacNeachtain,mmacneachtainj@blogs.com,999-475-3137
```

## Mock API

La mayoría de API no son de acceso público, esto significa que no se pueden ejecutar llamadas a ellas desde un entorno local.  
De modo que para poder ejecutar este *codelab* localmente, se va a crear un *API mock* que permitirá validar las peticiones y las respuestas.  
Para ello, se va a utilizar un *Mock server*. BBVA proporciona [vBank](https://platform.bbva.com/devops-clan/documentation/bf27f9c1290d667410c0b2d0dce6b7bd/testing/tools/global-testing-tools/service-virtualization/vbank) y es el que utilizaremos en este *codelab* para este propósito.  

Para más detalles sobre como crear un *mock* con [vBank](https://platform.bbva.com/devops-clan/documentation/bf27f9c1290d667410c0b2d0dce6b7bd/testing/tools/global-testing-tools/service-virtualization/vbank) puede mirar [este *codelab*](https://platform.bbva.com/codelabs/devops-clan/DevOps%20Codelabs#/devops-clan/vBank%20Fundamentals/Introduction/).  

El archivo de configuración que se ha creado para simular la API es el siguiente:
```yaml
when:
  backend: mybackend
  method: POST
  path: /persons
  match:
    body.id: $matches(^1?[0-9]$)
then:
  - return:
      status: SUCCESS
      id: $input.body.id
---
when:
  backend: mybackend
  method: POST
  path: /persons
  match:
    body.id: $matches(^[2-9][0-9]$)
then:
  - return:
      :status: 500
      status: ERROR
      error: The id must be between 1 and 19
```
 
En esta API solo se aceptan ids entre 1 y 19. Si llegan entre 20 y 99 fallará y por encima de 99 no responderá.

# 03-ExecuteAPICalls/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En esta primera iteración se va a utilizar un *target HTTP* para enviar los datos del documento de entrada a una API.  
Por ahora, se van a ignorar las respuestas.  

## Clases a implementar

Para poder usar el *target HTTP* es necesario implementar algunas clases de la arquitectura.


### Objeto de dominio PersonData

Primero se va a crear una clase que contiene el esquema de datos que será usado en las peticiones al API.  
En este caso, para facilitar la implementación del *codelab*, el esquema esperado por la API es el mismo que el del fichero de entrada.

```java
public class PersonData {

	private String id;

	private String firstName;

	private String lastName;

	private String email;

	private String phone;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

}
```

### ISparkHttpData

Para el correcto funcionamiento del *target HTTP* es necesario implementar la interfaz `ISparkHttpData`, la cual contendrá los datos de las peticiones y respuestas dentro del *Dataset*.  
Como se puede observar, se indica que el esquema de las peticiones es `PersonData` y el de las respuestas, debido a que en esta primera iteración se van a ignorar, se indica cómo un `String`.

```java
public class SparkApiRestData implements ISparkHttpData<PersonData, String> {

    private SparkHttpRequest<PersonData> sparkHttpRequest;
    private SparkHttpResponse<String> sparkHttpResponse;
    
	public SparkApiRestData() {
	}

	public SparkApiRestData(SparkHttpRequest<PersonData> sparkHttpRequest, SparkHttpResponse<String> sparkHttpResponse) {
		super(sparkHttpRequest, sparkHttpResponse);
	}
    
    @Override
    public SparkHttpRequest<PersonData> getSparkHttpRequest() {
        return sparkHttpRequest;
    }

    @Override
    public void setSparkHttpRequest(SparkHttpRequest<PersonData> sparkHttpRequest) {
        this.sparkHttpRequest = sparkHttpRequest;
    }

    @Override
    public SparkHttpResponse<String> getSparkHttpResponse() {
        return sparkHttpResponse;
    }

    @Override
    public void setSparkHttpResponse(SparkHttpResponse<String> sparkHttpResponse) {
        this.sparkHttpResponse = sparkHttpResponse;
    }
    
}
```

## Implementación de la clase Transform

En el *transform* se van a convertir los datos de entrada en un *dataset* de tipo `SparkApiRestData`.  
Esto permite proporcionar un formato conocido al *target HTTP*, que contiene la URL, cabeceras, método HTTP, el contenido de la petición, etc.  
Para ello, primero se convierte el *dataset* de entrada en un *dataset* de tipo `PersonData`, el cual es conforme con el esquema que la API acepta.  
Luego se realiza la transformación map sobre el *dataset* para convertirlo en uno de tipo `SparkApiRestData`, que contiene los datos necesarios para ejecutar las peticiones al API.  
Es importante indicar el `ContentType` para que la arquitectura pueda serializar el contenido correctamente.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<PersonData> personDataDataset = datasetsFromRead.get("personDataSource").as(Encoders.bean(PersonData.class));

    Dataset<SparkApiRestData> sparkApiRestDataDataset = personDataDataset.map((MapFunction<PersonData, SparkApiRestData>) personData -> new SparkApiRestData(
            new SparkHttpRequest.SparkHttpRequestBuilder<PersonData>()
                    .endpoint("http://localhost:7070/persons")
                    .method(SparkHttpRequest.HttpMethod.POST)
		            .contentType(SparkHttpRequest.SparkContentType.JSON)
                    .body(personData)
                    .build(), null), Encoders.bean(SparkApiRestData.class));

    datasetsToWrite.put("personDataApiTarget", sparkApiRestDataDataset.toDF());
    return datasetsToWrite;
}
```

## Implementación del builder

### Sources

Se crea un *source* de tipo CSV para leer el fichero local `person-data.csv`.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("personDataSource")
                    .physicalName("person-data.csv")
                    .serviceName("local.logicalDataStore.batch")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

### Transform

En el método `registerTransform` se indica cuál es nuestra clase *Transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets

Se crea un *target HTTP* en el que solo se indica el alias devuelto por el *transform* y que la clase que implementa `ISparkHttpData` en este caso es `SparkApiRestData`.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Http.REST.builder()
                    .alias("personDataApiTarget")
                    .httpDataClass(SparkApiRestData.class)
                    .build())
            .build();
}
```

## Test unitarios del job

### Builder

```java
class JobHttpRequestBuilderTest {

	private JobHttpRequestBuilder jobHttpRequestBuilder;

	@BeforeEach
	void setUp() {
		this.jobHttpRequestBuilder = new JobHttpRequestBuilder();
	}

	@Test
	void registerSources_na_SourceList() {
		final SourcesList sourcesList = this.jobHttpRequestBuilder.registerSources();
		assertNotNull(sourcesList);
		assertNotNull(sourcesList.getSources());
		assertEquals(1, sourcesList.getSources().size());

		final Source source = sourcesList.getSources().get(0);
		assertNotNull(source);
		assertEquals("personDataSource", source.getAlias());
		assertEquals("person-data.csv", source.getPhysicalName());
		assertTrue(((FileCsvSource) source).getCsvConfig().isHeader());
		assertEquals(",", ((FileCsvSource) source).getCsvConfig().getDelimiter());
	}

	@Test
	void registerTransform_na_Transform() {
		final TransformConfig transformConfig = this.jobHttpRequestBuilder.registerTransform();
		assertNotNull(transformConfig);
		assertNotNull(transformConfig.getTransform());
	}

	@Test
	void registerTargets_na_TargetList() {
		final TargetsList targetsList = this.jobHttpRequestBuilder.registerTargets();
		assertNotNull(targetsList);
		assertNotNull(targetsList.getTargets());
		assertEquals(1, targetsList.getTargets().size());

		final Target target = targetsList.getTargets().get(0);
		assertNotNull(target);
		assertEquals("personDataApiTarget", target.getAlias());
	}

}
```

### Transform

Se recomienda utilizar la clase `LRBASparkTest` que proporciona la arquitectura LRBA para realizar los test del *job*.

```java
class TransformerTest extends LRBASparkTest {

	private Transformer transformer;

	@BeforeEach
	void setUp() {
		this.transformer = new Transformer();
	}

	@Test
	void transform_Output() {
		StructType schema = DataTypes.createStructType(
				new StructField[]{
						DataTypes.createStructField("id", DataTypes.StringType, false),
						DataTypes.createStructField("firstName", DataTypes.StringType, false),
						DataTypes.createStructField("lastName", DataTypes.StringType, false),
						DataTypes.createStructField("email", DataTypes.StringType, false),
						DataTypes.createStructField("phone", DataTypes.StringType, false),
				});
		Row firstRow = RowFactory.create("1", "Daniella", "Adamec", "dadamec0@delicious.com", "474-596-0584");
		Row secondRow = RowFactory.create("2", "Rudd", "Parfett", "rparfett1@amazon.com", "383-143-9946");
		Row thirdRow = RowFactory.create("3", "Antoine", "Franscioni", "afranscioni2@apple.com", "363-112-4100");

		final List<Row> listRows = Arrays.asList(firstRow, secondRow, thirdRow);

		DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
		Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

		final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("personDataSource", dataset)));

		assertNotNull(datasetMap);
		assertEquals(1, datasetMap.size());

		Dataset<SparkApiRestData> returnedDs = datasetMap.get("personDataApiTarget").as(Encoders.bean(SparkApiRestData.class));
		final List<SparkApiRestData> rows = datasetToTargetData(returnedDs, SparkApiRestData.class);

		assertEquals(3, rows.size());
		assertEquals("1", rows.get(0).getSparkHttpRequest().getBody().getId());
		assertEquals("http://localhost:7070/persons", rows.get(0).getSparkHttpRequest().getEndpoint());
		assertEquals(SparkHttpRequest.HttpMethod.POST, rows.get(0).getSparkHttpRequest().getMethod());
		assertEquals("Daniella", rows.get(0).getSparkHttpRequest().getBody().getFirstName());
		assertEquals("Adamec", rows.get(0).getSparkHttpRequest().getBody().getLastName());
		assertEquals("dadamec0@delicious.com", rows.get(0).getSparkHttpRequest().getBody().getEmail());
		assertEquals("474-596-0584", rows.get(0).getSparkHttpRequest().getBody().getPhone());
		assertEquals("rparfett1@amazon.com", rows.get(1).getSparkHttpRequest().getBody().getEmail());
		assertEquals("afranscioni2@apple.com", rows.get(2).getSparkHttpRequest().getBody().getEmail());
	}

}
```

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```

Se puede observar que la ejecución no lanza ningún error, pero eso no asegura que las peticiones al API se hayan ejecutado satisfactoriamente. Para poder validarlas hay que guardar la respuesta.

# 03-ExecuteAPICalls/04-PersistApiResponses.md
# 4. Persistir respuestas del API sin deserializar

## ¿Qué cambios se deberían hacer?

### SparkApiRestData

En la primera implementación del *job*, se indica en la clase `SparkApiRestData` que el tipo de dato de las respuestas es *String*.  
Esto significa que el conector HTTP no va a deserializar los datos, todo el contenido de la respuesta será guardado como un *String*.  
Por lo tanto, **no se debe realizar ninguna modificación en esta clase**.


```java
public class SparkApiRestData implements ISparkHttpData<PersonData, String>
```

### HTTP target

En el *target HTTP* se debe indicar el tipo de dato de la respuesta en la etiqueta `responseBodyClass`. En este caso será *String*, como ya se ha explicado en el apartado anterior.  
También se incluirá un *target* en el que se guardará el resultado de la ejecución de las peticiones HTTP. En este caso se usará un fichero Parquet.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Http.REST.builder()
                    .alias("personDataApiTarget")
                    .httpDataClass(SparkApiRestData.class)
                    .responseBodyClass(String.class)
                    .responseTarget(Target.File.Parquet.builder()
                            .alias("personDataApiTarget")
                            .serviceName("local.logicalDataStore.batch")
                            .physicalName("result.parquet")
                            .build())
                    .build())
            .build();
}
```

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```

### Analizar el resultado

Ahora, se puede observar que en el directorio `local-execution/files` hay un fichero llamado `result.parquet`, el cual su contenido es el siguiente:

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sparkHttpRequest                                                                                                                                                                                                                                                                  | sparkHttpResponse                                                                                                                                                                                                  |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {'body': {'email': 'dadamec0@delicious.com', 'firstName': 'Daniella', 'id': '1', 'lastName': 'Adamec', 'phone': '474-596-0584'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}         | {'body': '{"status":"SUCCESS","id":"1"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'rparfett1@amazon.com', 'firstName': 'Rudd', 'id': '2', 'lastName': 'Parfett', 'phone': '383-143-9946'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': '{"status":"SUCCESS","id":"2"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'afranscioni2@apple.com', 'firstName': 'Antoine', 'id': '3', 'lastName': 'Franscioni', 'phone': '363-112-4100'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}      | {'body': '{"status":"SUCCESS","id":"3"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'bpitson3@storify.com', 'firstName': 'Bennett', 'id': '4', 'lastName': 'Pitson', 'phone': '803-547-5449'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': '{"status":"SUCCESS","id":"4"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'bdunne4@unicef.org', 'firstName': 'Barron', 'id': '5', 'lastName': 'Dunne', 'phone': '836-712-0236'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}                | {'body': '{"status":"SUCCESS","id":"5"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'drubinshtein5@ameblo.jp', 'firstName': 'Doti', 'id': '6', 'lastName': 'Rubinshtein', 'phone': '678-634-6530'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}       | {'body': '{"status":"SUCCESS","id":"6"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'ssilwood6@wp.com', 'firstName': 'Suzanna', 'id': '7', 'lastName': 'Silwood', 'phone': '625-196-9681'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}               | {'body': '{"status":"SUCCESS","id":"7"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'lgolsworthy7@dedecms.com', 'firstName': 'Leonardo', 'id': '8', 'lastName': 'Golsworthy', 'phone': '996-539-6575'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}   | {'body': '{"status":"SUCCESS","id":"8"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'rtytler8@furl.net', 'firstName': 'Rodrigo', 'id': '9', 'lastName': 'Tytler', 'phone': '417-229-7826'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}               | {'body': '{"status":"SUCCESS","id":"9"}', 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                                |
| {'body': {'email': 'cmcfeat9@dailymotion.com', 'firstName': 'Corabel', 'id': '10', 'lastName': 'McFeat', 'phone': '233-514-4082'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}       | {'body': '{"status":"SUCCESS","id":"10"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'bsiggersa@godaddy.com', 'firstName': 'Bree', 'id': '11', 'lastName': 'Siggers', 'phone': '190-314-6522'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': '{"status":"SUCCESS","id":"11"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'nhatzb@usatoday.com', 'firstName': 'Nomi', 'id': '12', 'lastName': 'Hatz', 'phone': '534-403-1270'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}                 | {'body': '{"status":"SUCCESS","id":"12"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'pbernonc@bluehost.com', 'firstName': 'Philipa', 'id': '13', 'lastName': 'Bernon', 'phone': '478-353-4348'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}          | {'body': '{"status":"SUCCESS","id":"13"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'apennockd@devhub.com', 'firstName': 'Anatollo', 'id': '14', 'lastName': 'Pennock', 'phone': '185-196-9581'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}         | {'body': '{"status":"SUCCESS","id":"14"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'nmeatone@usgs.gov', 'firstName': 'Neville', 'id': '15', 'lastName': 'Meaton', 'phone': '713-671-8576'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': '{"status":"SUCCESS","id":"15"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'amossopf@spiegel.de', 'firstName': 'Adaline', 'id': '16', 'lastName': 'Mossop', 'phone': '556-597-3940'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': '{"status":"SUCCESS","id":"16"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'fjeannotg@intel.com', 'firstName': 'Fredric', 'id': '17', 'lastName': 'Jeannot', 'phone': '270-107-9061'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}           | {'body': '{"status":"SUCCESS","id":"17"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'kzupoh@craigslist.org', 'firstName': 'Kaleb', 'id': '18', 'lastName': 'Zupo', 'phone': '918-121-7044'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': '{"status":"SUCCESS","id":"18"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'twatsonbrowni@europa.eu', 'firstName': 'Tabbie', 'id': '19', 'lastName': 'Watson-Brown', 'phone': '775-483-1697'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}   | {'body': '{"status":"SUCCESS","id":"19"}', 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                               |
| {'body': {'email': 'mmacneachtainj@blogs.com', 'firstName': 'Mitchel', 'id': '20', 'lastName': 'MacNeachtain', 'phone': '999-475-3137'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'} | {'body': '{"status":"ERROR","error":"The id must be between 1 and 19"}', 'headers': [('content-length', array(['60'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 500} |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

Se puede observar que todas las peticiones se han ejecutado correctamente excepto la última, que su id es 20 y se encuentra fuera del rango permitido. 

```
{'body': '{"status":"ERROR","error":"The id must be between 1 and 19"}', 'headers': [('content-length', array(['60'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 500}
```

### Analizando el resultado como JSON

Usando *spark-shell* se ha convertido el Parquet en JSON para mostrar la estructura de la respuesta con más claridad.  
Se puede ver que en la respuesta, la etiqueta que contiene el *body* se trata como un *String*, su esquema no ha sido parseado.

```json
{"sparkHttpRequest":{"body":{"email":"dadamec0@delicious.com","firstName":"Daniella","id":"1","lastName":"Adamec","phone":"474-596-0584"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"1\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"rparfett1@amazon.com","firstName":"Rudd","id":"2","lastName":"Parfett","phone":"383-143-9946"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"2\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"afranscioni2@apple.com","firstName":"Antoine","id":"3","lastName":"Franscioni","phone":"363-112-4100"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"3\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bpitson3@storify.com","firstName":"Bennett","id":"4","lastName":"Pitson","phone":"803-547-5449"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"4\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bdunne4@unicef.org","firstName":"Barron","id":"5","lastName":"Dunne","phone":"836-712-0236"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"5\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"drubinshtein5@ameblo.jp","firstName":"Doti","id":"6","lastName":"Rubinshtein","phone":"678-634-6530"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"6\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"ssilwood6@wp.com","firstName":"Suzanna","id":"7","lastName":"Silwood","phone":"625-196-9681"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"7\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"lgolsworthy7@dedecms.com","firstName":"Leonardo","id":"8","lastName":"Golsworthy","phone":"996-539-6575"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"8\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"rtytler8@furl.net","firstName":"Rodrigo","id":"9","lastName":"Tytler","phone":"417-229-7826"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"9\"}","headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"cmcfeat9@dailymotion.com","firstName":"Corabel","id":"10","lastName":"McFeat","phone":"233-514-4082"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"10\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bsiggersa@godaddy.com","firstName":"Bree","id":"11","lastName":"Siggers","phone":"190-314-6522"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"11\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"nhatzb@usatoday.com","firstName":"Nomi","id":"12","lastName":"Hatz","phone":"534-403-1270"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"12\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"pbernonc@bluehost.com","firstName":"Philipa","id":"13","lastName":"Bernon","phone":"478-353-4348"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"13\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"apennockd@devhub.com","firstName":"Anatollo","id":"14","lastName":"Pennock","phone":"185-196-9581"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"14\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"nmeatone@usgs.gov","firstName":"Neville","id":"15","lastName":"Meaton","phone":"713-671-8576"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"15\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"amossopf@spiegel.de","firstName":"Adaline","id":"16","lastName":"Mossop","phone":"556-597-3940"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"16\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"fjeannotg@intel.com","firstName":"Fredric","id":"17","lastName":"Jeannot","phone":"270-107-9061"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"17\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"kzupoh@craigslist.org","firstName":"Kaleb","id":"18","lastName":"Zupo","phone":"918-121-7044"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"18\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"twatsonbrowni@europa.eu","firstName":"Tabbie","id":"19","lastName":"Watson-Brown","phone":"775-483-1697"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"SUCCESS\",\"id\":\"19\"}","headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"mmacneachtainj@blogs.com","firstName":"Mitchel","id":"20","lastName":"MacNeachtain","phone":"999-475-3137"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":"{\"status\":\"ERROR\",\"error\":\"The id must be between 1 and 19\"}","headers":{"content-length":["60"],"content-type":["application/json"]},"status":500}}
```

***NOTA:*** La arquitectura LRBA no da soporte sobre como usar *spark-shell*. En este ejemplo ha sido usado para respaldar la explicación.

# 03-ExecuteAPICalls/05-DeserializeApiResponsesToAnObject.md
# 5. Deserializar respuestas del API en un objeto

## ¿Qué cambios se deberían hacer?

### Clase de dominio PersonDataResponse

Primero, hay que crear una clase que contenga el esquema de la respuesta.  
La respuesta contiene un campo `id` y uno `status`. Cuando ocurre un error, también contiene un campo `error`.

```java
public class PersonDataResponse {

	private String id;

	private String status;

	private String error;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}

	public String getError() {
		return error;
	}

	public void setError(String error) {
		this.error = error;
	}
}
```

### SparkApiRestData

En la clase `SparkApiRestData` se indicará el esquema de la respuesta.  
Se debe indicar tanto en el uso de genéricos al implementar `ISparkHttpData` como en el constructor.

```java
public class SparkApiRestData implements ISparkHttpData<PersonData, PersonDataResponse> {
    
    private SparkHttpRequest<PersonData> sparkHttpRequest;
    private SparkHttpResponse<PersonDataResponse> sparkHttpResponse;
    
	public SparkApiRestData() {
	}

	public SparkApiRestData(SparkHttpRequest<PersonData> sparkHttpRequest, SparkHttpResponse<PersonDataResponse> sparkHttpResponse) {
		super(sparkHttpRequest, sparkHttpResponse);
	}

    @Override
    public SparkHttpRequest<PersonData> getSparkHttpRequest() {
        return sparkHttpRequest;
    }

    @Override
    public void setSparkHttpRequest(SparkHttpRequest<PersonData> sparkHttpRequest) {
        this.sparkHttpRequest = sparkHttpRequest;
    }

    @Override
    public SparkHttpResponse<PersonDataResponse> getSparkHttpResponse() {
        return sparkHttpResponse;
    }

    @Override
    public void setSparkHttpResponse(SparkHttpResponse<PersonDataResponse> sparkHttpResponse) {
        this.sparkHttpResponse = sparkHttpResponse;
    }
}
```

### HTTP target

Finalmente, en el *target HTTP* se indica el tipo de dato de la respuesta en el campo `responseBodyClass`.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Http.REST.builder()
                    .alias("personDataApiTarget")
                    .httpDataClass(SparkApiRestData.class)
                    .responseBodyClass(PersonDataResponse.class)
                    .responseTarget(Target.File.Parquet.builder()
                            .alias("personDataApiTarget")
                            .serviceName("local.logicalDataStore.batch")
                            .physicalName("result.parquet")
                            .build())
                    .build())
            .build();
}
```

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```

### Analizar el resultado

Ahora, se puede observar que en el directorio `local-execution/files` hay un fichero llamado `result.parquet`, el cual su contenido es el siguiente:

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sparkHttpRequest                                                                                                                                                                                                                                                                  | sparkHttpResponse                                                                                                                                                                                                               |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {'body': {'email': 'dadamec0@delicious.com', 'firstName': 'Daniella', 'id': '1', 'lastName': 'Adamec', 'phone': '474-596-0584'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}         | {'body': {'error': None, 'id': '1', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'rparfett1@amazon.com', 'firstName': 'Rudd', 'id': '2', 'lastName': 'Parfett', 'phone': '383-143-9946'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': {'error': None, 'id': '2', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'afranscioni2@apple.com', 'firstName': 'Antoine', 'id': '3', 'lastName': 'Franscioni', 'phone': '363-112-4100'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}      | {'body': {'error': None, 'id': '3', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'bpitson3@storify.com', 'firstName': 'Bennett', 'id': '4', 'lastName': 'Pitson', 'phone': '803-547-5449'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': {'error': None, 'id': '4', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'bdunne4@unicef.org', 'firstName': 'Barron', 'id': '5', 'lastName': 'Dunne', 'phone': '836-712-0236'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}                | {'body': {'error': None, 'id': '5', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'drubinshtein5@ameblo.jp', 'firstName': 'Doti', 'id': '6', 'lastName': 'Rubinshtein', 'phone': '678-634-6530'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}       | {'body': {'error': None, 'id': '6', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'ssilwood6@wp.com', 'firstName': 'Suzanna', 'id': '7', 'lastName': 'Silwood', 'phone': '625-196-9681'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}               | {'body': {'error': None, 'id': '7', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'lgolsworthy7@dedecms.com', 'firstName': 'Leonardo', 'id': '8', 'lastName': 'Golsworthy', 'phone': '996-539-6575'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}   | {'body': {'error': None, 'id': '8', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'rtytler8@furl.net', 'firstName': 'Rodrigo', 'id': '9', 'lastName': 'Tytler', 'phone': '417-229-7826'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}               | {'body': {'error': None, 'id': '9', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['29'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                             |
| {'body': {'email': 'cmcfeat9@dailymotion.com', 'firstName': 'Corabel', 'id': '10', 'lastName': 'McFeat', 'phone': '233-514-4082'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}       | {'body': {'error': None, 'id': '10', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'bsiggersa@godaddy.com', 'firstName': 'Bree', 'id': '11', 'lastName': 'Siggers', 'phone': '190-314-6522'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': {'error': None, 'id': '11', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'nhatzb@usatoday.com', 'firstName': 'Nomi', 'id': '12', 'lastName': 'Hatz', 'phone': '534-403-1270'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}                 | {'body': {'error': None, 'id': '12', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'pbernonc@bluehost.com', 'firstName': 'Philipa', 'id': '13', 'lastName': 'Bernon', 'phone': '478-353-4348'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}          | {'body': {'error': None, 'id': '13', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'apennockd@devhub.com', 'firstName': 'Anatollo', 'id': '14', 'lastName': 'Pennock', 'phone': '185-196-9581'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}         | {'body': {'error': None, 'id': '14', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'nmeatone@usgs.gov', 'firstName': 'Neville', 'id': '15', 'lastName': 'Meaton', 'phone': '713-671-8576'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': {'error': None, 'id': '15', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'amossopf@spiegel.de', 'firstName': 'Adaline', 'id': '16', 'lastName': 'Mossop', 'phone': '556-597-3940'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}            | {'body': {'error': None, 'id': '16', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'fjeannotg@intel.com', 'firstName': 'Fredric', 'id': '17', 'lastName': 'Jeannot', 'phone': '270-107-9061'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}           | {'body': {'error': None, 'id': '17', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'kzupoh@craigslist.org', 'firstName': 'Kaleb', 'id': '18', 'lastName': 'Zupo', 'phone': '918-121-7044'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}              | {'body': {'error': None, 'id': '18', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'twatsonbrowni@europa.eu', 'firstName': 'Tabbie', 'id': '19', 'lastName': 'Watson-Brown', 'phone': '775-483-1697'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'}   | {'body': {'error': None, 'id': '19', 'status': 'SUCCESS'}, 'headers': [('content-length', array(['30'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 200}                            |
| {'body': {'email': 'mmacneachtainj@blogs.com', 'firstName': 'Mitchel', 'id': '20', 'lastName': 'MacNeachtain', 'phone': '999-475-3137'}, 'endpoint': 'http://localhost:7070/persons', 'headers': [('Content-Type', array(['application/json'], dtype=object))], 'method': 'POST'} | {'body': {'error': 'The id must be between 1 and 19', 'id': None, 'status': 'ERROR'}, 'headers': [('content-length', array(['60'], dtype=object)), ('content-type', array(['application/json'], dtype=object))], 'status': 500} |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

### Analizando el resultado como JSON

Usando *spark-shell* se ha convertido el Parquet en JSON para mostrar la estructura de la respuesta con más claridad.  
Se puede ver que en la respuesta, la etiqueta que contiene el *body* ha sido parseado y ahora tiene estructura.

```json
{"sparkHttpRequest":{"body":{"email":"dadamec0@delicious.com","firstName":"Daniella","id":"1","lastName":"Adamec","phone":"474-596-0584"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"1","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"rparfett1@amazon.com","firstName":"Rudd","id":"2","lastName":"Parfett","phone":"383-143-9946"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"2","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"afranscioni2@apple.com","firstName":"Antoine","id":"3","lastName":"Franscioni","phone":"363-112-4100"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"3","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bpitson3@storify.com","firstName":"Bennett","id":"4","lastName":"Pitson","phone":"803-547-5449"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"4","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bdunne4@unicef.org","firstName":"Barron","id":"5","lastName":"Dunne","phone":"836-712-0236"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"5","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"drubinshtein5@ameblo.jp","firstName":"Doti","id":"6","lastName":"Rubinshtein","phone":"678-634-6530"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"6","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"ssilwood6@wp.com","firstName":"Suzanna","id":"7","lastName":"Silwood","phone":"625-196-9681"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"7","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"lgolsworthy7@dedecms.com","firstName":"Leonardo","id":"8","lastName":"Golsworthy","phone":"996-539-6575"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"8","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"rtytler8@furl.net","firstName":"Rodrigo","id":"9","lastName":"Tytler","phone":"417-229-7826"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"9","status":"SUCCESS"},"headers":{"content-length":["29"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"cmcfeat9@dailymotion.com","firstName":"Corabel","id":"10","lastName":"McFeat","phone":"233-514-4082"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"10","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"bsiggersa@godaddy.com","firstName":"Bree","id":"11","lastName":"Siggers","phone":"190-314-6522"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"11","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"nhatzb@usatoday.com","firstName":"Nomi","id":"12","lastName":"Hatz","phone":"534-403-1270"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"12","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"pbernonc@bluehost.com","firstName":"Philipa","id":"13","lastName":"Bernon","phone":"478-353-4348"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"13","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"apennockd@devhub.com","firstName":"Anatollo","id":"14","lastName":"Pennock","phone":"185-196-9581"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"14","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"nmeatone@usgs.gov","firstName":"Neville","id":"15","lastName":"Meaton","phone":"713-671-8576"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"15","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"amossopf@spiegel.de","firstName":"Adaline","id":"16","lastName":"Mossop","phone":"556-597-3940"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"16","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"fjeannotg@intel.com","firstName":"Fredric","id":"17","lastName":"Jeannot","phone":"270-107-9061"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"17","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"kzupoh@craigslist.org","firstName":"Kaleb","id":"18","lastName":"Zupo","phone":"918-121-7044"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"18","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"twatsonbrowni@europa.eu","firstName":"Tabbie","id":"19","lastName":"Watson-Brown","phone":"775-483-1697"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"id":"19","status":"SUCCESS"},"headers":{"content-length":["30"],"content-type":["application/json"]},"status":200}}
{"sparkHttpRequest":{"body":{"email":"mmacneachtainj@blogs.com","firstName":"Mitchel","id":"20","lastName":"MacNeachtain","phone":"999-475-3137"},"endpoint":"http://localhost:7070/persons","headers":{"Content-Type":["application/json"]},"method":"POST"},"sparkHttpResponse":{"body":{"error":"The id must be between 1 and 19","status":"ERROR"},"headers":{"content-length":["60"],"content-type":["application/json"]},"status":500}}
```

***NOTA:*** La arquitectura LRBA no da soporte sobre como usar *spark-shell*. En este ejemplo ha sido usado para respaldar la explicación.  

# 04-ExecuteApiCallsWithXML/01-Introduction.md
# 1. Introduction

**API** es el acrónimo de **Application Programming Interface**, que es un intermediario de *software* que **permite que dos aplicaciones hablen entre sí**.
Cada vez que se utiliza una *app* como BBVA, se envía un mensaje instantáneo o se consulta el tiempo online, se está utilizando una API.

LRBA permite ejecutar llamadas API utilizando la funcionalidad y el paralelismo de Spark.  

En este ejemplo vamos a ver cómo se puede utilizar el target HTTP para hacer una solicitud a una API que sólo acepta XML en una ejecución local.  
El propósito de este *codelab* es entender cómo utilizar el Conector HTTP para comunicarse con una API que acepte otro contenido que no sea JSON.

# 04-ExecuteApiCallsWithXML/02-Prerequisites.md
# 2. Prerequisites

## Java IDEs

Eclipse es un IDE de código abierto. Se puede descargar de aquí: [Download Eclipse](https://www.eclipse.org/downloads/packages/).
IntelliJ IDEA es otro IDE que recomendamos. Tiene una versión gratuita que se puede descargar aquí: [IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI

El [LRBA command line interface (CLI)](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) ayuda a generar los archivos base, construir el *job*, probarlo y ejecutarlo en un entorno local. Lo único que se necesita es acceso a la terminal del sistema.

## CSV file

Se usará el fichero CSV `person-data.csv` que estará en el directorio `local-execution/files`.  
El contenido es el siguiente:

```csv
id,firstName,lastName,email,phone
1,Daniella,Adamec,dadamec0@delicious.com,474-596-0584
2,Rudd,Parfett,rparfett1@amazon.com,383-143-9946
3,Antoine,Franscioni,afranscioni2@apple.com,363-112-4100
4,Bennett,Pitson,bpitson3@storify.com,803-547-5449
5,Barron,Dunne,bdunne4@unicef.org,836-712-0236
6,Doti,Rubinshtein,drubinshtein5@ameblo.jp,678-634-6530
7,Suzanna,Silwood,ssilwood6@wp.com,625-196-9681
8,Leonardo,Golsworthy,lgolsworthy7@dedecms.com,996-539-6575
9,Rodrigo,Tytler,rtytler8@furl.net,417-229-7826
10,Corabel,McFeat,cmcfeat9@dailymotion.com,233-514-4082
11,Bree,Siggers,bsiggersa@godaddy.com,190-314-6522
12,Nomi,Hatz,nhatzb@usatoday.com,534-403-1270
13,Philipa,Bernon,pbernonc@bluehost.com,478-353-4348
14,Anatollo,Pennock,apennockd@devhub.com,185-196-9581
15,Neville,Meaton,nmeatone@usgs.gov,713-671-8576
16,Adaline,Mossop,amossopf@spiegel.de,556-597-3940
17,Fredric,Jeannot,fjeannotg@intel.com,270-107-9061
18,Kaleb,Zupo,kzupoh@craigslist.org,918-121-7044
19,Tabbie,Watson-Brown,twatsonbrowni@europa.eu,775-483-1697
20,Mitchel,MacNeachtain,mmacneachtainj@blogs.com,999-475-3137
```

## Mock API

La mayoría de las API no serán de acceso público. Eso significa que los desarrolladores no pueden ejecutar llamadas reales desde su entorno local.
Para ejecutar el trabajo localmente, es posible crear una imitación local de la API con el fin de validar las peticiones y respuestas.
Para ello, es posible utilizar un Mock Server. Para ello BBVA proporciona [vBank](https://platform.bbva.com/devops-clan/documentation/bf27f9c1290d667410c0b2d0dce6b7bd/testing/tools/global-testing-tools/service-virtualization/vbank).

Para mas detalles sobre como crear un *mock* con [vBank](https://platform.bbva.com/devops-clan/documentation/bf27f9c1290d667410c0b2d0dce6b7bd/testing/tools/global-testing-tools/service-virtualization/vbank) have a look at [this codelab](https://platform.bbva.com/codelabs/devops-clan/DevOps%20Codelabs#/devops-clan/vBank%20Fundamentals/Introduction/).

El fichero de configuración que tenemos que usar para el *mock* de la API es el siguiente:
```yaml
when:
  backend: mybackend2
  method: POST
  path: /persons
  match:
    body.person.id: $matches(^1?[0-9]$)
then:
  - return:
      :headers:
        content-type: application/xml
      :body:
        person-response:
          status: SUCCESS
          id: $input.body.person.id
---
when:
  backend: mybackend2
  method: POST
  path: /persons
  match:
    body.person.id: $matches(^[2-9][0-9]$)
then:
  - return:
      :status: 500
      :headers:
        content-type: application/xml
      :body:
        person-response:
          status: ERROR
          error: The id must be between 1 and 19
```

En este mock del API sólo se aceptan ids entre 1 y 19. Entre 20 y 99 fallará. Por encima de 99 no responderá.


# 04-ExecuteApiCallsWithXML/03-Example.md
# 3. Ejemplo

En este ejemplo, la API espera recibir una petición XML que cumpla el siguiente esquema.  

```xml
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="person">
    <xs:complexType>
      <xs:sequence>
        <xs:element type="xs:byte" name="id"/>
        <xs:element type="xs:string" name="firstName"/>
        <xs:element type="xs:string" name="lastName"/>
        <xs:element type="xs:string" name="email"/>
        <xs:element type="xs:string" name="phone"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

## Implementación de clases

Para utilizar la API, es necesario extender algunas clases de arquitectura.

### PersonData

En primer lugar vamos a crear una clase que contenga el esquema de datos que se utilizará en las peticiones a la API.  
En este caso, para facilitar la implementación del *codelab*, el esquema esperado por la API coincide con el fichero de entrada.

```java
public class PersonData {

	private String id;

	private String firstName;

	private String lastName;

	private String email;

	private String phone;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

}
```

### ISparkHttpData

Por último, el desarrollador debe implementar la interfaz `ISparkHttpData` que contendrá los datos de petición y respuesta dentro del *Dataset*.  
Indicamos que **el esquema de nuestras peticiones y respuestas es `String`.**.  
De esta forma, la arquitectura sabe que **no tiene que parsearlos** y **utilizará el contenido del cuerpo directamente**, tanto en las peticiones como en las respuestas.

```java
public class SparkApiRestData implements ISparkHttpData<String, String> {

    private SparkHttpRequest<String> sparkHttpRequest;
    private SparkHttpResponse<String> sparkHttpResponse;

    public SparkApiRestData() {
    }

    public SparkApiRestData(SparkHttpRequest<String> sparkHttpRequest, SparkHttpResponse<String> sparkHttpResponse) {
        super(sparkHttpRequest, sparkHttpResponse);
    }

    @Override
    public SparkHttpRequest<String> getSparkHttpRequest() {
        return sparkHttpRequest;
    }

    @Override
    public void setSparkHttpRequest(SparkHttpRequest<String> sparkHttpRequest) {
        this.sparkHttpRequest = sparkHttpRequest;
    }

    @Override
    public SparkHttpResponse<String> getSparkHttpResponse() {
        return sparkHttpResponse;
    }

    @Override
    public void setSparkHttpResponse(SparkHttpResponse<String> sparkHttpResponse) {
        this.sparkHttpResponse = sparkHttpResponse;
    }
}
```

## Declarar el *Transform*

En el transform debemos convertir nuestros datos de entrada a un conjunto de datos `SparkApiRestData`.  
Esto nos permite proporcionar un formato conocido al HTTP *target*, que contiene la URL, cabeceras, método, cuerpo, etc. de nuestras peticiones.  

En primer lugar, convertimos nuestro *dataset* de entrada en un *dataset* de tipo `PersonData`, que es el tipo de datos que acepta la API y que posteriormente convertiremos a XML.  
Después aplicamos un `mapPartitions` sobre este *dataset* para convertirlo en uno de tipo `SparkApiRestData` que contiene todos los datos necesarios para ejecutar las peticiones. Ten en cuenta que los objetos de tipo `PersonData` se convierten en un `String` en formato XML.    

La inicialización de XStream es muy lenta, pero es necesario hacerla dentro de la función porque no es serializable y no se puede enviar a los *executors*.  
Se ha utilizado `mapPartitions` en lugar de `map`, ya que un `mapPartitions` se ejecuta una vez por partición y un `map` se ejecuta una vez por registro.   
Usando `mapPartitions` sólo se inicializa el XStream una vez por partición y por tanto se obtiene un mejor rendimiento del proceso.  

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<PersonData> personDataDataset = datasetsFromRead.get("personDataSource").as(Encoders.bean(PersonData.class));

    Dataset<SparkApiRestData> sparkApiRestDataDataset = personDataDataset.mapPartitions((MapPartitionsFunction<PersonData, SparkApiRestData>) it -> {
        List<SparkApiRestData> result = new ArrayList<>();
        XStream xstream = new XStream();
        xstream.alias("person", PersonData.class);
        while (it.hasNext()) {
            result.add(new SparkApiRestData(
                    new SparkHttpRequest.SparkHttpRequestBuilder<String>()
                            .endpoint("http://localhost:7071/persons")
                            .method(SparkHttpRequest.HttpMethod.POST)
                            .header("Content-Type", "application/xml")
                            .body(xstream.toXML(it.next()))
                            .build(), null));
        }
        return result.iterator();
    }, Encoders.bean(SparkApiRestData.class));

    datasetsToWrite.put("personDataApiTarget", sparkApiRestDataDataset.toDF());
    return datasetsToWrite;
}
```

## Declarar el *Builder*

### Sources

Creamos un *source* de tipo CSV para que lea el fichero local `person-data.csv`.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("personDataSource")
                    .physicalName("person-data.csv")
                    .serviceName("local.logicalDataStore.batch")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

### Transform

En el *registerTransform* hacemos referencia a nuestra clase *Transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets

Creamos *HTTP target* al que indicamos:
- El alias que devuelve el "transform".
- La clase que implementa *ISparkHttpData*, en nuestro caso *SparkApiRestData*.
- El tipo de datos de la respuesta en el campo `responseBodyClass`. En nuestro caso será `String`. La respuesta de la API está en formato XML y la deserialización de este formato a un objeto no está soportada de forma nativa por la arquitectura.
- El *target* donde se guardará el resultado. En este caso lo haremos en un fichero Parquet.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Http.REST.builder()
                    .alias("personDataApiTarget")
                    .httpDataClass(SparkApiRestData.class)
                    .responseBodyClass(String.class)
                    .responseTarget(Target.File.Parquet.builder()
                            .alias("personDataApiTarget")
                            .serviceName("local.logicalDataStore.batch")
                            .physicalName("result.parquet")
                            .build())
                    .build())
            .build();
}
```

## Tests unitarios del job

### Builder

```java
class JobHttpXmlBuilderTest {

	private JobHttpXmlBuilder jobHttpXmlBuilder;

	@BeforeEach
	void setUp() {
		this.jobHttpXmlBuilder = new JobHttpXmlBuilder();
	}

	@Test
	void registerSources_na_SourceList() {
		final SourcesList sourcesList = this.jobHttpXmlBuilder.registerSources();
		assertNotNull(sourcesList);
		assertNotNull(sourcesList.getSources());
		assertEquals(1, sourcesList.getSources().size());

		final Source source = sourcesList.getSources().get(0);
		assertNotNull(source);
		assertEquals("personDataSource", source.getAlias());
		assertEquals("person-data.csv", source.getPhysicalName());
		assertTrue(((FileCsvSource) source).getCsvConfig().isHeader());
		assertEquals(",", ((FileCsvSource) source).getCsvConfig().getDelimiter());
	}

	@Test
	void registerTransform_na_Transform() {
		final TransformConfig transformConfig = this.jobHttpXmlBuilder.registerTransform();
		assertNotNull(transformConfig);
		assertNotNull(transformConfig.getTransform());
	}

	@Test
	void registerTargets_na_TargetList() {
		final TargetsList targetsList = this.jobHttpXmlBuilder.registerTargets();
		assertNotNull(targetsList);
		assertNotNull(targetsList.getTargets());
		assertEquals(1, targetsList.getTargets().size());

		final Target target = targetsList.getTargets().get(0);
		assertNotNull(target);
		assertEquals("personDataApiTarget", target.getAlias());
	}

}
```

### Transform

Recomendamos utilizar las clase de utilidad `LRBASparkTest` que proporciona LRBA para probar el *job*.

```java
class TransformerTest extends LRBASparkTest {

	private Transformer transformer;

	@BeforeEach
	void setUp() {
		this.transformer = new Transformer();
	}

	@Test
	void transform_Output() {
		StructType schema = DataTypes.createStructType(
				new StructField[]{
						DataTypes.createStructField("id", DataTypes.StringType, false),
						DataTypes.createStructField("firstName", DataTypes.StringType, false),
						DataTypes.createStructField("lastName", DataTypes.StringType, false),
						DataTypes.createStructField("email", DataTypes.StringType, false),
						DataTypes.createStructField("phone", DataTypes.StringType, false),
				});
		Row firstRow = RowFactory.create("1", "Daniella", "Adamec", "dadamec0@delicious.com", "474-596-0584");
		Row secondRow = RowFactory.create("2", "Rudd", "Parfett", "rparfett1@amazon.com", "383-143-9946");
		Row thirdRow = RowFactory.create("3", "Antoine", "Franscioni", "afranscioni2@apple.com", "363-112-4100");

		final List<Row> listRows = Arrays.asList(firstRow, secondRow, thirdRow);

		DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
		Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

		final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("personDataSource", dataset)));

		assertNotNull(datasetMap);
		assertEquals(1, datasetMap.size());

		Dataset<SparkApiRestData> returnedDs = datasetMap.get("personDataApiTarget").as(Encoders.bean(SparkApiRestData.class));
		final List<SparkApiRestData> rows = datasetToTargetData(returnedDs, SparkApiRestData.class);

		assertEquals(3, rows.size());
		assertEquals("http://localhost:7071/persons", rows.get(0).getSparkHttpRequest().getEndpoint());
		assertEquals(SparkHttpRequest.HttpMethod.POST, rows.get(0).getSparkHttpRequest().getMethod());
		assertEquals("<person>\n  <id>1</id>\n  <firstName>Daniella</firstName>\n  <lastName>Adamec</lastName>\n  <email>dadamec0@delicious.com</email>\n  <phone>474-596-0584</phone>\n</person>",
				rows.get(0).getSparkHttpRequest().getBody());
		assertEquals("<person>\n  <id>2</id>\n  <firstName>Rudd</firstName>\n  <lastName>Parfett</lastName>\n  <email>rparfett1@amazon.com</email>\n  <phone>383-143-9946</phone>\n</person>",
				rows.get(1).getSparkHttpRequest().getBody());
		assertEquals("<person>\n  <id>3</id>\n  <firstName>Antoine</firstName>\n  <lastName>Franscioni</lastName>\n  <email>afranscioni2@apple.com</email>\n  <phone>363-112-4100</phone>\n</person>",
				rows.get(2).getSparkHttpRequest().getBody());
	}

}
```

## Ejecutar el job en local

Ejecutamos el *job* usando el CLI de LRBA.

```bash
lrba run
```

### Analizar el resultado

Observamos que en el directorio `local-execution/files` hay un archivo llamado `result.parquet`.  
Revisamos su contenido:  

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sparkHttpRequest                                                                                                                                                                                                                                                                                                                        | sparkHttpResponse                                                                                                                                                                                                                                             |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {'body': '<person>\n  <id>1</id>\n  <firstName>Daniella</firstName>\n  <lastName>Adamec</lastName>\n  <email>dadamec0@delicious.com</email>\n  <phone>474-596-0584</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}         | {'body': '<person-response><id>1</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>2</id>\n  <firstName>Rudd</firstName>\n  <lastName>Parfett</lastName>\n  <email>rparfett1@amazon.com</email>\n  <phone>383-143-9946</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}              | {'body': '<person-response><id>2</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>3</id>\n  <firstName>Antoine</firstName>\n  <lastName>Franscioni</lastName>\n  <email>afranscioni2@apple.com</email>\n  <phone>363-112-4100</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}      | {'body': '<person-response><id>3</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>4</id>\n  <firstName>Bennett</firstName>\n  <lastName>Pitson</lastName>\n  <email>bpitson3@storify.com</email>\n  <phone>803-547-5449</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}            | {'body': '<person-response><id>4</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>5</id>\n  <firstName>Barron</firstName>\n  <lastName>Dunne</lastName>\n  <email>bdunne4@unicef.org</email>\n  <phone>836-712-0236</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}                | {'body': '<person-response><id>5</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>6</id>\n  <firstName>Doti</firstName>\n  <lastName>Rubinshtein</lastName>\n  <email>drubinshtein5@ameblo.jp</email>\n  <phone>678-634-6530</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}       | {'body': '<person-response><id>6</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>7</id>\n  <firstName>Suzanna</firstName>\n  <lastName>Silwood</lastName>\n  <email>ssilwood6@wp.com</email>\n  <phone>625-196-9681</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}               | {'body': '<person-response><id>7</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>8</id>\n  <firstName>Leonardo</firstName>\n  <lastName>Golsworthy</lastName>\n  <email>lgolsworthy7@dedecms.com</email>\n  <phone>996-539-6575</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}   | {'body': '<person-response><id>8</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>9</id>\n  <firstName>Rodrigo</firstName>\n  <lastName>Tytler</lastName>\n  <email>rtytler8@furl.net</email>\n  <phone>417-229-7826</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}               | {'body': '<person-response><id>9</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['69'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                    |
| {'body': '<person>\n  <id>10</id>\n  <firstName>Corabel</firstName>\n  <lastName>McFeat</lastName>\n  <email>cmcfeat9@dailymotion.com</email>\n  <phone>233-514-4082</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}       | {'body': '<person-response><id>10</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>11</id>\n  <firstName>Bree</firstName>\n  <lastName>Siggers</lastName>\n  <email>bsiggersa@godaddy.com</email>\n  <phone>190-314-6522</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}            | {'body': '<person-response><id>11</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>12</id>\n  <firstName>Nomi</firstName>\n  <lastName>Hatz</lastName>\n  <email>nhatzb@usatoday.com</email>\n  <phone>534-403-1270</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}                 | {'body': '<person-response><id>12</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>13</id>\n  <firstName>Philipa</firstName>\n  <lastName>Bernon</lastName>\n  <email>pbernonc@bluehost.com</email>\n  <phone>478-353-4348</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}          | {'body': '<person-response><id>13</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>14</id>\n  <firstName>Anatollo</firstName>\n  <lastName>Pennock</lastName>\n  <email>apennockd@devhub.com</email>\n  <phone>185-196-9581</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}         | {'body': '<person-response><id>14</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>15</id>\n  <firstName>Neville</firstName>\n  <lastName>Meaton</lastName>\n  <email>nmeatone@usgs.gov</email>\n  <phone>713-671-8576</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}              | {'body': '<person-response><id>15</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>16</id>\n  <firstName>Adaline</firstName>\n  <lastName>Mossop</lastName>\n  <email>amossopf@spiegel.de</email>\n  <phone>556-597-3940</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}            | {'body': '<person-response><id>16</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>17</id>\n  <firstName>Fredric</firstName>\n  <lastName>Jeannot</lastName>\n  <email>fjeannotg@intel.com</email>\n  <phone>270-107-9061</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}           | {'body': '<person-response><id>17</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>18</id>\n  <firstName>Kaleb</firstName>\n  <lastName>Zupo</lastName>\n  <email>kzupoh@craigslist.org</email>\n  <phone>918-121-7044</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}              | {'body': '<person-response><id>18</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>19</id>\n  <firstName>Tabbie</firstName>\n  <lastName>Watson-Brown</lastName>\n  <email>twatsonbrowni@europa.eu</email>\n  <phone>775-483-1697</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'}   | {'body': '<person-response><id>19</id><status>SUCCESS</status></person-response>', 'headers': [('content-length', array(['70'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 200}                                   |
| {'body': '<person>\n  <id>20</id>\n  <firstName>Mitchel</firstName>\n  <lastName>MacNeachtain</lastName>\n  <email>mmacneachtainj@blogs.com</email>\n  <phone>999-475-3137</phone>\n</person>', 'endpoint': 'http://localhost:7071/persons', 'headers': [('Content-Type', array(['application/xml'], dtype=object))], 'method': 'POST'} | {'body': '<person-response><error>The id must be between 1 and 19</error><status>ERROR</status></person-response>', 'headers': [('content-length', array(['103'], dtype=object)), ('content-type', array(['application/xml'], dtype=object))], 'status': 500} |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```
Observamos que tanto las peticiones como las respuestas están en formato XML.  
También vemos que todas las peticiones se han ejecutado correctamente excepto la última, que el id es 20, y está fuera del rango permitido.  

```xml
<person-response><error>The id must be between 1 and 19</error><status>ERROR</status></person-response>
```

# 05-ExecuteApiCallsWithAuthentication/01-Introduction.md
# 1. Introducción

**API** es el acrónimo de **Application Programming Interface**. Actúa de intermediario entre dos aplicaciones para se puedan comunicar entre si.
Cada vez que se utiliza una aplicación como BBVA, se envía un mensaje o se consulta información en tiempo real, se está utilizando una API.

LRBA permite ejecutar llamadas al API usando la funcionalidad y paralelismo de Spark.

En este *codelab* vas a poder aprender como ejecutar una llamada contra un API que requiere de autenticación.
El propósito de este *codelab* no es enseñar un caso de uso real, aun así, se demuestra como ejecutar llamadas contra el API que requieren autenticación.

Si es la primera vez usando el conector HTTP, recomendamos encarecidamente que consulte el *codelab*: [Execute API calls](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Ejecutar%20peticiones%20HTTP%20%28ESP%29/Introduction/).  


# 05-ExecuteApiCallsWithAuthentication/02-Prerequisites.md
# 2. Prerrequisitos

## IDEs de Java

Eclipse es un IDE código abierto. Se puede descargar de aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).  
IntelliJ IDEA es otro IDE, con una versión gratuita que puede ser usada. Se puede descargar de aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## CLI de LRBA

[El CLI de LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) ayuda a generar el código fuente, compilar los *jobs*, ejecutar los tests y ejecutar el *job* en un entorno local.  
Solo se necesita acceso a la terminal del sistema.


# 05-ExecuteApiCallsWithAuthentication/03-AuthenticationWitMTls.md
# 3. ¿Como implementar un *job* que usa Autenticación Mutual TLS?

Como veremos en el siguiente ejemplo, la implementación de un *job* es exactamente la misma que en el caso de un *job* que utiliza el Conector HTTP sin autenticación.
El único cambio es indicar la configuración de autenticación mTLS en el *Target* HTTP.


## Requisitos

En este ejemplo, el *job* espera recibir la siguiente entrada:

```csv
id,firstName,lastName,email,phone
1,Daniella,Adamec,dadamec0@delicious.com,474-596-0584
2,Rudd,Parfett,rparfett1@amazon.com,383-143-9946
3,Antoine,Franscioni,afranscioni2@apple.com,363-112-4100
4,Bennett,Pitson,bpitson3@storify.com,803-547-5449
5,Barron,Dunne,bdunne4@unicef.org,836-712-0236
```

## Implementación de clases

Para usar el *Target* HTTP, es necesario extender algunas clases de arquitectura.

### PersonData

Primero, vamos a crear una clase que contenga el esquema de datos que se usará en las peticiones al API.
En este caso, para facilitar la implementación del *codelab*, el esquema esperado por la API coincide con el archivo de entrada.

```java
public class PersonData {

	private String id;

	private String firstName;

	private String lastName;

	private String email;

	private String phone;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

}
```

### ISparkHttpData

Finalmente, el desarrollador debe implementar la interfaz `ISparkHttpData` que contendrá datos de la petición y la respuesta dentro del *dataset*.
Indicamos que el esquema de nuestras solicitudes es `PersonData` y la respuesta es `String`. De esta forma, la arquitectura sabe que **no tiene que analizar la respuesta** y **utilizará el contenido del *body* directamente**.


```java
public class SparkApiRestData implements ISparkHttpData<PersonData, String> {

    private SparkHttpRequest<PersonData> sparkHttpRequest;
    private SparkHttpResponse<String> sparkHttpResponse;

    public SparkApiRestData() {
    }

    public SparkApiRestData(SparkHttpRequest<PersonData> sparkHttpRequest, SparkHttpResponse<String> sparkHttpResponse) {
        super(sparkHttpRequest, sparkHttpResponse);
    }

    @Override
    public SparkHttpRequest<PersonData> getSparkHttpRequest() {
        return sparkHttpRequest;
    }

    @Override
    public void setSparkHttpRequest(SparkHttpRequest<PersonData> sparkHttpRequest) {
        this.sparkHttpRequest = sparkHttpRequest;
    }

    @Override
    public SparkHttpResponse<String> getSparkHttpResponse() {
        return sparkHttpResponse;
    }

    @Override
    public void setSparkHttpResponse(SparkHttpResponse<String> sparkHttpResponse) {
        this.sparkHttpResponse = sparkHttpResponse;
    }
}
```

## Declarar Transform

En el *Transform* convertiremos la entrada en un *dataset* `SparkApiRestData`.
Esto nos permite dar un formato conocido al *Target* HTTP, que contiene la URL, los *headers*, el método, *body*, etc. de nuestra petición.
Primero, convertimos el *dataset* de entrada en un *dataset* de tipo `PersonData`, que es el tipo de dato que el API acepta.
Entonces aplicamos un map sobre el *dataset* para convertirlo en uno de tipo `SparkApiRestData` que contenga todos los datos necesarios para ejecutar la petición.
Es importante indicar el *ContentType* para que la arquitectura pueda serializar el *body* correctamente.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<PersonData> personDataDataset = datasetsFromRead.get("personDataSource").as(Encoders.bean(PersonData.class));

    Dataset<SparkApiRestData> sparkApiRestDataDataset = personDataDataset.map((MapFunction<PersonData, SparkApiRestData>) personData -> new SparkApiRestData(
            new SparkHttpRequest.SparkHttpRequestBuilder<PersonData>()
                    .endpoint("https://fake-endpoint")
                    .method(SparkHttpRequest.HttpMethod.POST)
		            .contentType(SparkHttpRequest.SparkContentType.JSON)
                    .body(personData)
                    .build(), null), Encoders.bean(SparkApiRestData.class));
    datasetsToWrite.put("dataPersonApiTarget", sparkApiRestDataDataset.toDF());
    return datasetsToWrite;
}
```

## Declarar builder

### Sources

Podemos crear un *Source* de tipo File.CSV para leer el fichero `person-data.csv`.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("personDataSource")
                    .physicalName("person-data.csv")
                    .serviceName("bts.{{UUAA}}.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

### Transform

En el *registerTransform* indicamos nuestra clase *Transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets

Creamos un *Target* HTTP en el que indicamos:
- El alias que propagaremos al *Transform*.
- Nuestra clase que implementa *ISparkHttpData*, en nuestro caso, *SparkApiRestData*.
- El tipo de dato de la Response en el campo `responseBodyClass`. En nuestro caso será `String`.
- El *Target* en el que se guardará el resultado. En este caso, lo haremos en un fichero Parquet.  
- El método de autenticación. La clave del *bot* debe ser **EXACTAMENTE** el alias que se indicó en el momento de solicitar el certificado.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Http.REST.builder()
                    .alias("dataPersonApiTarget")
                    .authentication(Authentication.MTLS.builder()
                            .botKey("bot-test")
                            .build())
                    .httpDataClass(SparkApiRestData.class)
                    .responseBodyClass(String.class)
                    .responseTarget(Target.File.Parquet.builder()
                            .alias("dataPersonApiTarget")
                            .physicalName("mtls-responses.parquet")
                            .serviceName("bts.{{UUAA}}.BATCH")
                            .build())
                    .build())
            .build();
}
```

## Test Unitarios para el Job

### Builder

```java
class JobMutualTlsTestBuilderTest {

    private JobMutualTlsTestBuilder jobMutualTlsTestBuilder;

    @BeforeEach
    void setUp() {
        this.jobMutualTlsTestBuilder = new JobMutualTlsTestBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobMutualTlsTestBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("personDataSource", source.getAlias());
        assertEquals("person-data.csv", source.getPhysicalName());
        assertEquals("bts.{{UUAA}}.BATCH", source.getServiceName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobMutualTlsTestBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobMutualTlsTestBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("dataPersonApiTarget", target.getAlias());
        assertEquals(SparkApiRestData.class, ((HttpRESTTarget)target).getHttpDataClass());
        assertEquals(String.class, ((HttpRESTTarget)target).getResponseBodyClass());
        assertEquals("bot-test", ((MTLSAuthentication)((HttpRESTTarget)target).getAuthentication()).getBotKey());
    }

}
```

### Transform

Recomendamos encarecidamente usar la clase de utilidades `LRBASparkTest` que provee la arquitectura para testear los *jobs*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
               new StructField[]{
                         DataTypes.createStructField("id", DataTypes.StringType, false),
                         DataTypes.createStructField("firstName", DataTypes.StringType, false),
                         DataTypes.createStructField("lastName", DataTypes.StringType, false),
                         DataTypes.createStructField("email", DataTypes.StringType, false),
		               DataTypes.createStructField("phone", DataTypes.StringType, false),
               });
        Row firstRow = RowFactory.create("1", "Daniella", "Adamec", "dadamec0@delicious.com", "474-596-0584");
        Row secondRow = RowFactory.create("2", "Rudd", "Parfett", "rparfett1@amazon.com", "383-143-9946");
        Row thirdRow = RowFactory.create("3", "Antoine", "Franscioni", "afranscioni2@apple.com", "363-112-4100");

        final List<Row> listRows = Arrays.asList(firstRow, secondRow, thirdRow);

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

        final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("personDataSource", dataset)));

        assertNotNull(datasetMap);
        assertEquals(1, datasetMap.size());

        Dataset<SparkApiRestData> returnedDs = datasetMap.get("dataPersonApiTarget").as(Encoders.bean(SparkApiRestData.class));
        final List<SparkApiRestData> rows = datasetToTargetData(returnedDs, SparkApiRestData.class);

        assertEquals(3, rows.size());
	    assertEquals("1", rows.get(0).getSparkHttpRequest().getBody().getId());
	    assertEquals("https://fake-endpoint", rows.get(0).getSparkHttpRequest().getEndpoint());
	    assertEquals(SparkHttpRequest.HttpMethod.POST, rows.get(0).getSparkHttpRequest().getMethod());
        assertEquals("dadamec0@delicious.com", rows.get(0).getSparkHttpRequest().getBody().getEmail());
        assertEquals("rparfett1@amazon.com", rows.get(1).getSparkHttpRequest().getBody().getEmail());
        assertEquals("afranscioni2@apple.com", rows.get(2).getSparkHttpRequest().getBody().getEmail());
    }

}
```

## Ejecutar el *job* en el clúster

En este caso vamos a ejecutar solo el *job* en el cluster. Para ello, necesitamos desplegar el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

## Comprobar la salida del *job*

Especificamos en el campo `responseTarget` el fichero `mtls-responses.parquet`. Para ello, debemos usar el servicio [BTS Visor](../../developerexperience/06-BTSVisor.md) para verificar el contenido de nuestro fichero.

# 05-ExecuteApiCallsWithAuthentication/04-AuthenticationWithOAuth.md
# 4. ¿Como implementar un *job* que usa Autenticación OAuth?

## Introducción

En este ejemplo vamos a programar un *job* que ejecute las siguientes operaciones:

1. Leer un fichero de entrada con correos electrónicos:
    ```csv
    userId,email
    4f6645e3-5d80-4852-ba33-b826c1db9e7d,test@bbva.com
    42ab5822-0574-4983-a9a9-a6704ff05853,test+1@bbva.com
    ```

2. Transformar el fichero de entrada en llamadas HTTP

3. Usar un *Target.HTTP* para ejecutar peticiones HTTP y guardar el resultado en un fichero Parquet.

## Requisitos

Para ejecutar este código, necesitamos tener credenciales válidas contra el *Notification Manager API* en el *Vault*. Para más detalles, echar un vistazo a [Primeros pasos con el *Notification Manager*](https://platform.bbva.com/en-us/developers/notifications-manager/documentation/getting-started)

## Implementación de clases

Para usar el *Target.HTTP*, es necesario extender algunas clases de arquitectura. Como el *Notification Manager* usa *OAuth*, también necesitamos extender de estas clases.

### SparkOAuthRequest

La autenticación con el *Server OAuth* se realiza a través de autenticación *Basic*, por tanto, no es necesario especificar los atributos `ClientId` y `ClientSecret`. Si este fuera el caso, el desarrollador debería sobreescribir los valores `cIdAttrName` y `cSecretAttrName`.

**IMPORTANTE**: Como estas clases son compartidas con los *executors* de *Spark*, estas deben implementar `Serializable`

```java
public class SparkOAuthRequestImpl extends SparkOAuthRequest implements Serializable {

    private List<String> scopes;

    public SparkOAuthRequestImpl() {
        super();
        this.cIdAttrName = "client_id_modified";
        this.cSecretAttrName = "client_secret_modified";
        this.scopes = Arrays.asList("scope_lrba", "scope_lrba_test");
    }

}
```

### SparkOAuthResponse

El *API Server OAuth* también sigue el mismo patron de nombrado que el por defecto en LRBA, por lo que extender la clase es muy simple:

```java
public class SparkOAuthResponseImpl extends SparkOAuthResponse {

    public SparkOAuthResponseImpl() {
        super();
        this.accessTokenAttrName = "access_token_modified";
        this.expiresInAttrName = "expires_in_modified";
        this.tokenTypeAttrName = "token_type_modified";
    }

}
```

### Esquema del Notifications Manager

Como estamos desarrollando con Java, para serializar y deserializar *JSON*, es necesario implementar clases que sigan el siguiente esquema para solicitudes y respuestas del *Notification Manager*. En este ejemplo, vamos a usar una lista de `NotificationManagerRequest` para las solicitudes y un objeto `NotificationManagerResponse` para las respuestas.

### ISparkHttpData

Finalmente, el desarrollador debe implementar la interfaz `ISparkHttpData` que contiene las solicitudes y las repuestas dentro de un *dataset*:


```java
public class SparkAPIDataImpl implements ISparkHttpData<List<NotificationManagerRequest>, NotificationManagerResponse> {

   private SparkHttpRequest<List<NotificationManagerRequest>> sparkHttpRequest;
   private SparkHttpResponse<NotificationManagerResponse> sparkHttpResponse;

   public SparkApiRestData() {
   }

   public SparkApiRestData(SparkHttpRequest<List<NotificationManagerRequest>> sparkHttpRequest, SparkHttpResponse<NotificationManagerResponse> sparkHttpResponse) {
      super(sparkHttpRequest, sparkHttpResponse);
   }

   @Override
   public SparkHttpRequest<List<NotificationManagerRequest>> getSparkHttpRequest() {
      return sparkHttpRequest;
   }

   @Override
   public void setSparkHttpRequest(SparkHttpRequest<List<NotificationManagerRequest>> sparkHttpRequest) {
      this.sparkHttpRequest = sparkHttpRequest;
   }

   @Override
   public SparkHttpResponse<NotificationManagerResponse> getSparkHttpResponse() {
      return sparkHttpResponse;
   }

   @Override
   public void setSparkHttpResponse(SparkHttpResponse<NotificationManagerResponse> sparkHttpResponse) {
      this.sparkHttpResponse = sparkHttpResponse;
   }

}
```

## Declarar Transform

Transform *UserInput* dentro de la clase `NotificationManagerRequest`. Este paso es necesario ya que, la arquitectura necesita saber el endpoint, método de la petición y otra información necesaria.

```java
final Dataset<SparkAPIRESTData> userOutputDS = userInputDS.map((MapFunction<UserInput, SparkAPIRESTData>) userInput ->
               new SparkAPIRESTData(new SparkHttpRequest.SparkHttpRequestBuilder<List<NotificationManagerRequest>>()
                        .endpoint(NOTIFICATIONS_ENDPOINT)
                        .method(SparkHttpRequest.HttpMethod.POST)
                        .contentType(SparkHttpRequest.SparkContentType.JSON)
                        .body(Collections.singletonList(this.userInputToNotificationManagerRequest(userInput)))
                       .build(), null),
       Encoders.bean(SparkAPIRESTData.class));
```


## Declarar Target

Vamos a utilizar el siguiente código para nuestro *Target.HTTP*:

```java
Target.Http.REST.builder()
        .alias("userOutput")
        .authentication(Authentication.OAuth.builder()
                .uri(URI.create(Transformer.OAUTH_TOKEN_ENDPOINT))
                .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
                .request(new SparkOAuthRequestImpl())
                .responseClass(SparkOAuthResponseImpl.class)
                .authInHeader(true)
                .build()
        )
        .httpDataClass(SparkAPIDataImpl.class)
        .responseBodyClass(NotificationManagerResponse.class)
        .responseTarget(Target.File.Parquet.builder()
                .alias("userOutput")
                .physicalName("labs/email-user-output.parquet")
                .serviceName("bts.LRBA.BATCH")
                .build())
        .build()
```

## Test Unitarios para el *Job*

Recomendamos encarecidamente el uso de la clase de utilidades `LRBASparkTest` que provee la arquitectura para testear *jobs*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_InputData_ResultDatasets() {

        final UserInput userInput1 = new UserInput();
        userInput1.setUserId("8f649022-af6d-4306-b4d5-74560a649860");
        userInput1.setEmail("pablo.jimenez.tocino.next@bbva.com");
        final UserInput userInput2 = new UserInput();
        userInput2.setUserId("84e3ba6b-6533-4a93-bc20-2aa51293005a");
        userInput2.setEmail("pablo.jimenez.tocino.next+1@bbva.com");

        final Dataset<Row> inputDS = this.targetDataToDataset(Arrays.asList(userInput1, userInput2), UserInput.class);
        final Map<String, Dataset<Row>> resultDSMap = this.transformer.transform(new HashMap<>(Collections.singletonMap("userInput", inputDS)));
        final Dataset<Row> userOutput = resultDSMap.get("userOutput");

        assertNotNull(userOutput);

        final List<SparkAPIDataImpl> sparkAPIDataList = this.datasetToTargetData(userOutput, SparkAPIDataImpl.class);
        this.validateInputDataset(sparkAPIDataList);
    }

    private void validateInputDataset(final List<SparkAPIDataImpl> inputDataList) {
        assertNotNull(inputDataList);
        assertEquals(2, inputDataList.size());

        final SparkAPIDataImpl sparkAPIData1 = inputDataList
                .stream()
                .filter(sparkAPIData -> sparkAPIData
                        .getSparkHttpRequest()
                        .getBody()
                        .get(0)
                        .getUsers()[0]
                        .getEmail()
                        .equalsIgnoreCase("pablo.jimenez.tocino.next@bbva.com"))
                .findFirst().orElse(null);
        assertNotNull(sparkAPIData1);
        assertNull(sparkAPIData1.getSparkHttpResponse());
        assertEquals(Transformer.NOTIFICATION_TYPE_ID, sparkAPIData1.getSparkHttpRequest().getBody().get(0).getNotificationTypeId());
        assertEquals("8f649022-af6d-4306-b4d5-74560a649860", sparkAPIData1.getSparkHttpRequest().getBody().get(0).getUsers()[0].getUserId());
        assertEquals(Transformer.USER_TYPE, sparkAPIData1.getSparkHttpRequest().getBody().get(0).getUsers()[0].getUserType());
        assertEquals(Transformer.USER_COUNTRY, sparkAPIData1.getSparkHttpRequest().getBody().get(0).getUsers()[0].getCountry());
        assertEquals("Test notification API", sparkAPIData1.getSparkHttpRequest().getBody().get(0).getData().getSubject());
        assertEquals("Test notification API body for pablo.jimenez.tocino.next@bbva.com", sparkAPIData1.getSparkHttpRequest().getBody().get(0).getData().getBody());

        final SparkAPIData sparkAPIData2 = inputDataList
                .stream()
                .filter(sparkAPIData -> sparkAPIData
                        .getSparkHttpRequest()
                        .getBody()
                        .get(0)
                        .getUsers()[0]
                        .getEmail()
                        .equalsIgnoreCase("pablo.jimenez.tocino.next+1@bbva.com"))
                .findFirst().orElse(null);
        assertNotNull(sparkAPIData2);
        assertNull(sparkAPIData2.getSparkHttpResponse());
        assertEquals(Transformer.NOTIFICATION_TYPE_ID, sparkAPIData2.getSparkHttpRequest().getBody().get(0).getNotificationTypeId());
        assertEquals("84e3ba6b-6533-4a93-bc20-2aa51293005a", sparkAPIData2.getSparkHttpRequest().getBody().get(0).getUsers()[0].getUserId());
        assertEquals(Transformer.USER_TYPE, sparkAPIData2.getSparkHttpRequest().getBody().get(0).getUsers()[0].getUserType());
        assertEquals(Transformer.USER_COUNTRY, sparkAPIData2.getSparkHttpRequest().getBody().get(0).getUsers()[0].getCountry());
        assertEquals("Test notification API", sparkAPIData2.getSparkHttpRequest().getBody().get(0).getData().getSubject());
        assertEquals("Test notification API body for pablo.jimenez.tocino.next+1@bbva.com", sparkAPIData2.getSparkHttpRequest().getBody().get(0).getData().getBody());
    }

}
```

Para más información sobre la utilidad de LRBATest, ve a la sección *Tests de Integración para jobs* en [LRBA Utils](../../utilities/spark/01-Utils.md).

En este ejemplo, solo cubrimos los tests de la clase *Transformer*, pero también son necesarios los tests de los *builders*.


## Ejecutar el *job* en el cluster

Como el desarrollador no tiene acceso al *Notifications Manager API* desde un entorno de trabajo local, este *job* se debe de ejecutar en el clúster. Para ello, necesitamos desplegar el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).


## Comprobar la salida del *job*

Especificamos en el campo `responseTarget` el fichero `abs/email-user-output.parquet`. Para ello, debemos usar el servicio [BTS Visor](../../developerexperience/06-BTSVisor.md) para verificar el contenido de nuestro fichero.

Ejemplo de la salida de una ejecución (se muestra el fichero Parquet convertido a JSON):
```json
{
  "sparkHttpRequest": {
    "body": {
      "list": [
        {
          "element": {
            "data": {
              "body": "Test notification API body for test@bbva.com",
              "subject": "Test notification API"
            },
            "notificationTypeId": "60d1df6b17c0162d761a7a73",
            "users": {
              "list": [
                {
                  "element": {
                    "country": "ES",
                    "email": "test@bbva.com",
                    "userId": "4f6645e3-5d80-4852-ba33-b826c1db9e7d",
                    "userType": "EMPLOYEE"
                  }
                }
              ]
            }
          }
        }
      ]
    },
    "endpoint": "https://notifications.esolutions.work.eu.cld.nextgen.igrupobbva/notifications-manager/v1/notifications",
    "headers": {
      "key_value": [
        {
          "key": "Authorization",
          "value": {
            "list": [
              {
                "element": "Bearer ey..."
              }
            ]
          }
        },
        {
          "key": "Content-Type",
          "value": {
            "list": [
              {
                "element": "application/json"
              }
            ]
          }
        }
      ]
    },
    "method": "POST"
  },
  "sparkHttpResponse": {
    "body": {
      "data": {
        "links": {
          "list": [
            {
              "element": {
                "href": "https://notifications.esolutions.work.eu.cld.nextgen.igrupobbva/notifications-manager/v1/notifications/9bad6a2d-adbf-4ea8-84c3-cd2034d428da",
                "rel": "self"
              }
            }
          ]
        }
      }
    },
    "headers": {
      "key_value": [
        {
          "key": "cache-control",
          "value": {
            "list": [
              {
                "element": "no-cache, no-store, max-age=0, must-revalidate"
              }
            ]
          }
        },
        {
          "key": "connection",
          "value": {
            "list": [
              {
                "element": "keep-alive"
              }
            ]
          }
        },
        {
          "key": "content-type",
          "value": {
            "list": [
              {
                "element": "application/json;charset=UTF-8"
              }
            ]
          }
        },
        {
          "key": "date",
          "value": {
            "list": [
              {
                "element": "Thu, 26 Aug 2021 10:41:35 GMT"
              }
            ]
          }
        },
        {
          "key": "expires",
          "value": {
            "list": [
              {
                "element": "0"
              }
            ]
          }
        },
        {
          "key": "location",
          "value": {
            "list": [
              {
                "element": "https://notifications.esolutions.work.eu.cld.nextgen.igrupobbva/notifications-manager/v1/notifications/9bad6a2d-adbf-4ea8-84c3-cd2034d428da"
              }
            ]
          }
        },
        {
          "key": "pragma",
          "value": {
            "list": [
              {
                "element": "no-cache"
              }
            ]
          }
        },
        {
          "key": "server",
          "value": {
            "list": [
              {
                "element": "extended"
              }
            ]
          }
        },
        {
          "key": "strict-transport-security",
          "value": {
            "list": [
              {
                "element": "max-age=31536000; includeSubDomains"
              }
            ]
          }
        },
        {
          "key": "transfer-encoding",
          "value": {
            "list": [
              {
                "element": "chunked"
              }
            ]
          }
        },
        {
          "key": "x-frame-options",
          "value": {
            "list": [
              {
                "element": "SAMEORIGIN"
              }
            ]
          }
        },
        {
          "key": "x-rho-traceid",
          "value": {
            "list": [
              {
                "element": "d1f7fb34-824b-4ab9-bdd3-b7b720f4fc2a"
              }
            ]
          }
        },
        {
          "key": "x-xss-protection",
          "value": {
            "list": [
              {
                "element": "1; mode=block"
              }
            ]
          }
        }
      ]
    },
    "status": 201
  }
}
```

## Pasos Adicionales

Para un procesamiento posterior, se podría usar un segundo *job* para procesar el fichero *Parquet* generado. De manera que el desarrollador pueda hacer pasos adicionales para peticiones fallidas, almacenar respuestas en base de datos, etc. O, en caso de que el desarrollador quiera procesar el resultado en un mismo *job*, la [utilidad HTTP: Enviar Datasets al API HTTP](https://platform.bbva.com/lra-batch/documentation/24c414c411d5eebaf4b9c2ff1089ed59/lrba-architecture/utilities/spark/utils) puede ser usada en el *Transform*

# 06-Impersonation/01-Introduction.md
# 1. Introducción

Este *codelab* muestra el ciclo completo para compartir archivos entre las UUAAs con el BTS. 

**IMPORTANTE**: Los permisos para compartir archivos entre las UUAAs sólo pueden ser dados por los *Technical Leaders*.

# 06-Impersonation/02-Prerequisites.md
# 2. Requisitos Previos

## IDEs de Java
Eclipse es un IDE de código abierto. Puede ser descargado aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).  
IntelliJ IDEA es otro IDE que recomendamos su uso. Se puede descargar una versión gratuita aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## UUAA aprovisionadas
En este ejemplo no se va a desarrollar un *job* que se pueda ejecutar localmente. Se va a intentar guiar a los desarrolladores en el desarrollo de un *job* que se ejecute en el clúster.  
Por esta razón, el primer requisito es que la UUAA del desarrollador debe haber sido aprovisionada previamente. Si no es así, abra una solicitud al equipo de soporte del LRBA.

Vaya a la [Página de Soporte](https://platform.bbva.com/lra-batch/documentation/ee7143fa4ee75a4859bbc2a2b78dfe1b/lrba-architecture/support) para saber como abrir peticiones o incidencias a los equipos mencionados.


# 06-Impersonation/03-Example.md
# 3. Ejemplo

## Introducción

En este ejemplo, programaremos dos *jobs* diferentes de dos UUAAs diferentes.

Para cada uno, necesitaremos crear una nueva estructura base.

Después de eso, siga este *codelab* para programar cada uno de los *job*.


### Crear la Estructura de un Job

1- Crear una nueva estructura de un *job* con[esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

2- Después, ir al bitbucket del *job* y clonar el repositorio en local.

3- Ábralo con tu IDE favorito y, modifique el código tal y como se recomienda en la siguiente sección.


## UUAA1 Job

Este *job* crea un nuevo fichero y persiste en su propio BTS.

### Declarar el *Source*

- Leer los parámetros del *Source*.

### Declarar el *Transform* 

- Sí es aplicable la modificación de datos.

### Declarar el *Target*

- Añadir un *Target* de tipo Fichero Parquet
- Añadir un alias *Target*.
- Añadir un nombre físico (*physicalName*) para identificar el nombre del fichero de salida.
- Añadir el nombre de servicio definido para el BTS. Recuerde la sintaxis `bts.{your_UUAA}.BATCH`.
- Añadir la visibilidad del fichero adecuada para compartir el fichero.

El método *registerTargets* de la clase *JobCodelabBuilder.java* sería:

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.File.Parquet.builder()
                .alias("outputFile")
                .physicalName("transformedData.parquet")
                .serviceName("bts.UUA1.BATCH")
                .fileVisibility(VisibilityType.GROUP_SHARED)
                .build())
            .build();
        }
```

## Consola del LRBA

Antes de que otras UUAAs puedan usar los ficheros compartidos, debe darles permisos a través de la Consola del LRBA.

**IMPORTANTE**: Estos permisos sólo pueden ser dados por los *Technical Leaders*.

1. Seleccione el *namespace* para crear la entrada de impersonación.

2. Si es la primera vez, encontrará una pantalla como esta y presione el botón `CREATE CONFIG`.

![Crear Configuración](resources/CreateConfig.png)

Ahora se podrán crear nuevas entradas.

![Resultado Crear Configuración](resources/CreateConfigResult.png)

3. Añade una *`NEW IMPERSONATION CONFIG`*.
```
Type: bts
UUAA: UUAA for file sharing.
Visibility: GROUP_SHARED
Mode: RO.
```

![Nueva Impersonalización](resources/NewImpersonation.png) 

Una nueva entrada ha sido configurada. Puede siempre editarla o borrarla.

![Resultado Nueva Impersonalización](resources/NewImpersonationResult.png) 


## UUAA2 Job 

Este *job* lee un fichero desde la UUAA1 al BTS.

### Declarar *Source*

- Añadir un *source* Parquet para leer el fichero.
- Añadir un alias.
- Añadir un nombre físico (*physicalName*) que identifique el nombre del fichero de origen.
- Añadir el *service name* definido para el BTS de otra UUAA. Recuerde la sintaxis `bts.{other_UUAA}.BATCH`.


El método *registerSources* de la clase *JobCodelabBuilder.java* sería:

```java
@Override
public SourcesList registerSources() {
        return SourcesList.builder()
            .add(Source.File.Parquet.builder()
                .alias("inputFile")
                .physicalName("transformedData.parquet")
                .serviceName("bts.UUA1.BATCH")                
                .build())
            .build();
        }
```

### Declarar *Transform* 

- Si es aplicable añadir una transformación de datos.

### Declarar *Target*

- Defina que hacer con el resultado.

# 07-CryptoWrapper/01-Introduction.md
# 1. Introducción

## ¿Qué es LRBA Spark?

LRBA Spark es una implementación de LRBA para manejar sets de datos grandes. El ámbito de uso para esta nueva arquitectura incluye:

* Procesamiento de datos de aplicaciones entre **bases de datos operacionales** (Ether y Legacy) con una simple transformación lógica.

* Implementación de una **logica operacional de negocio** que incluye fuentes y destinos de datos de bases de datos operacionales y volumetrías para dar soporte en paralelo y procesos en memoria.

LRBA Spark ofrece:

* Una simplificación de desarrollo *batch* a través de aplicaciones sencillas (solo *SQL* para procesos *ETL*) o métodos de aplicación (API de Spark) con sets de datos.

* Accesos de configuración para **administradores de bases de datos** y otras persistencias (*buckets* de Epsilon que están DEPRECADOS o BTS) son transparentes para el desarrollo de la aplicación.

# 07-CryptoWrapper/02-Prerequisites.md
# 2. Prerrequisitos

## Java IDEs
Eclipse es un IDE (Entorno de Desarrollo Integrado) de código abierto. Se puede descargar desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que recomendamos utilizar. Tienes una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

## Configuración Crypto

Para utilizar esta funcionalidad, se debe solicitar la [petición de configuración crypto](https://itsmhelixbbva-dwp.onbmc.com/dwp/app/#/itemprofile/418).

# 07-CryptoWrapper/03-Implementation.md
# 3. Ejemplo

En este ejemplo, crearemos un *job* que leerá un fichero *Parquet* y escribirá un fichero *CSV* con filas encriptadas.

Ejemplo de *CSV* de salida:

```csv
value
joCdKDyxdRa2rxEk/LmSAIksNYehTNiI6k9jZvvaZoYNR4aX2xetXQhuy69zO5V8lWB4KHiflVqmBLnMiiol0eIwBS0aOaZg9YdC+1Y68x87oy0UGp+hos97cDIWD5Nwc7WPakHjxeucVpK8+99a1EzS1RLtRUw8Ywcw8uiXruZB1qyN6BBP1WbggsJFjHY+4aSXlFoofALVYdVdys7IAcAhNAVcnZ1TEi9CCfRRDaO3CygJQ==
tPZ2xEKK853C4lt18ER+9D/P7GucqOQuawx+Wk4HMIpkRoSTyPL/pn/9E8N8WXYry/+LdQsGTl9cruWku6B46qkGfyzWTwTqXviKc5pEyQ1/ZMwDgg7H0IJ5QuGIuliq80UXcVMc/ZWuuYdHwMMQ7ca3oKpHV0NrgaUsavN7aRCd6IA6GnG54t5YUrRHqp0W4lnbTb+69rA==
OwGHdQ6xz8Bj0dZhtaYru/ElhqHURMCCDCuiOKvhuhEHp/k/neO8znkXW0xRSqJhLPAYVocgZhk9XBJB0hrPH91MX2asfWIN57qS1RCrciGlOZLY0n9Wo/gtEZAOHjXZ2iCU258t5IQprEPIG628GgMkCdIThK6bEG3FD/3yM/AW3nLo9ji3OCudn8o9kE54hFmc1EeJSr+tfUTU1Q8/hYo7JK2XSIOH6Pl3zw==
4cLpZ7LHnXKF2R5yERqVIdtNphyC+aLFCzKN/JlSjqab9R+qI9y4jEa+orykuyaE+v6yP9WXfl5RTYMi4FQw7eVxjATdFZ4BeDHYmre4pDIlJ7tWwpOv/3XBe5JngWIBGL+aaYjuHerYxLTM3ms3RcM8e8tI15oE/auA59/3iDoL/Jotw5YN5vr6M/M+Qk173qFr6hZswf964UlLa453QxgHg==
```

## Implementaciones de la clase

### pom.xml

Añade la dependencia externa.
```xml
<dependencies>
    <dependency>
        <groupId>com.bbva.lrba.external-modules</groupId>
        <artifactId>crypto</artifactId>
    </dependency>
</dependencies>
```

## Crea un MapFunction

En nuestra función de la clase *Mapper*, se recibirá una instancia de *CryptoWrapper*.

```java
import com.bbva.lrba.crypto.CryptoWrapper;
import com.bbva.secarq.chameleon.sdk.core.exception.ChameleonSDKException;
import com.bbva.secarq.chameleon.sdk.core.model.ExecuteRequest;
import com.bbva.secarq.chameleon.sdk.core.model.ExecuteResponse;
import org.apache.spark.api.java.function.MapFunction;
import org.apache.spark.sql.Row;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.HashMap;
import java.util.Map;


public class MyMapper implements MapFunction<Row, String> {

    private final CryptoWrapper wrapper;

    public MyMapper(CryptoWrapper wrapper) {
        this.wrapper = wrapper;
    }

    @Override
    public String call(Row row) throws Exception {
        return encryptContent(row.mkString());
    }

    private String encryptContent(String toEncrypt) throws ChameleonSDKException {


        Map<String, String> context = new HashMap<>();
        context.put("operation", "DO");
        context.put("origin", "LRBA");
        context.put("endpoint", "LRBA"); // Your UUAA
        context.put("type", "datatosign");
        context.put("securityLevel", "5");
        ExecuteRequest request = new ExecuteRequest(toEncrypt, "PLAIN", "B64", context);

        // Execute the operation
        ExecuteResponse response;

        response = wrapper.getChameleonSDKClient().execute(request);


        //Retrieving result
        return response.getResult();
    }

    private void writeObject(ObjectOutputStream out) throws IOException {
        out.defaultWriteObject();
    }

    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject();
    }
}
```

Esta implementación *mapper* recibirá un valor de tipo *Row* y devolverá un *String*, tomará el valor *String* del *Row* y lo cifrará utilizando *cryptowrapper*. **Este contexto de definición es un ejemplo, cada aplicación debe tener sus propias configuraciones**.

## Declaración de Transform

En el *transform* se declaran dos constructores, un constructor vacío y otro con el *Mapper* creado como parámetro de entrada.

```java
package com.bbva.lrba.es.jsprk.crypto.v00;

import com.bbva.lrba.crypto.CryptoWrapper;
import com.bbva.lrba.properties.LRBAProperties;
import com.bbva.lrba.spark.transformers.Transform;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Encoders;
import org.apache.spark.sql.Row;

import java.util.HashMap;
import java.util.Map;

public class Transformer implements Transform {


    private MyMapper mapper;
    private final LRBAProperties lrbaProperties = new LRBAProperties();


    public Transformer() {
        CryptoWrapper wrapper = new CryptoWrapper(lrbaProperties.get("CRYPTO_BUNDLE_ID"), lrbaProperties.get("CRYPTO_NAMESPACE"));
        mapper = new MyMapper(wrapper);
    }

    public Transformer(MyMapper mapper) {
        this.mapper = mapper;
    }

    @Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {

        var input = map.get("fileAliasParquet");
        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
        datasetsToWrite.put("result", input.map(this.mapper, Encoders.STRING()).toDF());
        return datasetsToWrite;
    }

}
```
Esta implementación del *transform* llamará al *mapper* para cada fila, esta fila será encriptada como *String* y posteriormente devuelta.

## Declaración de *builder*

### *Sources*

Creamos un *Source* de tipo Parquet para leer el archivo `my_parquet` que tenemos localmente.

```java
    @Override
    public SourcesList registerSources() {
        return SourcesList.builder()
                .add(Source.File.Parquet.builder()
                        .alias("fileAliasParquet")
                        .physicalName("my_parquet")
                        .serviceName("bts.LRBA.BATCH")
                        .build())
                .build();
    }
```

### *Transform*

El el *registerTransform* indicamos nuestra clase *transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### *Targets*
En el *Target* definimos nuestra salida *CSV*.
```java
    @Override
    public TargetsList registerTargets() {
        return TargetsList.builder()
                .add(Target.File.Csv.builder()
                        .alias("result")
                        .physicalName("crypto.csv")
                        .serviceName("bts.LRBA.BATCH")
                        .header(true)
                        .delimiter(",")
                        .build())
                .build();
    }
}
```



# 07-CryptoWrapper/04-UnitTests.md
## Tests unitarios

Cada clase debe tener su propio test.

### Builder

```java
package com.bbva.lrba.es.jsprk.crypto.v00;

import com.bbva.lrba.builder.spark.domain.SourcesList;
import com.bbva.lrba.builder.spark.domain.TargetsList;
import com.bbva.lrba.properties.LRBAProperties;
import com.bbva.lrba.spark.domain.datasource.Source;
import com.bbva.lrba.spark.domain.datatarget.Target;
import com.bbva.lrba.spark.domain.transform.TransformConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class JobCryptoBuilderTest {

    private JobCryptoBuilder jobCryptoBuilder;


    @BeforeEach
    void setUp() {
        this.jobCryptoBuilder = new JobCryptoBuilder();
    }

    @Test
    void registerSources_na_SourceList() {

        final SourcesList sourcesList = this.jobCryptoBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("fileAliasParquet", source.getAlias());
        assertEquals("labs/my_parquet", source.getPhysicalName());
        assertEquals("bts.LRBA.BATCH", source.getServiceName());

    }


    @Test
    void registerTargets_na_TargetList() {


        final TargetsList targetsList = this.jobCryptoBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("result", target.getAlias());
        assertEquals("bts.LRBA.BATCH", target.getServiceName());
        assertEquals("crypto.csv", target.getPhysicalName());
    }
}
```

### Transform
Debemos proporcionar un objeto de tipo *Mock* para nuestro *mapper*, cada clase debe ser testada individualmente, una vez creado el *mock*, inicializa el *transform* enviando el *mapper* como parámetro de entrada.

```java
package com.bbva.lrba.es.jsprk.crypto.v00;


import com.bbva.lrba.spark.test.LRBASparkTest;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;

import java.util.Map;


class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @Mock(serializable = true)
    MyMapper mapper;

    @BeforeEach
    void setUp() throws Exception {
        MockitoAnnotations.openMocks(this);
        Mockito.doReturn("CIFRADO").when(mapper).call(Mockito.any());
        this.transformer = new Transformer(mapper);

    }

    @Test
    void transform_Output() {

        final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(Map.of("fileAliasParquet", mockedDataset()));
        Assertions.assertEquals(4, datasetMap.get("result").count());

    }

    private Dataset<Row> mockedDataset() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("id", DataTypes.StringType, false),
                        DataTypes.createStructField("firstName", DataTypes.StringType, false),
                        DataTypes.createStructField("lastName", DataTypes.StringType, false),
                });
        Row firstRow = RowFactory.create("1", "Daniella", "Adamec");
        Row secondRow = RowFactory.create("2", "Rudd", "Parfett");
        Row thirdRow = RowFactory.create("3", "Antoine", "Franscioni");
        Row lastRow = RowFactory.create("4", "Gabini", "Rodriguini");

        final List<Row> listRowsFirstDataset = Arrays.asList(firstRow, secondRow, thirdRow, lastRow);
        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        return datasetUtils.createDataFrame(listRowsFirstDataset, schema);
    }
}
```

### Mapper

Para hacer un test de nuestro *mapper* debemos crear *Mocks* de las clases *CryptoWrapper* y *ChameleonExtendedSDKClient*

```java
package com.bbva.lrba.es.jsprk.crypto.v00;

import com.bbva.lrba.crypto.CryptoWrapper;
import com.bbva.lrba.spark.test.LRBASparkTest;
import com.bbva.secarq.chameleon.sdk.core.exception.ChameleonSDKException;
import com.bbva.secarq.chameleon.sdk.core.model.ExecuteRequest;
import com.bbva.secarq.chameleon.sdk.core.model.ExecuteResponse;
import com.bbva.secarq.chameleon.sdk.ext.client.ChameleonExtendedSDKClient;
import org.apache.spark.sql.RowFactory;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;


class MyMapperTest extends LRBASparkTest {

    private MyMapper mapper;

    @Mock
    CryptoWrapper wrapper;

    @Mock
    ChameleonExtendedSDKClient sdk;

    @BeforeEach
    void setUp() throws ChameleonSDKException {
        MockitoAnnotations.openMocks(this);
        this.mapper = new MyMapper(wrapper);
        ExecuteResponse sdkresponse = new ExecuteResponse();
        sdkresponse.setResult("CIFRADO");
        Mockito.doReturn(sdk).when(wrapper).getChameleonSDKClient();
        Mockito.doReturn(sdkresponse).when(sdk).execute(Mockito.any(ExecuteRequest.class));
    }

    @Test
    void mapperTest() throws Exception {
        Assertions.assertEquals("CIFRADO", this.mapper.call(RowFactory.create("1", "Daniella", "Adamec")));
    }
}

```

# 08-TestingLRBA/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar los test con el fin de cumplir con los requisitos 
de cobertura de código, descubrir posibles errores en el código y asegurarse que el funcionamiento del job es el que debe.  

# 08-TestingLRBA/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.


# 08-TestingLRBA/03-HowToImplementTest.md
# 3. Cómo implementar test

Cada clase debe de tener su propio test. La clase Builder, la clase Transformer (si aplica) y cualquier otra clase que 
se haya añadido al proyecto que sea propia del job a desarrollar.

La utilidad LRBA Test tiene herramientas que ayudan y harán más fácil el desarrollo de estos test sin necesidad de añadir dependencias 
en el *pom.xml*. Estas herramientas sólo están disponibles en tests y no deben utilizarse en código normal. 

La clase destinada a testear la clase *Transformer* debe extender `LRBASparkTest`. Por ejemplo:

```java
class TransformerTest extends LRBASparkTest {
    // ...
}
```

En `LRBASparkTest` se inicia la sesión y se encarga de crear el contexto Spark. Es por ello que no se debe generar nunca una sesión de Spark en los test.  

Además, proporciona dos métodos de utilidad:

```java
    protected final <T> Dataset<Row> targetDataToDataset(List<T> targetData, Class<T> cls)
    protected final <T, U> List<T> datasetToTargetData(Dataset<U> dataset, Class<T> cls)
```
- `targetDataToDataset` permite al desarrollador transformar una `List` de objetos cuya clase es `T` en un `Dataset<Row>` que contenga todos esos objetos.
- `datasetToTargetData` permite transformar al desarrollador un `Dataset` de cualquier tipo en una `List` de objetos cuya clase es `T`.

Hay que recordar que **Spark** es **lazy** por lo que para poder trabajar con objetos se tendría que llamar a `datasetToTargetData` 
o un `collectAsList` si se quiere trabajar con *Rows*. Al no hacer uso de estos métodos las transformaciones realizadas no se aplicarían.
En los siguientes ejemplos se observan diferentes formas de uso:


```java
class TransformerTest extends LRBASparkTest {
    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
        MyData myDataObject = new MyData("id","valor1");
    }
    @Test
    void transform_Output() {
        final Map<String, Dataset<Row>> outputMap = this.transformer.transform(datasetsFromRead);
        Dataset<MyData> myDataDataset = outputMap.get("union").as(Encoders.bean(MyData.class));
        final List<MyData> rows = datasetToTargetData(myDataDataset, MyData.class);
        assertEquals(1, rows.size());
        assertEquals(myDataObject, rows.get(0));
    }
}
```
```java
class TransformerTest extends LRBASparkTest {
    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }
    @Test
    void transform_Output() {
        final Map<String, Dataset<Row>> outputMap = this.transformer.transform(datasetsFromRead);
        List<Row> rows = outputMap.get("union").collectAsList();
        assertEquals(1, rows.size());
        assertEquals("id", rows.get(0).get(0));
    }
}
```
```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_InputData_ResultDatasets() {

        List<InputSource1> mySource1List = new ArrayList<>();
        //rellenar con datos
        List<InputSource2> mySource2List = new ArrayList<>();
        //rellenar con datos
        
        final Dataset<Row> inputDS1 = this.targetDataToDataset(mySource1List, InputSource1.class);
        final Dataset<Row> inputDS2 = this.targetDataToDataset(mySource2List, InputSource2.class);
        final Map<String, Dataset<Row>> resultDSMap = this.transformer.transform(new HashMap<>(Map.of("sourceAlias1", inputDS1, "sourceAlias2", inputDS2)));
        final Dataset<Row> userOutput = resultDSMap.get("union");

        assertNotNull(userOutput);

        final List<JoinOutput> joinOutputList = this.datasetToTargetData(userOutput, JoinOutput.class);
        this.validateJoinOutputList(joinOutputList);
    }

    private void validateJoinOutputList(final List<JoinOutput> joinOutputList) {
        assertNotNull(joinOutputList);
        // Validate expected number of output objects
        assertEquals(2, joinOutputList.size());

        final JoinOutput joinOutput1 = joinOutputList
                .stream()
                .filter(joinOutput -> joinOutput
                        ...)
                .findFirst().orElse(null);
        assertNotNull(joinOutput1);
    }

}
```

En el caso de implementar la cobertura de código de la clase que implementa el job, esta no requiere ninguna herencia. 
Antes de cada método destinado a probar la lógica del job deberá instanciarse un objeto de la clase del job y en cada método
comprobar los valores que se han asignado a dicha clase como en el siguiente ejemplo:

```java
class JobDemoLRBATest {

    private JobDemoLRBA jobDemoLRBA;
    
    @BeforeEach
    void setUp() {
        jobDemoLRBA = new JobDemoLRBA();
    }
    
    @Test
    void registerSourcesTest() {
        final SourcesList sourcesList = this.jobDemoLRBA.registerSources();
        Source source = sourcesList.getSources().get(0);
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());        
        assertNotNull(source);
        assertEquals("fileAliasParquet", source.getAlias());
        assertEquals("labs/file.parquet", source.getPhysicalName());
        assertEquals("local.logicalDataStore.batch", source.getServiceName());
    }
    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobDemoLRBA.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }
    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobRwFileBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("union", target.getAlias());
        assertEquals("local.logicalDataStore.batch", target.getServiceName());
        assertEquals("labs/outputs/file_out.csv", target.getPhysicalName());
    }

}
```

# 08-TestingLRBA/04-TestingValues.md
# 4. Usando Parámetros en los Test

Existen diferentes tipos de parámetros que se utilizan para introducir datos al job:
    - `ApplicationContext`: Contexto de la aplicación.
    - `LRBAProperties`: Permite recuperar las configuraciones de despliegue.
    - `InputParams`: Parámetros de entrada que se pasan en tiempo de ejecución y son configurables en cada caso.

# Contexto de aplicación de LRBA

Con la clase `ApplicationContext` se puede almacenar información en cualquier paso y recuperarla en pasos posteriores.
Para poder testear que los datos se guardan correctamente se pueden recuperar de la siguiente manera: 

```java
public class TransformerTest extends LRBASparkTest {

    Transformer transformer;
    @BeforeEach
    void setUp() {
        transformer = new Transformer();
    }


    @Test
    public void registerTransformerTest() {
        Map<String, Dataset<Row>> result = transformer.transform(inputMap);
        String namesFiles = ((String)ApplicationContext.get("filesToWrite"));
        Assertions.assertEquals("A,C", namesFiles);

    }
}
```


# Propiedades LRBA

Como ya se ha dicho la clase `LRBAProperties` se usa para recuperar las configuraciones de despliegue.
Estos datos pueden ser mockeados y para ello hay que simular el comportamiento de la clase `LRBAProperties`, haciendo uso de Mockito de la siguiente manera:

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


# Parámetros de entrada

Para los parámetros de entrada se puede utilizar el método `InputParams.initialize(Map<String, String> inputParams)` para poder hacer un *mock*. 
Este método es accesible sólo en la capa test sin incluir ninguna librería y no es accesible en la capa de desarrollo de código.
En el siguiente ejemplo se puede ver como se mockean para que sean accesibles en la ejecución del test:

```java
class JobDemoLRBATest {

    @BeforeEach
    void setUp() {
        InputParams.initialize(Collections.singletonMap("EXECUTION_INTERVAL", "DAILY"));
        this.jdbcBuilder = new JDBCBuilder();
    }
    @Test
    void registerSources_InputParameters_NoException() {
        assertDoesNotThrow(() -> this.jobLRBADemo.registerSources());
    }
}
```

# 09-ReadApiHttp/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job de lectura de una API HTTP.
Se mostrará un ejemplo simple de como iterar sobre los resultados.
Además, se desarrollarán los tests unitarios para el código.

# 09-ReadApiHttp/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.

## API HTTP
Se ha proporcionado una API HTTP paginada para este codelab en una imagen Docker. Dicha imagen se tiene que crear desde el siguiente script de Python:

```python
import json
from collections import OrderedDict

import pandas as pd
from flask import Flask, request, Response

app = Flask(__name__)

csv_file_path = 'resources/person-data.csv'
df = pd.read_csv(csv_file_path, dtype=str)
data = [OrderedDict(row) for row in df.to_dict('records')]


def paginate_data(dataset, page, page_size):
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = dataset[start_idx:end_idx]
    return paginated_data


@app.route('/api/data', methods=['GET'])
def get_paginated_data():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', data.__len__() / 10))

    paginated_data = paginate_data(data, page, page_size)

    return Response(
        json.dumps({'results': paginated_data, 'page': page, 'pageSize': paginated_data.__len__(), 'totalItems': len(data)},
                   sort_keys=False), mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
```

El fichero `resources/person-data.csv` tendrá el siguiente contenido:

```csv
id,firstName,lastName,email,phone
1,Valentino,Dmitrievski,vdmitrievski0@cyberchimps.com,197-342-9235
2,Roderigo,Cullin,rcullin1@cbc.ca,216-394-1003
3,Baxy,Caulton,bcaulton2@netvibes.com,190-733-1608
4,Anthony,Kimmitt,akimmitt3@msn.com,866-119-7061
5,Zachary,Abrashkov,zabrashkov4@biblegateway.com,832-563-6834
6,Marybelle,Bremley,mbremley5@virginia.edu,826-961-3073
7,Sybil,Sculley,ssculley6@harvard.edu,269-573-2074
8,West,Ilewicz,wilewicz7@miitbeian.gov.cn,692-400-4134
9,Min,Tomaszkiewicz,mtomaszkiewicz8@google.co.uk,531-888-7677
10,Eadie,Jerrim,ejerrim9@vimeo.com,686-918-6401
11,Ulberto,Leither,uleithera@yolasite.com,530-488-8739
12,Dorree,Kenchington,dkenchingtonb@icio.us,649-857-4982
13,Una,Aberdeen,uaberdeenc@goo.gl,125-205-1038
14,Gabriellia,Pawelczyk,gpawelczykd@theglobeandmail.com,513-891-3857
15,Caprice,Parkey,cparkeye@devhub.com,476-435-1456
16,Carver,Sparwell,csparwellf@homestead.com,601-275-0717
17,Yolanda,Krauze,ykrauzeg@dmoz.org,736-461-5434
18,Audry,Ruby,arubyh@canalblog.com,281-430-7475
19,Gale,Manes,gmanesi@nps.gov,779-292-6146
20,Charlean,O'Meara,comearaj@creativecommons.org,348-558-7484
```

Para esta prueba usamos las siguientes dependencias de Python en el fichero `requirements.txt`:

```text
Flask==3.0.0
pandas==2.1.4
```

Una vez tenemos todo preparado, podemos crear la imagen Docker con el siguiente `Dockerfile`:

```Dockerfile
FROM python:3.12

WORKDIR /usr/src/app

RUN . /usr/src/app/venv/bin/activate

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./app.py" ]
```

Para ejecutarla, ejecute los siguientes comandos:

```bash
docker build -t person_data_api:0.0.0 .
docker run -p 5000:5000 person_data_api:0.0.0
```

Al hacer una llamada GET `http://127.0.0.1:5000/api/data?page_size=10&page=1` devuelve datos de personas con las columnas `id`, `firstName`, `lastName`, `email` y `phone`. La llamada devuelve un JSON con la siguiente estructura:

```json
{
  "results": [
    {
      "id": "1",
      "firstName": "firstName",
      "lastName": "lastName",
      "email": "email",
      "phone": "phone"
    }
  ],
  "page": 1,
  "pageSize": 10,
  "totalItems": 20
}
```

# 09-ReadApiHttp/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a utilizar un *Source HTTP* para leer los datos de una API, generar un *dataset* de tipo `PersonData` y guardarlos en un fichero CSV.  

## Clases a implementar

Para desarrollar este conector es necesario implementar algunas clases de la arquitectura.


### Objeto de dominio PersonData

Primero se va a crear una clase que contiene el esquema de datos que será usado en las peticiones al API.  
En este caso, para facilitar la implementación del *codelab*, el esquema esperado por la API es el mismo que el del fichero de entrada.

```java
public class PersonData implements Serializable {

    private Integer id;

    private String firstName;

    private String lastName;

    private String email;

    private String phone;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}
```

### Objeto de dominio ApiResponseWrapper

Se va a crear una clase que contenga el esquema de datos que será usado en las respuestas del API. En este caso será una representación del JSON que devuelve la API.

```java
public class ApiResponseWrapper implements Serializable {

    private List<PersonData> results;
    private int pageSize;
    private int totalItems;

    public List<PersonData> getResults() {
        return results;
    }

    public void setResults(List<PersonData> results) {
        this.results = results;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getTotalItems() {
        return totalItems;
    }

    public void setTotalItems(int totalItems) {
        this.totalItems = totalItems;
    }
}
```

Es importante que **todas estas clases sean serializables** para que la arquitectura pueda enviarlas al ejecutor. Esto se valida al construir el *job* pero recomendamos tenerlo en cuenta desde el principio.

### APIProvider

Para el correcto funcionamiento del *Source HTTP* es necesario extender de la clase `HttpRequestReaderHandler`, implementar el método `next` y
además el método `execute` que se encargará de realizar la petición al API.

La clase `ApiProvider` extiende (extends) la clase `HttpRequestReaderHandler<PersonData>`, lo que significa que hereda 
todas las propiedades y métodos de la clase base `HttpRequestReaderHandler`, adaptándolos para trabajar específicamente 
con objetos del tipo que se defina en el `DTO` , en este caso, `PersonData`. Esto permite reutilizar la funcionalidad 
de la clase base mientras se especializa el comportamiento para manejar datos relacionados con `PersonData`.

En este ejemplo de API paginada, se va a implementar un iterador que recorrerá los elementos y devolverá `false` cuando llegue al último.

Cuando Spark necesita obtener el siguiente registro de la partición que está leyendo, llama al método `get` de la clase 
`HttpRequestReaderHandler<PersonData>` y transforma cada uno de los elementos en un `InternalRow` que será usado por la
arquitectura para guardar los datos en el *dataset*. 
Para ello se hace uso de la función `ExpressionEncoder.javaBean` que transforma un objeto de dominio, `PersonData` en 
este job, en un `InternalRow` serializable.

```java
public class ApiProvider extends HttpRequestReaderHandler<PersonData> {

    private Iterator<PersonData> iterator;
    

    public ApiProvider(StructType schema, String url, Authentication authentication, Proxy proxy) {
        super(schema, url, authentication, proxy);
        this.iterator = null;
    }

    @Override
    public boolean next() {
        initializeIteratorIfNeeded();
        if (iteratorHasNext()) {
            consumeNextElement();
            return true;
        }
        return false;
    }

    private void initializeIteratorIfNeeded() {
        if (iterator == null) {
            iterator = getIterator();
        }
    }

    private boolean iteratorHasNext() {
        return iterator != null && iterator.hasNext();
    }

    private void consumeNextElement() {
        iterator.next(); // Consume the next element
        super.setIterator(iterator); // Update the iterator in the parent class
    }

    private Iterator<PersonData> getIterator() {
        URI uri = URI.create(this.getUrl());
        ApiRequest<ApiResponseWrapper> apiRequest = createApiRequest(uri);
        ApiResponse<ApiResponseWrapper> response = execute(apiRequest, ApiResponseWrapper.class);
        ApiResponseWrapper responseBody = response.getBody();
        return responseBody.getResults().iterator();
    }

    private ApiRequest<ApiResponseWrapper> createApiRequest(URI url) {
        return new ApiRequest.ApiRequestBuilder<ApiResponseWrapper>()
                .endpoint(url)
                .method(HttpMethod.GET)
                .headers(new HashMap<>())
                .build();
    }
    
}
```

## Implementación del builder

### Sources

Se crea un *source* de tipo HTTP para leer el API paginado. Se indica el alias, la URL del API, el esquema de datos que se espera y la referencia a la clase `ApiProvider` que se ha implementado.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.Http.builder()
                    .alias("alias")
                    .schema(Encoders.bean(PersonData.class).schema())
                    .url("http://127.0.0.1:5000/api/data?page_size=20&page=1")
                    .apiReaderClass(ApiProvider.class)
                    .build())
            .build();
}
```

### Transform

En el método `registerTransform` se indica cuál es nuestra clase *Transform*. Para este ejemplo se devuelve `null` ya que no se va a realizar ninguna transformación.

```java
@Override
public TransformConfig registerTransform() {
    return null;
}
```

### Targets

Se crea un *target* que va a escribir los datos en un CSV.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Csv.builder()
                    .alias("alias")
                    .physicalName("labs/outputs/api_result.csv")
                    .serviceName("local.logicalDataStore.batch")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

## Test unitarios del job

### Builder

```java
class JobApiToBtsBuilderTest {

    private JobApiToBtsBuilder jobApiToBtsBuilder;

    @BeforeEach
    void setUp() {
        this.jobApiToBtsBuilder = new JobApiToBtsBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobApiToBtsBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("alias", source.getAlias());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobApiToBtsBuilder.registerTransform();
        assertNull(transformConfig);
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobApiToBtsBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("alias", target.getAlias());
        assertEquals("labs/outputs/api_result.csv", target.getPhysicalName());
    }

}
```

### ApiProvider

En este test se tendrá que validar que el iterador recorre todos los registros y que el método `get` devuelve un `InternalRow` con los datos esperados.
Para poder hacer esto, se va a hacer uso de *mocks* para simular la respuesta del API y el conector HTTP. Es necesario setear el conector HTTP en el `ApiProvider` para poder hacer las pruebas.
Este conector se va a simular con un *mock* de la interfaz `IHttpConnector` y se mockeará el método `execute` para que devuelva una respuesta esperada. 
Después se añade a la clase `ApiProvider` mediante el método `setConnector`.

```java
class ApiProviderTest {

    private ApiProvider apiProvider;

    @BeforeEach
    void setUp() {
        this.apiProvider = new ApiProvider(mock(StructType.class), "url", mock(Authentication.class), mock(Proxy.class));
    }

    @Test
    void next_fetchNextPage() {
        // Mock response
        ApiResponseWrapper responseWrapper = mock(ApiResponseWrapper.class);
        when(responseWrapper.getPageSize()).thenReturn(10);
        when(responseWrapper.getTotalItems()).thenReturn(20);
        when(responseWrapper.getResults()).thenReturn(List.of(mock(PersonData.class), mock(PersonData.class)));
        ApiResponse<ApiResponseWrapper> response = new ApiResponse<>(200, new HashMap<>(), responseWrapper);

        // Connector Mock
        IHttpConnector connector = mock(IHttpConnector.class);
        when(connector.execute(any(ApiRequest.class), any())).thenReturn(response);
        this.apiProvider.setConnector(connector);

        // Call to next method
        assertTrue(this.apiProvider.next());
        assertTrue(this.apiProvider.next());
        assertFalse(this.apiProvider.next());

        verify(connector, Mockito.times(1)).execute(any(ApiRequest.class), any());
    }
}
```


# 09-ReadApiHttp/04-ExecuteJob.md
# 4. Cómo ejecutar el job

En esta fase vamos a ejecutar nuestro *job* en local y ver cómo se comporta.

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```

Se puede observar que la ejecución no lanza ningún error, pero eso no asegura que las peticiones al API se hayan ejecutado satisfactoriamente. Para poder validarlas hay que revisar el fichero de salida.

### Analizar el resultado

Ahora, se puede observar que en el directorio `local-execution/files` hay un fichero llamado `output/api_result.csv`, el cual su contenido es el siguiente:

```csv
email,firstName,id,lastName,phone
vdmitrievski0@cyberchimps.com,Valentino,1,Dmitrievski,197-342-9235
rcullin1@cbc.ca,Roderigo,2,Cullin,216-394-1003
bcaulton2@netvibes.com,Baxy,3,Caulton,190-733-1608
akimmitt3@msn.com,Anthony,4,Kimmitt,866-119-7061
zabrashkov4@biblegateway.com,Zachary,5,Abrashkov,832-563-6834
mbremley5@virginia.edu,Marybelle,6,Bremley,826-961-3073
ssculley6@harvard.edu,Sybil,7,Sculley,269-573-2074
wilewicz7@miitbeian.gov.cn,West,8,Ilewicz,692-400-4134
mtomaszkiewicz8@google.co.uk,Min,9,Tomaszkiewicz,531-888-7677
ejerrim9@vimeo.com,Eadie,10,Jerrim,686-918-6401
uleithera@yolasite.com,Ulberto,11,Leither,530-488-8739
dkenchingtonb@icio.us,Dorree,12,Kenchington,649-857-4982
uaberdeenc@goo.gl,Una,13,Aberdeen,125-205-1038
gpawelczykd@theglobeandmail.com,Gabriellia,14,Pawelczyk,513-891-3857
cparkeye@devhub.com,Caprice,15,Parkey,476-435-1456
csparwellf@homestead.com,Carver,16,Sparwell,601-275-0717
ykrauzeg@dmoz.org,Yolanda,17,Krauze,736-461-5434
arubyh@canalblog.com,Audry,18,Ruby,281-430-7475
gmanesi@nps.gov,Gale,19,Manes,779-292-6146
comearaj@creativecommons.org,Charlean,20,O'Meara,348-558-7484
```

# 10-ReadMultiPageApiHttp/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job de lectura de una API HTTP paginada.
Se mostrará un ejemplo simple de como iterar sobre los resultados de una página y como hacer que el iterador salte a la 
siguiente página y se detenga en el último elemento de la última página.
Además, se desarrollarán los tests unitarios para el código.

# 10-ReadMultiPageApiHttp/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.

## Api HTTP
Se ha proporcionado una API HTTP paginada para este codelab en una imagen Docker. Dicha imagen se tiene que crear desde el siguiente script de Python:

```python
import json
from collections import OrderedDict

import pandas as pd
from flask import Flask, request, Response

app = Flask(__name__)

csv_file_path = 'resources/person-data.csv'
df = pd.read_csv(csv_file_path, dtype=str)
data = [OrderedDict(row) for row in df.to_dict('records')]


def paginate_data(dataset, page, page_size):
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = dataset[start_idx:end_idx]
    return paginated_data


@app.route('/api/data', methods=['GET'])
def get_paginated_data():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', data.__len__() / 10))

    paginated_data = paginate_data(data, page, page_size)

    return Response(
        json.dumps({'results': paginated_data, 'page': page, 'pageSize': paginated_data.__len__(), 'totalItems': len(data)},
                   sort_keys=False), mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
```

El fichero `resources/person-data.csv` tendrá el siguiente contenido:

```csv
id,firstName,lastName,email,phone
1,Valentino,Dmitrievski,vdmitrievski0@cyberchimps.com,197-342-9235
2,Roderigo,Cullin,rcullin1@cbc.ca,216-394-1003
3,Baxy,Caulton,bcaulton2@netvibes.com,190-733-1608
4,Anthony,Kimmitt,akimmitt3@msn.com,866-119-7061
5,Zachary,Abrashkov,zabrashkov4@biblegateway.com,832-563-6834
6,Marybelle,Bremley,mbremley5@virginia.edu,826-961-3073
7,Sybil,Sculley,ssculley6@harvard.edu,269-573-2074
8,West,Ilewicz,wilewicz7@miitbeian.gov.cn,692-400-4134
9,Min,Tomaszkiewicz,mtomaszkiewicz8@google.co.uk,531-888-7677
10,Eadie,Jerrim,ejerrim9@vimeo.com,686-918-6401
11,Ulberto,Leither,uleithera@yolasite.com,530-488-8739
12,Dorree,Kenchington,dkenchingtonb@icio.us,649-857-4982
13,Una,Aberdeen,uaberdeenc@goo.gl,125-205-1038
14,Gabriellia,Pawelczyk,gpawelczykd@theglobeandmail.com,513-891-3857
15,Caprice,Parkey,cparkeye@devhub.com,476-435-1456
16,Carver,Sparwell,csparwellf@homestead.com,601-275-0717
17,Yolanda,Krauze,ykrauzeg@dmoz.org,736-461-5434
18,Audry,Ruby,arubyh@canalblog.com,281-430-7475
19,Gale,Manes,gmanesi@nps.gov,779-292-6146
20,Charlean,O'Meara,comearaj@creativecommons.org,348-558-7484
```

Para esta prueba usamos las siguientes dependencias de Python en el fichero `requirements.txt`:

```text
Flask==3.0.0
pandas==2.1.4
```

Una vez tenemos todo preparado, podemos crear la imagen Docker con el siguiente `Dockerfile`:

```Dockerfile
FROM python:3.12

WORKDIR /usr/src/app

RUN . /usr/src/app/venv/bin/activate

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./app.py" ]
```

Para ejecutarla, ejecute los siguientes comandos:

```bash
docker build -t person_data_api:0.0.0 .
docker run -p 5000:5000 person_data_api:0.0.0
```

Al hacer una llamada GET `http://127.0.0.1:5000/api/data?page_size=10&page=1` devuelve datos de personas con las columnas `id`, `firstName`, `lastName`, `email` y `phone`. La llamada devuelve un JSON con la siguiente estructura:

```json
{
  "results": [
    {
      "id": "1",
      "firstName": "firstName",
      "lastName": "lastName",
      "email": "email",
      "phone": "phone"
    }
  ],
  "page": 1,
  "pageSize": 10,
  "totalItems": 20
}
```

# 10-ReadMultiPageApiHttp/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a utilizar un *Source HTTP* para leer los datos de una API paginada, generar un *dataset* de tipo `PersonData` y guardarlos en un fichero CSV.  

## Clases a implementar

Para desarrollar este conector es necesario implementar algunas clases de la arquitectura.


### Objeto de dominio PersonData

Primero se va a crear una clase que contiene el esquema de datos que será usado en las peticiones al API.  
En este caso, para facilitar la implementación del *codelab*, el esquema esperado por la API es el mismo que el del fichero de entrada.

```java
public class PersonData implements Serializable {

    private Integer id;

    private String firstName;

    private String lastName;

    private String email;

    private String phone;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}
```

### Objeto de dominio ApiResponseWrapper

Se va a crear una clase que contenga el esquema de datos que será usado en las respuestas del API. En este caso será una representación del JSON que devuelve la API.

```java
public class ApiResponseWrapper implements Serializable {

    private List<PersonData> results;
    private int pageSize;
    private int totalItems;

    public List<PersonData> getResults() {
        return results;
    }

    public void setResults(List<PersonData> results) {
        this.results = results;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getTotalItems() {
        return totalItems;
    }

    public void setTotalItems(int totalItems) {
        this.totalItems = totalItems;
    }
}
```

Es importante que **todas estas clases sean serializables** para que la arquitectura pueda enviarlas al ejecutor. Esto se valida al construir el *job* pero recomendamos tenerlo en cuenta desde el principio.

### APIProvider

Para el correcto funcionamiento del *Source HTTP* es necesario extender de la clase `HttpRequestReaderHandler`, implementar el método `next` y
además el método `execute` que se encargará de realizar la petición al API.

La clase `ApiProvider` extiende (extends) la clase `HttpRequestReaderHandler<PersonData>`, lo que significa que hereda
todas las propiedades y métodos de la clase base `HttpRequestReaderHandler`, adaptándolos para trabajar específicamente
con objetos del tipo que se defina en el `DTO` , en este caso, `PersonData`. Esto permite reutilizar la funcionalidad
de la clase base mientras se especializa el comportamiento para manejar datos relacionados con `PersonData`.

En este ejemplo de API paginada, se va a implementar un iterador que recorrerá los elementos y devolverá `false` cuando llegue al último.

```java
public class ApiProvider extends HttpRequestReaderHandler<PersonData> {

    private Iterator<PersonData> iterator;
    private int readedItems;
    private int page;
    private boolean hasNextPage;
    private ApiResponse<ApiResponseWrapper> response;

    public ApiProvider(StructType schema, String url, Authentication authentication, Proxy proxy) {
        super(schema, url, authentication, proxy);
        this.page = 1;
        this.readedItems = 0;
        this.hasNextPage = true;
        this.iterator = null;
    }

    @Override
    public boolean next() {
        if (hasNextPage && (iterator == null || !iterator.hasNext())) {
            iterator = fetchNextPage();
            super.setIterator(iterator);
        }
        return iterator.hasNext();
    }

    private Iterator<PersonData> fetchNextPage() {
        URI uri = URI.create(this.getUrl() + page);
        ApiRequest<ApiResponseWrapper> apiRequest = createApiRequest(uri);
        response = execute(apiRequest, ApiResponseWrapper.class);
        ApiResponseWrapper responseBody = response.getBody();
        page++;
        readedItems += responseBody.getPageSize();
        hasNextPage = readedItems < responseBody.getTotalItems();
        return responseBody.getResults().iterator();
    }

    private ApiRequest<ApiResponseWrapper> createApiRequest(URI url) {
        return new ApiRequest.ApiRequestBuilder<ApiResponseWrapper>()
                .endpoint(url)
                .method(HttpMethod.GET)
                .headers(new HashMap<>())
                .build();
    }

    
}
```

## Implementación del builder

### Sources

Se crea un *source* de tipo HTTP para leer el API paginado. Se indica el alias, la URL del API, el esquema de datos que se espera y la referencia a la clase `ApiProvider` que se ha implementado.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.Http.builder()
                    .alias("alias")
                    .schema(Encoders.bean(PersonData.class).schema())
                    .url("http://127.0.0.1:5000/api/data?page_size=10&page=")
                    .apiReaderClass(ApiProvider.class)
                    .build())
            .build();
}
```

### Transform

En el método `registerTransform` se indica cuál es nuestra clase *Transform*. Para este ejemplo se devuelve `null` ya que no se va a realizar ninguna transformación.

```java
@Override
public TransformConfig registerTransform() {
    return null;
}
```

### Targets

Se crea un *target* que va a escribir los datos en un CSV.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Csv.builder()
                    .alias("alias")
                    .physicalName("output/api_result.csv")
                    .serviceName("local.logicalDataStore.batch")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

## Test unitarios del job

### Builder

```java
class JobApiToBtsBuilderTest {

    private JobApiToBtsBuilder jobApiToBtsBuilder;

    @BeforeEach
    void setUp() {
        this.jobApiToBtsBuilder = new JobApiToBtsBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobApiToBtsBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("alias", source.getAlias());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobApiToBtsBuilder.registerTransform();
        assertNull(transformConfig);
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobApiToBtsBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("alias", target.getAlias());
        assertEquals("labs/outputs/api_result.csv", target.getPhysicalName());
    }

}
```

### ApiProvider

En este test se tendrá que validar que el iterador recorre todas las páginas y que el método `get` devuelve un `InternalRow` con los datos esperados.
Para poder hacer esto, se va a hacer uso de *mocks* para simular la respuesta del API y el conector HTTP. Es necesario setear el conector HTTP en el `ApiProvider` para poder hacer las pruebas.
Este conector se va a simular con un *mock* de la interfaz `IHttpConnector` y se mockeará el método `execute` para que devuelva una respuesta esperada. 
Después se añade a la clase `ApiProvider` mediante el método `setConnector`.

```java
class ApiProviderTest {

    private ApiProvider apiProvider;

    @BeforeEach
    void setUp() {
        this.apiProvider = new ApiProvider(mock(StructType.class), "url", mock(Authentication.class), mock(Proxy.class));
    }

    @Test
    void next_getIerator() {
        // Mock respuesta
        ApiResponseWrapper responseWrapper = mock(ApiResponseWrapper.class);
        when(responseWrapper.getResults()).thenReturn(new ArrayList<>(0));
        ApiResponse<ApiResponseWrapper> response = new ApiResponse<>(200, new HashMap<>(), responseWrapper);

        // Mock del conector
        IHttpConnector connector = mock(IHttpConnector.class);
        when(connector.execute(any(ApiRequest.class), any())).thenReturn(response);
        this.apiProvider.setConnector(connector);

        this.apiProvider.next();

        verify(connector, Mockito.times(1)).execute(any(ApiRequest.class), any());
    }

    @Test
    void get_iterator_hasNext() {
        // Mock respuesta
        ApiResponseWrapper responseWrapper = mock(ApiResponseWrapper.class);
        when(responseWrapper.getResults()).thenReturn(List.of(mock(PersonData.class), mock(PersonData.class)));
        ApiResponse<ApiResponseWrapper> response = new ApiResponse<>(200, new HashMap<>(), responseWrapper);

        // Mock del conector
        IHttpConnector connector = mock(IHttpConnector.class);
        when(connector.execute(any(ApiRequest.class), any())).thenReturn(response);
        this.apiProvider.setConnector(connector);

        // Llamada al api
        this.apiProvider.next();
        InternalRow row = this.apiProvider.get();
        assertNotNull(row);

        // Segundo elemento de la lista
        this.apiProvider.next();
        row = this.apiProvider.get();
        assertNotNull(row);

        // Ha terminado el iterador
        assertFalse(this.apiProvider.next());

        verify(connector, Mockito.times(1)).execute(any(ApiRequest.class), any());
    }

}
```


# 10-ReadMultiPageApiHttp/04-ExecuteJob.md
# 4. Cómo ejecutar el job

En esta fase vamos a ejecutar nuestro *job* en local y ver cómo se comporta.

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```

Se puede observar que la ejecución no lanza ningún error, pero eso no asegura que las peticiones al API se hayan ejecutado satisfactoriamente. Para poder validarlas hay que revisar el fichero de salida.

### Analizar el resultado

Ahora, se puede observar que en el directorio `local-execution/files` hay un fichero llamado `output/api_result.csv`, el cual su contenido es el siguiente:

```csv
email,firstName,id,lastName,phone
vdmitrievski0@cyberchimps.com,Valentino,1,Dmitrievski,197-342-9235
rcullin1@cbc.ca,Roderigo,2,Cullin,216-394-1003
bcaulton2@netvibes.com,Baxy,3,Caulton,190-733-1608
akimmitt3@msn.com,Anthony,4,Kimmitt,866-119-7061
zabrashkov4@biblegateway.com,Zachary,5,Abrashkov,832-563-6834
mbremley5@virginia.edu,Marybelle,6,Bremley,826-961-3073
ssculley6@harvard.edu,Sybil,7,Sculley,269-573-2074
wilewicz7@miitbeian.gov.cn,West,8,Ilewicz,692-400-4134
mtomaszkiewicz8@google.co.uk,Min,9,Tomaszkiewicz,531-888-7677
ejerrim9@vimeo.com,Eadie,10,Jerrim,686-918-6401
uleithera@yolasite.com,Ulberto,11,Leither,530-488-8739
dkenchingtonb@icio.us,Dorree,12,Kenchington,649-857-4982
uaberdeenc@goo.gl,Una,13,Aberdeen,125-205-1038
gpawelczykd@theglobeandmail.com,Gabriellia,14,Pawelczyk,513-891-3857
cparkeye@devhub.com,Caprice,15,Parkey,476-435-1456
csparwellf@homestead.com,Carver,16,Sparwell,601-275-0717
ykrauzeg@dmoz.org,Yolanda,17,Krauze,736-461-5434
arubyh@canalblog.com,Audry,18,Ruby,281-430-7475
gmanesi@nps.gov,Gale,19,Manes,779-292-6146
comearaj@creativecommons.org,Charlean,20,O'Meara,348-558-7484
```

# 11-JdbcTransactionalJob/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job jdbc transaccional.
Se mostrará un ejemplo de como ejecutar las consultas.
Además, se desarrollarán los tests unitarios para el código.

# 11-JdbcTransactionalJob/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.

## JDBC TRANSACCIONAL
A continuación se proporciona una imagen docker con la base de datos de prueba para este codelab. 
* Se utilizará *PostgreSQL* como ejemplo solo para este codelab, no está permitido su uso en la arquitectura.


Se debe crear el fichero `exampledb.sql` con el siguiente contenido.

```Example db
\c postgres
create database exampledb;

\c exampledb

-- Create schema if it does not exist
CREATE SCHEMA IF NOT EXISTS schema_test;

-- Create table for accounts in the schema_test schema
CREATE TABLE schema_test.accounts
(
    account_id    SERIAL PRIMARY KEY,
    account_number VARCHAR(20),
    balance DECIMAL(10, 2),
    created_at    DATE,
    updated_at    DATE
);

INSERT INTO schema_test.accounts (account_number, balance, created_at, updated_at)
VALUES
    ('123456789012345', 10.32, '2023-01-01', '2023-01-01'),
    ('234567890123456', 344.14, '2023-02-01', '2023-02-01'),
    ('345678901234567', 1439.78, '2023-03-01', '2023-03-01'),
    ('456789012345678', 400.13, '2023-04-01', '2023-04-01'),
    ('567890123456789', 543.34, '2023-05-01', '2023-05-01'),
    ('678901234567890', 603.20, '2023-06-01', '2023-06-01'),
    ('789012345678901', 7366.43, '2023-07-01', '2023-07-01'),
    ('890123456789012', 3466.22, '2023-08-01', '2023-08-01'),
    ('901234567890123', 13879.17, '2023-09-01', '2023-09-01'),
    ('012345678901234', 1045.32, '2023-10-01', '2023-10-01');


-- Create table for movements in the schema_test schema
create table  schema_test.movements
(
    id varchar PRIMARY KEY,
    account_id INTEGER REFERENCES schema_test.accounts(account_id),
    amount DECIMAL(10, 2),
    type VARCHAR(1),
    status VARCHAR(1),
    created_at DATE,
    updated_at DATE
);

-- Insert specific records into the movements table
INSERT INTO schema_test.movements (id, account_id, amount, type, status, created_at, updated_at)
VALUES
    ('000000001', 1, 23.34, 'I', 'P', '2023-01-01', '2023-01-01'),
    ('000000002', 2, 60.45, 'E', 'L', '2023-02-01', '2023-02-01'),
    ('000000003', 3, 70.65, 'I', 'P', '2023-03-01', '2023-03-01'),
    ('000000004', 4, 80.17, 'E', 'L', '2023-04-01', '2023-04-01'),
    ('000000005', 5, 90.22, 'I', 'P', '2023-05-01', '2023-05-01'),
    ('000000006', 6, 34.45, 'E', 'L', '2023-06-01', '2023-06-01'),
    ('000000007', 7, 110.65, 'I', 'P', '2023-07-01', '2023-07-01'),
    ('000000008', 8, 55.10, 'E', 'L', '2023-08-01', '2023-08-01'),
    ('000000009', 9, 450.15, 'I', 'P', '2023-09-01', '2023-09-01'),
    ('000000010', 10, 140.56, 'E', 'L', '2023-10-01', '2023-10-01');
```

En el mismo directorio se deberá crear el siguiente `Dockerfile`:

```Dockerfile
FROM postgres:latest

ENV POSTGRES_PASSWORD=postgres

# Copiar el script SQL al contenedor
COPY exampledb.sql /docker-entrypoint-initdb.d/

# Exponer el puerto 5432
EXPOSE 5432
```

Para iniciar la base de datos, desde ese mismo directorio, ejecute los siguientes comandos:

```bash
# Construir la imagen Docker
docker build -t jdbc_test:0.0.0 .

# Ejecutar el contenedor Docker
docker run --name postgres-test -p 5432:5432 -d jdbc_test:0.0.0
```

# 11-JdbcTransactionalJob/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

Partiendo de la base de datos generada anteriormente y que consta de dos tablas (Movements y Accounts), se desarrollará un job de ejemplo
que tendrá el siguiente flujo. 

- Leer un fichero con varios registros de operaciones. 
- Comprobar que no se haya insertado esa operación previamente. Esto se hace debido a que no se puede garantizar
que no se vaya a repetir la ejecución de la fila (ya sea por un relanzamiento de una tarea o del batch entero)
   - Si ya existe, no hace nada y sigue con la siguiente operación. 
   - Si no existe, se hace una select for update de la tabla de cuentas y se comprueba 
  	si el cliente tiene saldo en la cuenta. 
       - Si tiene saldo
         - Insert en la tabla de operaciones con estado liquidado (L)
         - Update del saldo en la tabla de cuentas.
       - Si no tiene saldo
         - Se inserta la operación en la tabla de operaciones con estado pendiente (P). 


## Clases a implementar

Para desarrollar este job es necesario implementar algunas clases de la arquitectura.

Es importante que **todas estas clases sean serializables** para que la arquitectura pueda enviarlas al ejecutor. Esto se valida al construir el *job* pero recomendamos tenerlo en cuenta desde el principio.

### Fichero lectura BTS
Se generará un fichero que se leerá en el *Source* del job, simulando distintas operaciones hechas por clientes con abonos (I) y cargos (E). 

***local-execution/files/input1.csv***
```csv
id,account_id,amount,type
000000003,8,15.12,E
000000011,1,123.45,E
000000012,2,2.56,E
000000013,3,11.67,I
000000014,4,16.78,E
000000015,5,745.89,E
000000016,6,3.90,E
000000017,7,150.01,I
000000018,8,34.12,E
000000019,9,21.23,I
000000020,10,16.34,E
```

### JdbcTransactional

Para el correcto funcionamiento del *Target JDBC Transaccional* es necesario crear una clase que extienda de la clase `JdbcTransactionWriterHandler` e implementar el método `write` 
que se encargará de realizar las *querys* contra la base de datos.

El método `write` se ejecutará por cada uno de los registros del Dataset, y su información vendrá en el parámetro `internalRow`.
Las consultas deberán realizarse haciendo uso del método createPreparedStatement, que recibirá como parámetro la query a ejecutar. 
Se le deberán asignar los parámetros necesarios y cerrar el `PrearedStatement` una vez finalizada la consulta tal y como se muestra 
en el ejemplo.


```java
public class JdbcTransactional extends JdbcTransactionWriterHandler {
    private final String tableName_movements = "schema_test.movements";
    private final String tableName_accounts = "schema_test.accounts";
    private final String STATUS_PENDING = "P";
    private final String STATUS_LIQUIDATED = "L";
    private final String TYPE_INCOME = "I";
    private final String TYPE_EXPENSE = "E";
    private static final Logger LOGGER = LoggerFactory.getLogger(JdbcTransactional.class);

    @Override
    public void write(Map<String, Object> row, StructType structType) {

        String movement_id = (String) row.get("id");
        int account_id = (Integer) row.get("account_id");
        double amount = (Double) row.get("amount");
        String movement_type = (String) row.get("type");

        try {
            boolean movement_exists = this.movement_exists(movement_id);

            if(!movement_exists){
                LOGGER.info("The movement with id {} does not exist in the database", movement_id);

                double currentBalance = this.select_for_update_account(account_id);

                boolean has_available_balance = true;
                if (TYPE_EXPENSE.equals(movement_type)) {
                    has_available_balance = currentBalance >= amount;
                }

                if(!has_available_balance){
                    LOGGER.info("The account with id {} does not have enough balance", account_id);
                    this.insert_movement(row, STATUS_PENDING);
                }else {
                    this.insert_movement(row, STATUS_LIQUIDATED);
                    double newBalance = this.calculate_new_balance(currentBalance, amount, movement_type);
                    this.update_account_balance(account_id, newBalance);
                }
            }

        } catch (SQLException e) {
            LOGGER.error("Error while executing the transaction:", e);
            throw new LrbaApplicationException("Error while executing the transaction", 6);
        }
    }

    private boolean movement_exists(String pk) throws SQLException {
        LOGGER.info("Checking if the movement with id {} exists in the database", pk);
        String query = "SELECT id FROM " + tableName_movements + " WHERE id = ?";
        try (PreparedStatement sqlSelect = this.createPreparedStatement(query)) {
            sqlSelect.setString(1, pk);
            try (ResultSet resultSet = sqlSelect.executeQuery()) {
                return resultSet.next();
            }
        }
    }

    private double select_for_update_account(Integer pk) throws SQLException {
        LOGGER.info("Select for update in the account with id {}", pk);
        String query = "SELECT balance FROM " + tableName_accounts + " WHERE account_id= ? FOR UPDATE";
        try (PreparedStatement sqlSelect = this.createPreparedStatement(query)) {
            sqlSelect.setInt(1, pk);
            try (ResultSet resultSet = sqlSelect.executeQuery()) {
                if (resultSet.next()) {
                    return resultSet.getDouble("balance");
                } else {
                    throw new SQLException("Account not found for id: " + pk);
                }
            }
        }
    }

    private void insert_movement(Map<String, Object> row, String status) throws SQLException {
        LOGGER.info("Inserting movement with id {} and status {} in the database", row.get("id"), status);
        try (PreparedStatement sqlInsert = this.createPreparedStatement("INSERT INTO "+ tableName_movements +" (id, account_id, amount, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?,  current_timestamp, current_timestamp)")) {
            sqlInsert.setString(1, (String) row.get("id"));
            sqlInsert.setInt(2, (Integer) row.get("account_id"));
            sqlInsert.setDouble(3, (Double) row.get("amount"));
            sqlInsert.setString(4, (String) row.get("type"));
            sqlInsert.setString(5, status);
            sqlInsert.execute();
        }
    }

    private double calculate_new_balance(double currentBalance, double amount, String type) {
        if (TYPE_INCOME.equals(type)) {
            return currentBalance + amount;
        } else {
            return currentBalance - amount;
        }
    }

    private void update_account_balance(Integer pk, double newBalance) throws SQLException {
        String updateQuery = "UPDATE " + tableName_accounts + " SET balance = ?, updated_at = current_timestamp WHERE account_id= ?";
        try (PreparedStatement sqlUpdate = this.createPreparedStatement(updateQuery)) {
            sqlUpdate.setDouble(1, newBalance);
            sqlUpdate.setInt(2, pk);
            sqlUpdate.execute();
        }
    }
}
```

## Implementación del builder

```java
@Builder
public class JobJdbcTransactBuilder extends RegisterSparkBuilder {

    public static final String SERVICE_NAME_BTS = "local.logicalFileDataStore.BATCH";
    public static final String SERVICE_NAME_POSTGRESQL = "local.logicalDbDataStore.BATCH";
    public static final String ALIAS_INPUT = "inputFile";
    public static final String ALIAS_OUTPUT = "output";

    @Override
    public SourcesList registerSources() {
        return SourcesList.builder()
                .add(Source.File.Csv.builder()
                        .alias(ALIAS_INPUT)
                        .serviceName(SERVICE_NAME_BTS)
                        .physicalName("input.csv")
                        .delimiter(",")
                        .header(true)
                        .build())
                .build();
    }

    @Override
    public TransformConfig registerTransform() {
        return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
    }

    @Override
    public TargetsList registerTargets() {
        return TargetsList.builder()
                .add(Target.Jdbc.Transactional.builder()
                        .alias(ALIAS_OUTPUT)
                        .serviceName(SERVICE_NAME_POSTGRESQL)
                        .jdbcTransactionWriter(JdbcTransactional.class)
                        .build())
                .build();
    }
}
```

## Implementación del *Transform*
```Java
public class Transformer implements Transform {

    @Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
        StructType schema = new StructType(new StructField[]{
                DataTypes.createStructField("id", DataTypes.StringType, false),
                DataTypes.createStructField("account_id", DataTypes.IntegerType, false),
                DataTypes.createStructField("amount", DataTypes.DoubleType, false),
                DataTypes.createStructField("type", DataTypes.StringType, false),
        });
        Dataset<Row> typesDataDataset = datasetsFromRead.get(ALIAS_INPUT);

        typesDataDataset = typesDataDataset
                .map((MapFunction<Row, Row>) row -> RowFactory.create(row.getAs("id"), Integer.parseInt(row.getAs("account_id")),
                        Double.parseDouble(row.getAs("amount")), row.getAs("type")), Encoders.row(schema));

        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
        datasetsToWrite.put(ALIAS_OUTPUT, typesDataDataset);
        return datasetsToWrite;
    }
}
```

## Test unitarios del job

### JobJdbcTransactBuilderTest

```java
class JobJdbcTransactBuilderTest {

    private JobJdbcTransactBuilder jobJdbcTransactBuilder;

    @BeforeEach
    void setUp() {
        this.jobJdbcTransactBuilder = new JobJdbcTransactBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobJdbcTransactBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputFile", source.getAlias());
        assertEquals("input.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobJdbcTransactBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobJdbcTransactBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("output", target.getAlias());
    }
}
```

### TransformerTest

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
               new StructField[]{
                       DataTypes.createStructField("id", DataTypes.StringType, false),
                       DataTypes.createStructField("account_id", DataTypes.StringType, false),
                       DataTypes.createStructField("amount", DataTypes.StringType, false),
                       DataTypes.createStructField("type", DataTypes.StringType, false),
               });

        Row firstRow = RowFactory.create("0001", "1", "1.0", "I");
        Row secondRow = RowFactory.create("0002", "2", "2.0", "E");
        Row thirdRow = RowFactory.create("0003", "3", "3.0", "I");

        final List<Row> listRows = Arrays.asList(firstRow, secondRow, thirdRow);

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

        final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("inputFile", dataset)));

        assertNotNull(datasetMap);
        assertEquals(1, datasetMap.size());

        Dataset<Row> outputDataset = datasetMap.get("output");
        assertNotNull(outputDataset);

        List<Row> outputRows = outputDataset.collectAsList();
        assertEquals(3, outputRows.size());

        assertEquals(RowFactory.create("0001", 1, 1.0, "I"), outputRows.get(0));
        assertEquals(RowFactory.create("0002", 2, 2.0, "E"), outputRows.get(1));
        assertEquals(RowFactory.create("0003", 3, 3.0, "I"), outputRows.get(2));
    }
}
```

### JdbcTransactionalTest

```java
class JdbcTransactionalTest {

    private JdbcTransactional jdbcTransactional;

    @BeforeEach
    void setUp() {
        this.jdbcTransactional = spy(new JdbcTransactional());
    }

    @Test
    void write_test() throws SQLException {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("id", DataTypes.StringType, false),
                        DataTypes.createStructField("account_id", DataTypes.IntegerType, false),
                        DataTypes.createStructField("amount", DataTypes.DoubleType, false),
                        DataTypes.createStructField("type", DataTypes.StringType, false),
                });

        List<Map<String, Object>> rows = new ArrayList<>();
        rows.add(Map.of("id", "0001", "account_id", 1, "amount", 32.24, "type", "I"));
        rows.add(Map.of("id", "0002", "account_id", 2, "amount", 10.20, "type", "E"));
        rows.add(Map.of("id", "0003", "account_id", 3, "amount", 112.45, "type", "E"));
        rows.add(Map.of("id", "0004", "account_id", 4, "amount", 3.00, "type", "I"));

        JdbcConnectionHandler conn = mock(JdbcConnectionHandler.class);

        jdbcTransactional.setConnection(conn);

        PreparedStatement psMovements = mock(PreparedStatement.class);
        PreparedStatement psSelecForUpdate = mock(PreparedStatement.class);
        PreparedStatement anyPreparedStatement = mock(PreparedStatement.class);

        when(conn.getPreparedStatement(any(String.class))).thenAnswer(invocation -> {
            String query = invocation.getArgument(0, String.class);
            if (query.contains("SELECT id FROM schema_test.movements")) {
                return psMovements;
            } else if (query.contains("SELECT balance FROM schema_test.accounts WHERE account_id= ? FOR UPDATE")) {
                return psSelecForUpdate;
            } else {
                return anyPreparedStatement;
            }
        });

        ResultSet mockResultSetBalance = mock(ResultSet.class);
        when(mockResultSetBalance.next()).thenReturn(true);
        when(mockResultSetBalance.getDouble("balance")).thenReturn(100.0);

        when(psSelecForUpdate.executeQuery()).thenReturn(mockResultSetBalance);
        when(psMovements.executeQuery()).thenReturn(mock(ResultSet.class));

        for(Map<String, Object> row : rows) {
            jdbcTransactional.write(row, schema);
        }

        verify(jdbcTransactional, times(4)).createPreparedStatement("SELECT id FROM schema_test.movements WHERE id = ?");
        verify(jdbcTransactional, times(4)).createPreparedStatement("SELECT balance FROM schema_test.accounts WHERE account_id= ? FOR UPDATE");
    }

    @Test
    void write_test_movement_exists() throws SQLException {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("id", DataTypes.StringType, false),
                        DataTypes.createStructField("account_id", DataTypes.IntegerType, false),
                        DataTypes.createStructField("amount", DataTypes.DoubleType, false),
                        DataTypes.createStructField("type", DataTypes.StringType, false),
                });

        List<Map<String, Object>> rows = new ArrayList<>();
        rows.add(Map.of("id", "0001", "account_id", 1, "amount", 32.24, "type", "I"));
        rows.add(Map.of("id", "0002", "account_id", 2, "amount", 10.20, "type", "E"));

        JdbcConnectionHandler conn = mock(JdbcConnectionHandler.class);

        jdbcTransactional.setConnection(conn);

        PreparedStatement psMovements = mock(PreparedStatement.class);
        PreparedStatement anyPreparedStatement = mock(PreparedStatement.class);

        when(conn.getPreparedStatement(any(String.class))).thenAnswer(invocation -> {
            String query = invocation.getArgument(0, String.class);
            if (query.contains("SELECT id FROM schema_test.movements")) {
                return psMovements;
            } else{
                return anyPreparedStatement;
            }
        });

        ResultSet mockResultSet = mock(ResultSet.class);
        when(mockResultSet.next()).thenReturn(true);
        when(psMovements.executeQuery()).thenReturn(mockResultSet);

        for(Map<String, Object> row : rows) {
            jdbcTransactional.write(row, schema);
        }

        verify(jdbcTransactional, times(2)).createPreparedStatement("SELECT id FROM schema_test.movements WHERE id = ?");
        verify(jdbcTransactional, times(0)).createPreparedStatement("SELECT balance FROM schema_test.accounts WHERE account_id= ? FOR UPDATE");
    }


    @Test
    void write_test_error() throws SQLException {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("id", DataTypes.StringType, false),
                        DataTypes.createStructField("account_id", DataTypes.IntegerType, false),
                        DataTypes.createStructField("amount", DataTypes.DoubleType, false),
                        DataTypes.createStructField("type", DataTypes.StringType, false),
                });

        Map<String, Object> row = Map.of("id", "0001", "account_id", 1, "amount", 32.24, "type", "I");

        PreparedStatement preparedStatement = mock(PreparedStatement.class);
        JdbcConnectionHandler conn = mock(JdbcConnectionHandler.class);

        jdbcTransactional.setConnection(conn);
        when(conn.getPreparedStatement(any(String.class))).thenReturn(preparedStatement);
        when(preparedStatement.executeQuery()).thenThrow(new SQLException("Error"));

        PreparedStatement psSelecForUpdate = mock(PreparedStatement.class);
        PreparedStatement anyPreparedStatement = mock(PreparedStatement.class);

        when(conn.getPreparedStatement(any(String.class))).thenAnswer(invocation -> {
            String query = invocation.getArgument(0, String.class);
            if (query.contains("SELECT balance FROM schema_test.accounts WHERE account_id= ? FOR UPDATE")) {
                return psSelecForUpdate; 
            } else {
                return anyPreparedStatement;
            }
        });

        ResultSet mockResultSetBalance = mock(ResultSet.class);
        when(mockResultSetBalance.next()).thenReturn(false);

        when(anyPreparedStatement.executeQuery()).thenReturn(mock(ResultSet.class));
        when(psSelecForUpdate.executeQuery()).thenReturn(mockResultSetBalance);

        assertThrows(LrbaApplicationException.class, () -> {
            jdbcTransactional.write(row, schema);
        });
    }
}
```


# 11-JdbcTransactionalJob/04-ExecuteJob.md
# 4. Cómo ejecutar el job

En esta fase vamos a ejecutar nuestro *job* en local y ver cómo se comporta.

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```
### Analizar el resultado

Se puede observar que en la tabla de movimientos aparecen los nuevos registros con la información
obtenida del fichero de entrada. 

| id        | account_id | amount | type | status | created_at | updated_at |
|:----------|:-----------|:-------|:-----|:-------|:-----------|:-----------|
| 000000001 | 1          | 23.34  | I    | P      | 2023-01-01 | 2023-01-01 |
| 000000002 | 2          | 60.45  | E    | L      | 2023-02-01 | 2023-02-01 |
| 000000003 | 3          | 70.65  | I    | P      | 2023-03-01 | 2023-03-01 |
| 000000004 | 4          | 80.17  | E    | L      | 2023-04-01 | 2023-04-01 |
| 000000005 | 5          | 90.22  | I    | P      | 2023-05-01 | 2023-05-01 |
| 000000006 | 6          | 34.45  | E    | L      | 2023-06-01 | 2023-06-01 |
| 000000007 | 7          | 110.65 | I    | P      | 2023-07-01 | 2023-07-01 |
| 000000008 | 8          | 55.10  | E    | L      | 2023-08-01 | 2023-08-01 |
| 000000009 | 9          | 450.15 | I    | P      | 2023-09-01 | 2023-09-01 |
| 000000010 | 10         | 140.56 | E    | L      | 2023-10-01 | 2023-10-01 |
| 000000011 | 1          | 123.45 | E    | P      | 2024-10-29 | 2024-10-29 |
| 000000012 | 2          | 2.56   | E    | L      | 2024-10-29 | 2024-10-29 |
| 000000013 | 3          | 11.67  | I    | L      | 2024-10-29 | 2024-10-29 |
| 000000014 | 4          | 16.78  | E    | L      | 2024-10-29 | 2024-10-29 |
| 000000015 | 5          | 745.89 | E    | P      | 2024-10-29 | 2024-10-29 |
| 000000016 | 6          | 3.90   | E    | L      | 2024-10-29 | 2024-10-29 |
| 000000017 | 7          | 150.01 | I    | L      | 2024-10-29 | 2024-10-29 |
| 000000018 | 8          | 34.12  | E    | L      | 2024-10-29 | 2024-10-29 |
| 000000019 | 9          | 21.23  | I    | L      | 2024-10-29 | 2024-10-29 |
| 000000020 | 10         | 16.34  | E    | L      | 2024-10-29 | 2024-10-29 |


Ademaś, en la tabla de cuentas se ven actualizados los saldos.

| account_id | account_number  | balance  | created_at | updated_at |
|:-----------|:----------------|:---------|:-----------|:-----------|
| 1          | 123456789012345 | 10.32    | 2023-01-01 | 2023-01-01 |
| 2          | 234567890123456 | 341.58   | 2023-02-01 | 2024-10-29 |
| 3          | 345678901234567 | 1451.45  | 2023-03-01 | 2024-10-29 |
| 4          | 456789012345678 | 383.35   | 2023-04-01 | 2024-10-29 |
| 5          | 567890123456789 | 543.34   | 2023-05-01 | 2023-05-01 |
| 6          | 678901234567890 | 599.30   | 2023-06-01 | 2024-10-29 |
| 7          | 789012345678901 | 7516.44  | 2023-07-01 | 2024-10-29 |
| 8          | 890123456789012 | 3432.10  | 2023-08-01 | 2024-10-29 |
| 9          | 901234567890123 | 13900.40 | 2023-09-01 | 2024-10-29 |
| 10         | 012345678901234 | 1028.98  | 2023-10-01 | 2024-10-29 |




# 12-GrpcBEASendEvents/01-Introduction.md
# 1. Introducción

BEA (acrónimo de Arquitectura de Eventos de Negocio, Business Events Architecture en inglés) es la evolución de las 
Arquitecturas de Eventos de BBVA que persigue añadir valor a las iniciativas de negocio siendo más proactivos en la 
relación con nuestros clientes y gestores y rediseñando nuestros procesos de forma que podamos evolucionarlos desde la 
aproximación actual (orientada a batch) para poder realizarse en tiempo real e incluir nuevas capacidades como la 
inferencia online.

Más info en: [¿Que es BEA?](https://platform.bbva.com/bea/documentation/1ULLDbeJBpIz5DANLctgzbF_SdGArroPWsrk42e-Z2mY/01-que-es-bea)

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job que realize las siguientes acciones:
1. Leer de un fichero de origen.
2. Transformar los datos de dicho fichero para generar eventos.
3. Publicar dichos eventos en el canal de BEA. 

Se mostrará un ejemplo simple de como realizar dichas operaciones.
Además, se desarrollarán los tests unitarios para el código.

**Importante**:<br/>
El uso de BEA esta securizado a dos niveles:
1. Mediante Mutual TLS a través del bot de LRBA
2. Mediante los permisos definidos para que un determinado job pueda operar un tipo de eventos concreto.

**Por este motivo no es posible ejecutar un job de BEA en local**


# 12-GrpcBEASendEvents/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
[El CLI de LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) ayuda a generar el código fuente, construir el **job**, probarlo y ejecutarlo en un entorno local. Lo único que se necesita es acceso al terminal del sistema.

Para ejecutar los test unitarios, es posible ejecutar `lrba test`.<br/>
Si la tecnología es Java, ejecutará `mvn clean test`.<br/>
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.

## Consola Ether y Catálogo de Eventos de Negocio
Previamente a la publicación de Eventos de Negocio es necesario seguir los pasos descritos en la documentación oficial 
de BEA: [Como usar BEA -> Proceso de uso](https://platform.bbva.com/bea/documentation/1OE_wSoJSNyWFDXNWp1rfcXcDeqWGoowo2ImElYez66w/02-como-usar-bea/02-3-proceso-de-uso)

## Servicio expuesto por BEA
BEA ha expuesto un servicio que permite a un job autorizado publicar eventos.

**A tener en cuenta:**
- Dichos eventos estarán asociados a un tipo de evento previamente registrado en el catálogo de eventos.
- El envío de cada uno de los eventos incluirá una serie de cabeceras funcionales propias de dicho evento.
- De cara a optimizar la publicación de eventos en BEA, se hará en tramas o bulks de un determinado tamaño, medido 
en número máximo de eventos por bulk.

### Modelado del tipo de evento
Un evento BEA se identificará por los atributos:
* eventID: Es el identificador único del evento.
* majorVersion: Número de versión major del evento que se desea emitir.
* minorVersion: Número de versión minor del evento que se desea emitir.

De cara a la operativa que se ha habilitado desde LRBA para la publicación de eventos, se ofrece la opción de configurar el tamaño del bulk:
* bulkSize: Máximo número de eventos a enviar en un bulk.

**En caso de no indicarlo el bulkSize por defecto tiene un valor de 100.**



# 12-GrpcBEASendEvents/03-HowToImplementTheJob.md
# 3. Cómo implementar el job
Un job aplicativo podría usar cualquiera de los origenes de datos disponibles en la arquitectura LRBA.<br/>
Para el ejemplo propuesto se van a leer los datos de un fichero CSV.<br/>
En este job se va a:

1. Leer de un *Source File Csv*. Dicho fichero contendrá eventos junto con sus cabeceras asociadas.  
   La estructura de dicho fichero será:

```csv
jsonEvent|aap|authorizationCode|authorizationVersion|branchCode|channelCode|clientDocument|clientIdentificationType|contactIdentifier|countryCode|currencyCode|entityCode|environCode|languageCode|operativeBranchCode|operativeEntityCode|productCode|secondaryCurrencyCode
{"isbn": "8", "title": "title1", "author": "author1"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title2", "author": "author2"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title3", "author": "author3"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title4", "author": "author4"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title5", "author": "author5"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title6", "author": "author6"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title7", "author": "author7"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title8", "author": "author8"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title9", "author": "author9"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title10", "author": "author10"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title11", "author": "author11"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title12", "author": "author12"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title13", "author": "author13"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title14", "author": "author14"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title15", "author": "author15"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title1", "author": "author16"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title2", "author": "author26"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title3", "author": "author36"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title4", "author": "author46"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title5", "author": "author56"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title6", "author": "author66"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title7", "author": "author76"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title8", "author": "author86"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title9", "author": "author96"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title10", "author": "author106"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title11", "author": "author116"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title12", "author": "author126"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title13", "author": "author136"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title14", "author": "author146"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title15", "author": "author156"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title1", "author": "author17"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title2", "author": "author27"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title3", "author": "author37"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title4", "author": "author47"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title5", "author": "author57"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title6", "author": "author67"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title7", "author": "author77"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title8", "author": "author87"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title9", "author": "author97"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title10", "author": "author107"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title11", "author": "author117"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title12", "author": "author127"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title13", "author": "author137"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title14", "author": "author147"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title15", "author": "author157"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title1", "author": "author18"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title2", "author": "author28"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title3", "author": "author38"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title4", "author": "author48"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title5", "author": "author58"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title6", "author": "author68"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title7", "author": "author78"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title8", "author": "author88"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title9", "author": "author98"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title10", "author": "author108"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title11", "author": "author118"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title12", "author": "author128"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title13", "author": "author138"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title14", "author": "author148"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title15", "author": "author158"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title1", "author": "author19"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title2", "author": "author29"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title3", "author": "author39"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title4", "author": "author49"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title5", "author": "author59"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title6", "author": "author69"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title7", "author": "author79"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title8", "author": "author89"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title9", "author": "author99"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title10", "author": "author109"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title11", "author": "author119"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title12", "author": "author129"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title13", "author": "author139"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title14", "author": "author149"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
{"isbn": "8", "title": "title15", "author": "author159"}|00000013|000000014|05|9999|02|12345678Z|1|23524K52L45U234U53|us|EUR|0182|01|ZZ|0001|0000|4501|EUR
```
2. Transformar las filas leidas en un *dataset* de tipo `SparkEventBean`. 
3. Publicar los eventos en el canal de BEA.
  

## Clases a implementar
Para desarrollar este conector es necesario implementar algunas clases de la arquitectura.

## Implementación del builder
### Sources
Se crea un *source* de tipo `File.Csv` para leer el fichero csv.<br/> 
Se indican los atributos:
* alias: Alias para cada *source* JDBC
* physicalName: Physical name perteneciente a la tabla que quieres leer. Recuerda la sintaxis **schema.nombre_tabla**.
* serviceName: Service name definido para conectarse al BTS. Recuerda la sintaxis bts.{UUAA}.BATCH.
* sql: Consulta para recuperar los datos del source.
* header: Se indica que el CSV tiene cabecera.
* delimiter: Se indica el delimitador de campos del CSV. 

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("beaEvent")
                    .physicalName("events.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .sql("SELECT * FROM beaEvent")
                    .header(true)
                    .delimiter("|")
                    .build())
            .build();
}
```

### Transform
* En el método `registerTransform` se indica que se va a realizar una transformación de los registros leídos.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets
Se crea un *target* que va a publicar los eventos en BEA.

#### Target Bea.Publish
Con el fin de facilitar el uso del conector de BEA para publicar eventos, desde la Arquitectura LRBA se ha provisto del target `Target.Bea.Publish`.<br/>
Este target dispone de un builder para registrar el tipo de evento a publicar en BEA

```java
    public static class GrpcBeaTargetBuilder extends TargetBuilder<GrpcBeaTargetBuilder, GrpcBeaTarget> {
    private String eventId;
    private Integer majorVersion;
    private Integer minorVersion;
    private Integer bulkSize;

    @Override
    public GrpcBeaTarget build() {
        this.physicalName("grpc");
        this.serviceName("noop.LRBA.BATCH");
        return new GrpcBeaTarget(getThis()).validate();
    }
```
A destacar:
- Obliga a indicar los atributos:
  - eventID: Es el identificador único del evento.
  - majorVersion: Número de versión major del evento que se desea emitir.
  - minorVersion: Número de versión minor del evento que se desea emitir.  
- Mete por defecto los siguientes valores:
  - physicalName: `grpc`
  - serviceName: `noop.LRBA.BATCH`
- El bulkSize se rellena con un tamaño por defecto de 100. Se permite al aplicativo modificar este valor en caso de considerarlo necesario. 

#### Registrar el target Bea.Publish
Se registra un *target* que va a publicar los eventos en BEA.
```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.Bea.Publish.builder()
                    .alias("beaEventProcessed")
                    .eventId("bea00007")
                    .majorVersion(1)
                    .minorVersion(0)
                    .bulkSize(150)
                    .build())
            .build();
}
```
Como se puede observar en el trozo de código, se usará el Builder proporcionado por la arquitectura de BEA, 
`Target.Bea.Publish.builder()`

## Implementación del Transformer
Transformar los registros leídos del CSV usando el encoder del bean `SparkEventBean`

#### Objeto de dominio SparkEventBean
Con el fin de facilitar el uso del conector de BEA para publicar eventos, desde la Arquitectura LRBA se ha provisto de la clase `SparkEventBean`.<br/>
Esta clase contiene la estructura definida por el servicio de BEA para cada evento publicado.<br>
Dicha estructura está compuesta por: 
  * El json del evento
  * Las cabeceras propias del evento

Para mas información sobre las cabeceras del evento, consultar [Cabeceras del evento](../../utilities/spark/connectors/07-BEA.md)


```java
/**
 * Bean to encapsulate a BEA Event
 */
public class SparkEventBean implements Serializable {

    private String jsonEvent;
    private String aap;
    private String authorizationCode;
    private String authorizationVersion;
    private String branchCode;
    private String channelCode;
    private String clientDocument;
    private String clientIdentificationType;
    private String contactIdentifier;
    private String countryCode;
    private String currencyCode;
    private String entityCode;
    private String environCode;
    private String languageCode;
    private String operativeBranchCode;
    private String operativeEntityCode;
    private String productCode;
    private String secondaryCurrencyCode;
```

Ir a la clase *Transformer.java* y modificar el método *transform* con el siguiente bloque de código.
```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<SparkEventBean> dataset = datasetsFromRead.get("beaEvent").as(Encoders.bean(SparkEventBean.class));
    datasetsToWrite.put("beaEventProcessed", dataset.toDF());
    return datasetsToWrite;
}
```

## Test unitarios del job

### Builder

```java
class JobBeaEventTestBuilderTest {

  private JobBeaEventTestBuilder jobBeaEventTestBuilder;

  @BeforeEach
  void setUp() {
    this.jobBeaEventTestBuilder = new JobBeaEventTestBuilder();
  }

  @Test
  void registerSources_na_SourceList() {
    final SourcesList sourcesList = this.jobBeaEventTestBuilder.registerSources();
    assertNotNull(sourcesList);
    assertNotNull(sourcesList.getSources());
    assertEquals(1, sourcesList.getSources().size());

    final Source source = sourcesList.getSources().get(0);
    assertNotNull(source);
    assertEquals("beaEvent", source.getAlias());
    assertEquals("events.csv", source.getPhysicalName());
    assertEquals("bts.YOUR_UUAA.BATCH", source.getServiceName());
    assertEquals("SELECT * FROM beaEvent", source.getSql());
  }

  @Test
  void registerTransform_na_Transform() {
    final TransformConfig transformConfig = this.jobBeaEventTestBuilder.registerTransform();
    assertNotNull(transformConfig);
    assertNotNull(transformConfig.getTransform());
  }

  @Test
  void registerTargets_na_TargetList() {
    final TargetsList targetsList = this.jobBeaEventTestBuilder.registerTargets();
    assertNotNull(targetsList);
    assertNotNull(targetsList.getTargets());
    assertEquals(1, targetsList.getTargets().size());

    final Target target = targetsList.getTargets().get(0);
    assertNotNull(target);
    assertEquals(GrpcBeaTarget.class, target.getClass());
    GrpcBeaTarget grpcBeaTarget = (GrpcBeaTarget) target;
    assertEquals("beaEventProcessed", grpcBeaTarget.getAlias());
    assertEquals("bea00007", grpcBeaTarget.getEventId());
    assertEquals(1, grpcBeaTarget.getMajorVersion());
    assertEquals(0, grpcBeaTarget.getMinorVersion());
    assertEquals(150, grpcBeaTarget.getBulkSize());
    assertEquals("beaEventProcessed", grpcBeaTarget.getAlias());
    assertEquals("noop.LRBA.BATCH", grpcBeaTarget.getServiceName());
    assertEquals("grpc", grpcBeaTarget.getPhysicalName());
  }

}
```

### Transform
Se recomienda utilizar la clase `LRBASparkTest` que proporciona la arquitectura LRBA para realizar los test del *job*.

```java
class TransformerTest extends LRBASparkTest {
  private Transformer transformer;

  @BeforeEach
  void setUp() {
    this.transformer = new Transformer();
  }

  @Test
  void transform_Output() {
    StructType schema = DataTypes.createStructType(
            new StructField[]{
                    DataTypes.createStructField("jsonEvent", DataTypes.StringType, false),
                    DataTypes.createStructField("aap", DataTypes.StringType, false),
                    DataTypes.createStructField("authorizationCode", DataTypes.StringType, false),
                    DataTypes.createStructField("authorizationVersion", DataTypes.StringType, false),
                    DataTypes.createStructField("branchCode", DataTypes.StringType, false),
                    DataTypes.createStructField("channelCode", DataTypes.StringType, false),
                    DataTypes.createStructField("clientDocument", DataTypes.StringType, false),
                    DataTypes.createStructField("clientIdentificationType", DataTypes.StringType, false),
                    DataTypes.createStructField("contactIdentifier", DataTypes.StringType, false),
                    DataTypes.createStructField("countryCode", DataTypes.StringType, false),
                    DataTypes.createStructField("currencyCode", DataTypes.StringType, false),
                    DataTypes.createStructField("entityCode", DataTypes.StringType, false),
                    DataTypes.createStructField("environCode", DataTypes.StringType, false),
                    DataTypes.createStructField("languageCode", DataTypes.StringType, false),
                    DataTypes.createStructField("operativeBranchCode", DataTypes.StringType, false),
                    DataTypes.createStructField("operativeEntityCode", DataTypes.StringType, false),
                    DataTypes.createStructField("productCode", DataTypes.StringType, false),
                    DataTypes.createStructField("secondaryCurrencyCode", DataTypes.StringType, false),
            });

    Row firstRow = RowFactory.create("{\"isbn\": \"8\", \"title\": \"title1\", \"author\": \"author1\"}", "00000013", "000000014", "05", "9999", "02", "12345678Z", "1", "23524K52L45U234U53", "us", "EUR", "0182", "01", "ZZ", "0001", "0000", "4501", "EUR");
    Row secondRow = RowFactory.create("{\"isbn\": \"8\", \"title\": \"title2\", \"author\": \"author2\"}", "00000013", "000000014", "05", "9999", "02", "12345678Z", "1", "23524K52L45U234U53", "us", "EUR", "0182", "01", "ZZ", "0001", "0000", "4501", "EUR");
    Row thirdRow = RowFactory.create("{\"isbn\": \"8\", \"title\": \"title3\", \"author\": \"author3\"}", "00000013", "000000014", "05", "9999", "02", "12345678Z", "1", "23524K52L45U234U53", "us", "EUR", "0182", "01", "ZZ", "0001", "0000", "4501", "EUR");

    final List<Row> listRows = Arrays.asList(firstRow, secondRow, thirdRow);

    DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
    Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

    final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("beaEvent", dataset)));

    assertNotNull(datasetMap);
    assertEquals(1, datasetMap.size());

    Dataset<SparkEventBean> returnedDs = datasetMap.get("beaEventProcessed").as(Encoders.bean(SparkEventBean.class));
    final List<SparkEventBean> rows = datasetToTargetData(returnedDs, SparkEventBean.class);

    assertEquals(3, rows.size());
    assertEquals("{\"isbn\": \"8\", \"title\": \"title1\", \"author\": \"author1\"}", rows.get(0).getJsonEvent());
    assertEquals("00000013", rows.get(0).getAap());
    assertEquals("000000014", rows.get(0).getAuthorizationCode());
    assertEquals("05", rows.get(0).getAuthorizationVersion());
    assertEquals("9999", rows.get(0).getBranchCode());
    assertEquals("02", rows.get(0).getChannelCode());
    assertEquals("12345678Z", rows.get(0).getClientDocument());
    assertEquals("1", rows.get(0).getClientIdentificationType());
    assertEquals("23524K52L45U234U53", rows.get(0).getContactIdentifier());
    assertEquals("us", rows.get(0).getCountryCode());
    assertEquals("EUR", rows.get(0).getCurrencyCode());
    assertEquals("0182", rows.get(0).getEntityCode());
    assertEquals("01", rows.get(0).getEnvironCode());
    assertEquals("ZZ", rows.get(0).getLanguageCode());
    assertEquals("0001", rows.get(0).getOperativeBranchCode());
    assertEquals("0000", rows.get(0).getOperativeEntityCode());
    assertEquals("4501", rows.get(0).getProductCode());
    assertEquals("EUR", rows.get(0).getSecondaryCurrencyCode());

    assertEquals("{\"isbn\": \"8\", \"title\": \"title2\", \"author\": \"author2\"}", rows.get(1).getJsonEvent());
    assertEquals("00000013", rows.get(1).getAap());
    assertEquals("000000014", rows.get(1).getAuthorizationCode());
    assertEquals("05", rows.get(1).getAuthorizationVersion());
    assertEquals("9999", rows.get(1).getBranchCode());
    assertEquals("02", rows.get(1).getChannelCode());
    assertEquals("12345678Z", rows.get(1).getClientDocument());
    assertEquals("1", rows.get(1).getClientIdentificationType());
    assertEquals("23524K52L45U234U53", rows.get(1).getContactIdentifier());
    assertEquals("us", rows.get(1).getCountryCode());
    assertEquals("EUR", rows.get(1).getCurrencyCode());
    assertEquals("0182", rows.get(1).getEntityCode());
    assertEquals("01", rows.get(1).getEnvironCode());
    assertEquals("ZZ", rows.get(1).getLanguageCode());
    assertEquals("0001", rows.get(1).getOperativeBranchCode());
    assertEquals("0000", rows.get(1).getOperativeEntityCode());
    assertEquals("4501", rows.get(1).getProductCode());
    assertEquals("EUR", rows.get(1).getSecondaryCurrencyCode());

    assertEquals("{\"isbn\": \"8\", \"title\": \"title3\", \"author\": \"author3\"}", rows.get(2).getJsonEvent());
    assertEquals("00000013", rows.get(2).getAap());
    assertEquals("000000014", rows.get(2).getAuthorizationCode());
    assertEquals("05", rows.get(2).getAuthorizationVersion());
    assertEquals("9999", rows.get(2).getBranchCode());
    assertEquals("02", rows.get(2).getChannelCode());
    assertEquals("12345678Z", rows.get(2).getClientDocument());
    assertEquals("1", rows.get(2).getClientIdentificationType());
    assertEquals("23524K52L45U234U53", rows.get(2).getContactIdentifier());
    assertEquals("us", rows.get(2).getCountryCode());
    assertEquals("EUR", rows.get(2).getCurrencyCode());
    assertEquals("0182", rows.get(2).getEntityCode());
    assertEquals("01", rows.get(2).getEnvironCode());
    assertEquals("ZZ", rows.get(2).getLanguageCode());
    assertEquals("0001", rows.get(2).getOperativeBranchCode());
    assertEquals("0000", rows.get(2).getOperativeEntityCode());
    assertEquals("4501", rows.get(2).getProductCode());
    assertEquals("EUR", rows.get(2).getSecondaryCurrencyCode());
  }

}
```

# 12-GrpcBEASendEvents/04-ExecuteJob.md
# 4. Ejecutar el Job
Cómo ya se ha comentado anteriormente, las restricciones de seguridad impiden ejecutar un job de BEA en local por lo que 
deberá ser ejecutado en el cluster.

## Ejecutar el job en el clúster
1. Disponer de un evento regitrado en el catalogo de eventos de negocio siguiendo los pasos descritos en: [Como usar BEA -> Proceso de uso](https://platform.bbva.com/bea/documentation/1OE_wSoJSNyWFDXNWp1rfcXcDeqWGoowo2ImElYez66w/02-como-usar-bea/02-3-proceso-de-uso)  
2. Hacer push del código del *job* a Bitbucket.
3. Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 13-ReadTransformWithApachePOI/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se lean documentos de Microsoft como Excel.

# 13-ReadTransformWithApachePOI/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 13-ReadTransformWithApachePOI/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a utilizar un *Source Binario* para leer los datos de documentos XSLX. Se procesarán utilizando Apache POI para generar un *dataset* y guardarlos en un fichero CSV.  

## Ficheros XSLX

Para este job debemos crear dos ficheros `.xslx` distintos con los siguientes datos:

***local-execution/files/person-data.xlsx***

| ENTIDAD | DNI  | NOMBRE    | TELEFONO |
|---------|------|-----------|----------|
| 182     | 0001 | John Doe  | 123-456  |
| 182     | 0002 | Mike Doe  | 123-567  |
| 182     | 0003 | Paul Doe  | 123-678  |
| 182     | 0004 | Shane Doe | 123-789  |

***local-execution/files/email-data.xlsx***

| DNI  | EMAIL              |
|------|--------------------|
| 0001 | johndoe@gmail.com  |
| 0002 | mikedoe@gmail.com  |
| 0003 | pauldoe@gmail.com  |
| 0004 | shanedoe@gmail.com |

## pom.xml

Añade la dependencia externa de Apache POI.
```xml
<dependencies>
    <dependency>
        <groupId>com.bbva.lrba.external-modules</groupId>
        <artifactId>apachePOI</artifactId>
    </dependency>
</dependencies>
```

## Implementación del builder

### Sources

Se crea un *source* de tipo fichero binario y se le especifica un *physicalName* que contenga un wildcard que abarque ambos ficheros excel.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Binary.builder()
                    .alias("binaryAlias")
                    .physicalName("files/*.xlsx")
                    .serviceName(bts.YOUR_UUAA.BATCH)
                    .sql("SELECT * FROM binaryAlias")
                    .build())
            .build();
}
```

### Transform

En el método `registerTransform` se indica cuál es nuestra clase *Transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets

Se crea un *target* que va a escribir los datos en un CSV.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Csv.builder()
                    .alias("csvTarget")
                    .physicalName("labs/outputs/result.csv")
                    .serviceName(bts.YOUR_UUAA.BATCH)
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

## Implementación del transformer

Implementamos el método *transform* para procesar los datos leídos y unirlos utilizando la columna *DNI*.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<Row> firstDataset = null;
    Dataset<Row> secondDataset = null;

    WindowSpec spec = Window.orderBy(functions.col("path").asc());
    Dataset<Row> datasetWithId = datasetsFromRead.get("binaryAlias")
                .withColumn("id", functions.row_number().over(spec));

    Dataset<Row> firstRow = datasetWithId.filter(functions.col("id").equalTo(1));
    Dataset<Row> secondRow = datasetWithId.filter(functions.col("id").equalTo(2));
    

    try {
        firstDataset = datasetFromBinaryRow(firstRow.first());
        secondDataset = datasetFromBinaryRow(secondRow.first());
    } catch (IOException e) {
        
        LOGGER.error("Error while reading the binary content:", e);
        throw new LrbaApplicationException("Error while reading the binary content", 6);
        
    }

    Dataset<Row> datasetUpdated = firstDataset.join(secondDataset, "DNI").toDF();
    datasetsToWrite.put("csvTarget", datasetUpdated);

    return datasetsToWrite;
}
```

Cada fila del dataset obtenido por la lectura de ficheros binarios tiene siempre cuatro columnas:

* `path`: representa la ruta del fichero al que pertenece la fila.
* `modificationTime`: es la fecha de la última modificación del fichero.
* `length`: muestra la longitud del fichero.
* `content`: contiene todo el contenido en binario del fichero.

Para transformar cada una de estas filas en datasets se ha utilizado el método privado `datasetFromBinaryRow` que utiliza elementos de la dependencia externa Apache POI:

```java
private Dataset<Row> datasetFromBinaryRow(Row row) throws IOException {
    byte[] content = row.getAs("content");
    InputStream stream = new ByteArrayInputStream(content);
    Workbook workbook = WorkbookFactory.create(stream);
    
    List<Row> rowList = new ArrayList<>();
    StructType schema = null;
    List<StructField> structs = new ArrayList<>();
    List<String> rowValues;

    Sheet sheet = workbook.getSheetAt(0);
    for(org.apache.poi.ss.usermodel.Row poiRow : sheet) {
        if (schema == null) {
            for (Cell cell : poiRow) {
                structs.add(DataTypes.createStructField(cell.getStringCellValue(), DataTypes.StringType, true));
            }
            schema = DataTypes.createStructType(structs);
        } else {
            rowValues = new ArrayList<>();
            for (Cell cell : poiRow) {
                switch (cell.getCellType()) {
                    case STRING:
                        rowValues.add(cell.getStringCellValue());
                        break;
                    case NUMERIC:
                        rowValues.add(String.valueOf((int) cell.getNumericCellValue()));
                        break;
                }
            }
            if (!rowValues.isEmpty()) {
                rowList.add(RowFactory.create(rowValues.toArray()));
            }
        }
    }
    workbook.close();

    DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
    return datasetUtils.createDataFrame(rowList, schema);
}
```

## Test unitarios del job

### Builder

```java
import com.bbva.lrba.builder.spark.domain.SourcesList;
import com.bbva.lrba.builder.spark.domain.TargetsList;
import com.bbva.lrba.spark.domain.datasource.Source;
import com.bbva.lrba.spark.domain.datatarget.Target;
import com.bbva.lrba.spark.domain.transform.TransformConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class JobReadBinaryfileBuilderTest {

    private JobReadBinaryfileBuilder jobReadBinaryfileBuilder;

    @BeforeEach
    void setUp() {
        this.jobReadBinaryfileBuilder = new JobReadBinaryfileBuilder();
    }

    @Test
    void registerSources_na_SourceList() {

        final SourcesList sourcesList = this.jobReadBinaryfileBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("binaryAlias", source.getAlias());
        assertEquals("files/*.xlsx", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobReadBinaryfileBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobReadBinaryfileBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("csvTarget", target.getAlias());
        assertEquals("labs/outputs/result.csv", target.getPhysicalName());
    }

}
```

### Transformer

Para testear nuestro transformer, necesitaremos crear unos ficheros excel exclusivamente dedicados a las pruebas unitarias. Estos ficheros se leerán en formato binario y se van a inyectar mediante la columna content del dataset de entrada. Luego comprobaremos que estos ficheros se han unido correctamente en un solo dataset.

***testfiles/person-test-data.xlsx***

| ENTIDAD | DNI  | NOMBRE    | TELEFONO |
|---------|------|-----------|----------|
| 182     | 0001 | John Doe  | 123-456  |

***testfiles/email-data.xlsx***

| DNI  | EMAIL              |
|------|--------------------|
| 0001 | johndoe@gmail.com  |

```java
class TransformerTest extends LRBASparkTest {
    
    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        Path firstFilePath = Paths.get("<FROM_CONTENT_ROOT>/testfiles/email-test-data.xlsx");
        Path secondFilePath = Paths.get("<FROM_CONTENT_ROOT>/testfiles/person-test-data.xlsx");

        byte[] firstFile = null;
        byte[] secondFile = null;
        try {
            firstFile = Files.readAllBytes(firstFilePath);
            secondFile = Files.readAllBytes(secondFilePath);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        StructType schema = DataTypes.createStructType(
               new StructField[]{
                       DataTypes.createStructField("path", DataTypes.StringType, false),
                       DataTypes.createStructField("modificationTime", DataTypes.StringType, false),
                       DataTypes.createStructField("length", DataTypes.StringType, false),
                       DataTypes.createStructField("content", DataTypes.BinaryType, false),
               });
        Row firstRow = RowFactory.create("file:/home/", "2024-11-15T13:01:02.268+01:00", "7", firstFile);
        Row secondRow = RowFactory.create("file:/home/", "2024-11-15T13:01:02.268+01:01", "7", secondFile);

        final List<Row> listRows = Arrays.asList(firstRow, secondRow);

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);

        final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("binaryAlias", dataset)));

        assertNotNull(datasetMap);
        assertEquals(1, datasetMap.size());

        Dataset<Row> returnedDs = datasetMap.get("csvTarget");
        String[] datasetColumns = returnedDs.columns();
        List<Row> returnedDsList = returnedDs.collectAsList();

        assertNotNull(returnedDs);
        assertEquals(1, returnedDs.count());
        assertEquals(5, datasetColumns.length);
        assertEquals("DNI", datasetColumns[0]);
        assertEquals("EMAIL", datasetColumns[1]);
        assertEquals("ENTIDAD", datasetColumns[2]);
        assertEquals("NOMBRE", datasetColumns[3]);
        assertEquals("TELEFONO", datasetColumns[4]);

        assertEquals("1", returnedDsList.get(0).get(0));
        assertEquals("johndoe@gmail.com", returnedDsList.get(0).get(1));
        assertEquals("182", returnedDsList.get(0).get(2));
        assertEquals("John Doe", returnedDsList.get(0).get(3));
        assertEquals("123-456", returnedDsList.get(0).get(4));
    }
}
```

# 13-ReadTransformWithApachePOI/04-ExecuteJob.md
# 4. Cómo ejecutar el job

En esta fase vamos a ejecutar nuestro *job* en local y ver cómo se comporta.

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```
### Analizar el resultado

Se puede observar que en el `.csv` que obtenemos como resultado aparecen los datos de las personas junto a su email.

```csv
DNI,EMAIL,ENTIDAD,NOMBRE,TELEFONO
1,johndoe@gmail.com,182,John Doe,123-456
2,mikedoe@gmail.com,182,Mike Doe,123-567
3,pauldoe@gmail.com,182,Paul Doe,123-678
```

# 14-Deadletter/01-Introduction.md
# 1. Introducción

La arquitectura BEA (Business Events Architecture) ofrece a los proyectos un conjunto de capacidades para el procesamiento de eventos de negocio.

Más info ¿Que es [BEA](https://platform.bbva.com/bea/documentation/1ULLDbeJBpIz5DANLctgzbF_SdGArroPWsrk42e-Z2mY/01-que-es-bea)?

## Deadletter

Sin embargo, existe la posibilidad de que algunos eventos de un elemento de publicación no puedan entregarse, considerándose como fallidos, llevándonos a dos situaciones:
- Descartar estos eventos
- Enviarlos a la deadletter

Este codelab se centra en el caso de envío a la deadletter y por consiguiente se enfoca en cómo recuperar los eventos fallidos por medio de LRBA.

Más info ¿Que es [Deadletter](https://platform.bbva.com/bea/documentation/1nGNWRHPAolC3_1VrXvEQVmvaTRBZ1k0Wbfo73XAxevk/02-como-usar-bea/02-4-deadletter)?

# 14-Deadletter/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs

Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI

Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.

## Información necesaria

Partiendo de la necesidad de recuperar nuestras deadletter, consideremos tener lo siguiente para iniciar:

1. **Tener la deadletter activa**
    - Debemos tener a mano el id_publisher de nuestra deadletter que se nos proporciona al momento de la activación.
2. **Aprovisionar y habilitar LRBA**
    - [Primeros pasos](../../quickstart/gettingstarted/01-LRBASpark.md)
3. **Generar una malla en control-m, incorporando un FileWatcher y secuencialmente un Job LRBA**
    - Documentación [Control-M](../../developerexperience/04-JobOrchestration/01-Introduction.md)    
    - **¿Por qué necesito un Filewatcher?**
        - Es necesario configurar un Filewatcher para validar que exista al menos una deadletter antes de intentar procesarlas en un job evitando la ejecución si esta no existe o, en el caso de omitir el Filewatcher, un fallo del job si no hay eventos fallidos disponibles en el bucket.
    - **¿Cómo genero una deadletter?**
        - Una deadletter solo es generada cuando un evento no pudo ser entregado debido a algún fallo, por lo tanto, es necesario estar observando el bucket de BEA para que nuestro job procese los eventos fallidos depositados en el bucket.
4. **Configurar un [Filewatcher](../../developerexperience/10-FileWatcher/01-Introduction.md)**
    - Considerar la periodicidad con la que se consultan los deadletters por medio de un filewatcher.
    - Es recomendable usar el mismo wildcard tanto en el ***file-name*** del filewatcher como en el ***physicalName*** del source del job
    - Incorporar el parámetro ***service*** en la ejecución del filewatcher "-service 'bea_deadletter'" para leer el bucket de BEA.
5. **Procesar, validar y depurar nuestras deadletter**
    
    - ***El procesamiento*** de todas nuestras deadletter se procesarán a través de un job y con uso de wildcards, ya que desconocemos el nombrado del archivo y el momento exacto en el que un evento no logró entregarse.

        - Patrón de nombrado: `<id_publisher>/<datetime_utc>-<cloud>-<offsetInicio>-<offsetFin>.parquet`
        - Considerar el patrón de nombrado para ajustar el wildcard a usar en el job.
        - Wildcard para leer todos los deadletters, Ej: `{id_publisher}/*.parquet`

    - ***La validación*** se refiere a solo procesar las deadletter que existían antes de la ejecución del batch, esta validación se realiza agregando la propiedad **“ignoreCreatedFileAfterExecution(true)”** en el Source del job y las razones de su uso son las siguientes:

        - La propiedad **ignoreCreatedFileAfterExecution**, se encarga de solamente leer deadletter que tengan fecha anterior a la ejecución del job, evitando depurar deadletter que no fueron procesadas.
        - El caso más común será cuando se empiezan a leer deadletter con un patrón wildcard **“*.parquet”** y el fallo en la entrega de eventos continue generando más deadletters mientras ejecutamos nuestro Job. Por lo tanto, al seguir generando nuevas deadletter, existe la posibilidad de eliminar aquellas que no han sido procesadas.
    
    - ***El depurado*** se hace a través del mismo job, incorporando una propiedad en el Source del Job  **“deleteFile(true)”** y esta es necesaria para no procesar más de una vez la misma deadletter.

# 14-Deadletter/03-HowToImplementTheJob.md
# 3. Cómo implementar el job
Un job aplicativo que consume una deadletter siempre debe apuntar a su datasource 'bea_deadletter.{UUAA}.BATCH' y esta siempre procesara deadletters en formato parquet; cabe mencionar que todas las deadlettters no están particionadas.

Para el ejemplo propuesto se van a leer todas las deadletter disponibles en el bucket BEA.

1. **Leer de un *Source File parquet*. Dicho fichero contendrá la metadata de la deadletter y el mesaje original generado por kafka.**
  La estructura de dicho fichero será:
    ```json
    {
        "metaInfo": {
          "eventId": "123",
          "retries": 1,
          "time_long": 1631024400000,
          "time_human": "2021-09-07T14:00:00.000Z",
          "reason": "LRA is not active"
        },
        "original": "{...}"
    }
    ```
    Donde:
    - MetaInfo: Metadata del mensaje
    - Original: Mensaje original recuperado de BEA en formato json.

## Implementación del builder

### Sources
Se crea un *source* de tipo `File.parquet` para leer el fichero parquet. Se indican los atributos:
* alias: Alias para cada *source*
* physicalName: Para este caso debemos incluir el "id_publisher" y un wildcard que nos ayude a leer todos nuestros archivos. Recuerda, la estructura de nombrado de los deadletters es:
  - `<id_publisher>/<datetime_utc>-<cloud>-<offsetInicio>-<offsetFin>.parquet`.
* serviceName: *ServiceName* definido para conectarse al bucket de BEA. Recuerda que para las deadletters debemos ingresar un nuevo origen de datos 'bea_deadletter', la sintaxis seria `bea_deadletter.{UUAA}.BATCH`.
* deleteFile: Indica si los archivos leídos serán eliminados después de ser procesados.
* ignoreCreatedFilesAfterExecution: Indica que solo serán leídos archivos que ya existían antes del arranque del job.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
		        .add(Source.File.Parquet.builder()
			              .alias("deadletter")
			              .physicalName("<id_publisher>/*.parquet")
			              .serviceName("bea_deadletter.<UUAA>.BATCH")
			              .deleteFile(true)
			              .ignoreCreatedFilesAfterExecution(true)
			              .build())
		          .build();

}
```

2. **Transformar el objeto deadletter**

### Transform
* En el método `registerTransform` se indica que se va a realizar una transformación de los registros leídos.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

3. **Insertar los detalles de la deadletter en una BD**

### Targets
Se crea un *target* para insertar las deadletters en BD.

- Añadir un *target* del tipo Jdbc Insert.
- Añadir un alias para el *target*.
- Añadir el *physical name* perteneciente a la tabla que quieres modificar. Recuerda la sintaxis `schema.nombre_tabla`.
- Añadir el *service name* definido para la conexión con Oracle. Recuerda la sintaxis `oracle.{UUAA}.BATCH`.

El método *registerTargets* en la clase *JobCodelabBuilder.java* sería:

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.Jdbc.Insert.builder()
                .alias("oracleTarget")
                .physicalName("SCHEMA.TABLE_NAME")
                .serviceName("oracle.LRBA.BATCH")
                .build())
            .build();
        }
```

## Implementación del Transformer
Transformar los registros leídos del parquet usando el encoder del bean por medio de las sigiuentes clases `Deadletter.java` y `MetaInfo.java`

#### Objetos para recuperar nuestras deadletter

```java
public class Deadletter implements Serializable {

    private MetaInfo metaInfo;
    private String original;

    // { getter & setter}
}

public class MetaInfo implements Serializable {

    private String eventId;
    private String retries;
    private String time_long;
    private String time_human;
    private String reason;

    // { getter & setter}
}
```

### Declarar Transform
- Ir a la clase *Transformer.java* y modificar el método *transform* con el siguiente bloque de código.

```java
@Override
	public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {
		  Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
        Dataset<Deadletter> dataset = map.get("deadletter").as(Encoders.bean(Deadletter.class));
        datasetsToWrite.put("oracleTarget", dataset.toDF());
	}
```

## Test unitarios del job

### Builder

```java
class JobDeadletterTestBuilderTest {

  private JobDeadletterTestBuilder jobDeadletterTestBuilder;

  @BeforeEach
  void setUp() {
    this.jobDeadletterTestBuilder = new JobDeadletterTestBuilder();
  }

  @Test
  void registerSources_na_SourceList() {
    final SourcesList sourcesList = this.jobDeadletterTestBuilder.registerSources();
    assertNotNull(sourcesList);
    assertNotNull(sourcesList.getSources());
    assertEquals(1, sourcesList.getSources().size());

    final Source source = sourcesList.getSources().get(0);
    assertNotNull(source);
    assertEquals("deadletter", source.getAlias());
    assertEquals("deadletter.parquet", source.getPhysicalName());
    assertEquals("bea_deadletter.YOUR_UUAA.BATCH", source.getServiceName());
  }

  @Test
  void registerTransform_na_Transform() {
    final TransformConfig transformConfig = this.jobDeadletterTestBuilder.registerTransform();
    assertNotNull(transformConfig);
    assertNotNull(transformConfig.getTransform());
  }

  @Test
  void registerTargets_na_TargetList() {
    final TargetsList targetsList = this.jobDeadletterTestBuilder.registerTargets();
    assertNotNull(targetsList);
    assertNotNull(targetsList.getTargets());
    assertEquals(1, targetsList.getTargets().size());

    final Target target = targetsList.getTargets().get(0);
    assertNotNull(target);
    assertEquals("oracleTarget", target.getAlias());
    assertEquals("oracle.LRBA.BATCH", target.getServiceName());
    assertEquals("SCHEMA.TABLE_NAME", target.getPhysicalName());
  }
}
```

### Transform

Se recomienda utilizar la clase `LRBASparkTest` que proporciona la arquitectura LRBA para realizar los test del *job*.

```java
class TransformerTest extends LRBASparkTest {
  private Transformer transformer;

  @BeforeEach
  void setUp() {
    this.transformer = new Transformer();
  }

  @Test
  void transform_Output() {

    StructType schema = DataTypes.createStructType(
          new StructField[]{
              DataTypes.createStructField("metaInfo", DataTypes.createStructType(
                  new StructField[]{
                      DataTypes.createStructField("eventId", DataTypes.StringType, false),
                      DataTypes.createStructField("retries", DataTypes.StringType, false),
                      DataTypes.createStructField("time_long", DataTypes.StringType, false),
                      DataTypes.createStructField("time_human", DataTypes.StringType, false),
                      DataTypes.createStructField("reason", DataTypes.StringType, false),
                  }
              ), false),
              DataTypes.createStructField("original", DataTypes.StringType, false),
          });

      Row firstsRow = RowFactory.create(
          RowFactory.create("222","3","1631024400000", "2021-09-07T14:00:00.000Z","LRA is not active"),
          "{\"id\": 1,\"name\": \"John Doe\"}"
      );

      final List<Row> listRows = Arrays.asList(firstsRow);
      DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
      Dataset<Row> dataset = datasetUtils.createDataFrame(listRows, schema);
      final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(new HashMap<>(Map.of("deadletter", dataset)));

      assertNotNull(datasetMap);
      assertEquals(1, datasetMap.size());

      Dataset<Deadletter> returnedDsTest = datasetMap.get("oracleTraget").as(Encoders.bean(Deadletter.class));
      final List<Deadletter> rows = datasetToTargetData(returnedDsTest, Deadletter.class);
      MetaInfo metaInfo = rows.get(0).getMetaInfo();
      assertEquals("222", metaInfo.getEventId());
      assertEquals("3", metaInfo.getRetries());

}
```

# 14-Deadletter/04-ExecuteJob.md
# 4. Ejecutar el Job
Para lograr ejecutar un job en local es necesario tener una deadletter en formato parquet.

## Ejecutar el job en el clúster
1 - Disponer de una deadletter y seguir los pasos descritos en: [Deadletter](https://platform.bbva.com/bea/documentation/1nGNWRHPAolC3_1VrXvEQVmvaTRBZ1k0Wbfo73XAxevk/02-como-usar-bea/02-4-deadletter)  
2 - Hacer push del código del *job* a Bitbucket.
3 - Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 15-WriteBinaryFiles/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se escriban ficheros binarios.

# 15-WriteBinaryFiles/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 15-WriteBinaryFiles/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a utilizar un *Target Binario* para escribir distintos ficheros independientemente de su formato.

## Ficheros a escribir

Para poder escribir ficheros, necesitaremos su contenido binario. Si bien este se puede obtener de diversas formas, en este *codelab* los extraeremos de nuestro sistema de ficheros local. Los ficheros a escribir serán los siguientes:

* ***local-execution/files/foto.jpg***
* ***local-execution/files/texto.txt***
* ***local-execution/files/documento.pdf***

**IMPORTANTE**: El contenido de estos ficheros es indiferente para el desarrollo del *codelab*, escoge los documentos que más te apetezcan.

## Implementación del builder

### Sources

En este caso, como obtendremos los ficheros de nuestro equipo local, no necesitaremos ningún source.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder().build();
}
```

### Transform

En el método `registerTransform` se indica cuál es nuestra clase *Transform*.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Targets

Debido a la naturaleza del target binario, vamos a crear dos distintos para observar las diferentes casuísticas:

1. Target binario con un *physicalName* especificado. De esta manera establecemos una ruta común para todos los ficheros que vaya a escribir el target.
2. Target binario con un *physicalName* sin especificar. De este modo cada fichero se escribirá únicamente con la ruta especificada en su *BinaryFileBean*. 

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Binary.builder()
                    .alias("withPhysicalName")
                    .physicalName("labs/outputs/withPhysicalName")
                    .serviceName(bts.YOUR_UUAA.BATCH)
                    .build())
            .add(Target.File.Binary.builder()
                    .alias("withoutPhysicalName")
                    .serviceName(bts.YOUR_UUAA.BATCH)
                    .build())
            .build();
}
```

## Implementación del transformer

Implementamos el método *transform* para leer los ficheros que queremos escribir con nuestros targets y especificar donde queremos que se escriban dentro del contexto de cada target. Si se quiere, se puede experimentar escribiendo diversas rutas.

```java
 @Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> map) {
    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();

    try {
        Dataset<Row> datasetWithPhysicalName = createBinaryFileDataset("fotos/foto.jpg", "textos/texto.txt", "docs/documento.pdf");
        Dataset<Row> datasetWithoutPhysicalName = createBinaryFileDataset(
                "labs/outputs/withoutPhysicalName/fotos/foto.jpg",
                "labs/outputs/withoutPhysicalName/textos/texto.txt",
                "labs/outputs/withoutPhysicalName/docs/documento.pdf"
        );

        datasetsToWrite.put("withPhysicalName", datasetWithPhysicalName);
        datasetsToWrite.put("withoutPhysicalName", datasetWithoutPhysicalName);
    } catch (IOException e) {
        throw new RuntimeException(e);
    }
    return datasetsToWrite;
}
```

Como se puede ver se crean dos datasets distintos, uno para cada target. Para ello, se ha utilizado el método privado `datasetFromBinaryRow` que dado el nombre a escribir de cada fichero de este *codelab*, te devuelve un dataset preparado para servir como input del target.

```java
public Dataset<Row> createTestDataset(String nombreFoto, String nombreTexto, String nombreDocumento) throws IOException {
    byte[] fotoJpg, textoTxt, documentoPdf;

    fotoJpg = Files.readAllBytes(Paths.get("local-execution/files/foto.jpg"));
    textoTxt = Files.readAllBytes(Paths.get("local-execution/files/texto.txt"));
    documentoPdf = Files.readAllBytes(Paths.get("local-execution/files/documento.pdf"));

    List<BinaryFileBean> data = Arrays.asList(
            new BinaryFileBean.Builder()
                    .path(nombreFoto)
                    .content(fotoJpg)
                    .build(),
            new BinaryFileBean.Builder()
                    .path(nombreTexto)
                    .content(textoTxt)
                    .build(),
            new BinaryFileBean.Builder()
                    .path(nombreDocumento)
                    .content(documentoPdf)
                    .build()
    );

    DatasetUtils<BinaryFileBean> binaryFileDatasetUtils = new DatasetUtils<>();
    return binaryFileDatasetUtils.createDataset(data, Encoders.bean(BinaryFileBean.class)).toDF();
}
```

## Test unitarios del job

### Builder

```java
import com.bbva.lrba.builder.spark.domain.SourcesList;
import com.bbva.lrba.builder.spark.domain.TargetsList;
import com.bbva.lrba.spark.domain.datasource.Source;
import com.bbva.lrba.spark.domain.datatarget.Target;
import com.bbva.lrba.spark.domain.transform.TransformConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class JobWriteBinaryfileBuilderTest {

    private JobWriteBinaryfileBuilder jobWriteBinaryfileBuilder;

    @BeforeEach
    void setUp() {
        this.jobWriteBinaryfileBuilder = new JobWriteBinaryfileBuilder();
    }

    @Test
    void registerSources_na_SourceList() {

        final SourcesList sourcesList = this.jobWriteBinaryfileBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(0, sourcesList.getSources().size());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobWriteBinaryfileBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobWriteBinaryfileBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(2, targetsList.getTargets().size());

        final Target target1 = targetsList.getTargets().get(0);
        assertNotNull(target1);
        assertEquals("withPhysicalName", target1.getAlias());
        assertEquals("labs/outputs/withPhysicalName", target1.getPhysicalName());

        final Target target2 = targetsList.getTargets().get(1);
        assertNotNull(target2);
        assertEquals("withoutPhysicalName", target2.getAlias());
        assertTrue(target2.getPhysicalName().isBlank());
    }

}
```


### Transformer

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        Map<String, Dataset<Row>> datasets = new HashMap<>();

        final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

        assertNotNull(datasetMap);
        assertEquals(2, datasetMap.size());

        assertEquals(3, datasetMap.get("withPhysicalName").count());
        assertEquals(3, datasetMap.get("withoutPhysicalName").count());
    }

}
```

# 15-WriteBinaryFiles/04-ExecuteJob.md
# 4. Cómo ejecutar el job

En esta fase vamos a ejecutar nuestro *job* en local y ver cómo se comporta.

## Ejecutar el job en local

Se ejecuta el *job* con la ayuda del CLI de LRBA.

```bash
lrba run
```
### Analizar el resultado

Se puede observar que los ficheros se han escrito correctamente en el directorio `local-execution/files/labs/outputs`.

```
withoutPhysicalName/
├── docs/
│   └── documento.pdf
├── fotos/
│   └── foto.jpg
└── textos/
    └── texto.txt

withPhysicalName/
├── docs/
│   └── documento.pdf
├── fotos/
│   └── foto.jpg
└── textos/
    └── texto.txt
```

# 16-OracleInlineQueries/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se realicen queries inline desde un dataset a una base de datos Oracle.

# 16-OracleInlineQueries/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 16-OracleInlineQueries/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a leer un fichero csv en un dataset, se va a completar con datos de una BBDD Oracle mediante *inline queries* y se va a escribir en otro fichero csv.

**IMPORTANTE**: Para poder realizar este *codelab* es necesario tener acceso a una BBDD Oracle en el cluster o disponer de un entorno local con una BBDD Oracle.

## Datos de entrada

### Esquema de la BBDD

La BBDD de ejemplo que se va a utilizar en este *codelab* es la siguiente:

```sql
create table PERSONAS
(
    COD_CLIENTE NUMBER(10) not null
        primary key,
    NOMBRE      VARCHAR2(100),
    CIUDAD      VARCHAR2(100),
    PAIS        VARCHAR2(50),
    TELEFONO    VARCHAR2(50),
    EMAIL       VARCHAR2(50),
    EDAD        NUMBER(3)
)
```

### Fichero de entrada

Se va a leer un fichero csv que contendrá los campos *ciudad* y *edad* separados por comas, los cuales se utilizarán para realizar las consultas a la BBDD Oracle.
El fichero tendrá el siguiente contenido:

```csv
ciudad,edad
Madrid,25
Bilbao,30
Barcelona,10
```

**NOTA**: Estos datos son solo para este ejemplo de desarrollo, se pueden utilizar otros datos.

## Implementación del builder

Se va a implementar el *job* en la clase *JobJdbcInlineQueryBuilder.java*.

### Source

Se va a leer el fichero csv que se ha creado en el paso anterior. Para ello se va a crear un *source* de tipo *File CSV*.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.CSV.builder()
                    .alias("inputFile")
                    .physicalName("fichero_entrada.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .sql("SELECT * FROM inputFile")
                    .build())
            .build();
}
```

### Transform

En la clase *JobJdbcInlineQueryBuilder.java* no modificar el método *registerTransform* que está por defecto. 

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Target

Se va a escribir el fichero csv de salida. Para ello se va a crear un *target* de tipo *File CSV*.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.CSV.builder()
                    .alias("outputFile")
                    .physicalName("fichero_salida.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .build())
            .build();
}
```

## Implementación del transformer

En la clase *Transformer.java* se va a modificar el método *transform* para iterar el dataset de entrada y realizar las consultas a la BBDD Oracle por cada fila.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<InputData> datasetEdades = datasetsFromRead.get("inputFile").as(Encoders.bean(InputData.class));

    Dataset<OracleData> oracleResults = datasetEdades.flatMap((FlatMapFunction<InputData, OracleData>) row -> JdbcIterableQuery.createQuery(
            new MyJdbcHelper(),
            "oracle.YOUR_UUAA.BATCH",
            row), Encoders.bean(OracleData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    datasetsToWrite.put("outputFile", oracleResults.toDF());

    return datasetsToWrite;
} 
```

## Implementación de las interfaces y beans

Se van a crear las clases *InputData.java* y *OracleData.java* para mapear los datos de entrada y salida respectivamente. Ambas clases **deben implementar la interfaz Serializable**.

### InputData.java

```java
public class InputData implements Serializable {
    
    private String ciudad;
    private int edad;

    public String getCiudad() {
        return ciudad;
    }

    public void setCiudad(String ciudad) {
        this.ciudad = ciudad;
    }

    public int getEdad() {
        return edad;
    }

    public void setEdad(int edad) {
        this.edad = edad;
    }
}
```

### OracleData.java

```java
public class OracleData implements Serializable {

    private long COD_CLIENTE;
    private String NOMBRE;
    private String CIUDAD;
    private String PAIS;
    private String TELEFONO;
    private String EMAIL;
    private int EDAD;

    public long getCOD_CLIENTE() {
        return COD_CLIENTE;
    }
    
    public void setCOD_CLIENTE(long codCliente) {
        COD_CLIENTE = codCliente;
    }
    
    public String getNOMBRE() {
        return NOMBRE;
    }
    
    public void setNOMBRE(String nombre) {
        NOMBRE = nombre;
    }
    
    public String getCIUDAD() {
        return CIUDAD;
    }
    
    public void setCIUDAD(String ciudad) {
        CIUDAD = ciudad;
    }
    
    public String getPAIS() {
        return PAIS;
    }
    
    public void setPAIS(String pais) {
        PAIS = pais;
    }
    
    public String getTELEFONO() {
        return TELEFONO;
    }
    
    public void setTELEFONO(String telefono) {
        TELEFONO = telefono;
    }
    
    public String getEMAIL() {
        return EMAIL;
    }
    
    public void setEMAIL(String email) {
        EMAIL = email;
    }
    
    public int getEDAD() {
        return EDAD;
    }
    
    public void setEDAD(int edad) {
        EDAD = edad;
    }

} 
```

Por último, se va a crear la clase *MyJdbcHelper.java* que implementará la interfaz *IJdbcIterableQueryHandler* para crear las consultas parametrizadas a la BBDD Oracle, 
setear los parámetros y mapear los resultados a la clase *OracleData.java*.

```java
public class MyJdbcHelper implements IJdbcIterableQueryHandler<InputData, OracleData>, Serializable {

    private static final long serialVersionUID = 1L;

    private String edad;
    private String ciudad;
    
    @Override
    public void setSearchValue(Bean s) {
       this.edad = s.getEdad();
       this.ciudad = s.getCiudad();
    }

    @Override
    public String getQuery() {
       return "SELECT * FROM PERSONAS WHERE EDAD = ? AND CIUDAD = ?";
    }

    @Override
    public void prepareBindVariables(PreparedStatement pst) throws SQLException {
       pst.setInt(1, Integer.parseInt(edad));
       pst.setString(2, ciudad);
    }

    @Override
    public OracleData processResultSet(ResultSet rs) {
       OracleData rowData = new OracleData();

       if (rs!=null) {
          try {
             rowData.setCOD_CLIENTE(rs.getLong("COD_CLIENTE"));
             rowData.setNOMBRE(rs.getString("NOMBRE"));
             rowData.setCIUDAD(rs.getString("CIUDAD"));
             rowData.setPAIS(rs.getString("PAIS"));
             rowData.setTELEFONO(rs.getString("TELEFONO"));
             rowData.setEMAIL(rs.getString("EMAIL"));
             rowData.setEDAD(rs.getInt("EDAD"));
          } catch (SQLException e) {
             e.printStackTrace();
          }
       } else {
          rowData.setEDAD(Integer.parseInt(edad));
       }
       return rowData;
    }

    @Override
    public boolean processNoData() {
       return true;
    }

}
```

## Test unitarios del job

### JobJdbcInlineQueryBuilder

Se van a crear los test unitarios de la clase *JobJdbcInlineQueryBuilder.java* en la clase *JobJdbcInlineQueryBuilderTest.java*.

```java
class JobJdbcInlineQueryBuilderTest {

    private JobJdbcInlineQueryBuilder jobJdbcInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        this.jobJdbcInlineQueryBuilder = new JobJdbcInlineQueryBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobJdbcInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputFile", source.getAlias());
        assertEquals("fichero_entrada.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobJdbcInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobJdbcInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("outputFile", target.getAlias());
        assertEquals("fichero_salida.csv", target.getPhysicalName());
    }

}
```

### TransformerTest

Se van a crear los test unitarios de la clase *Transformer.java* en la clase *TransformerTest.java*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("edad", DataTypes.IntegerType, false),
                        DataTypes.createStructField("ciudad", DataTypes.StringType, false)
                });

        final List<Row> data = Arrays.asList(
                RowFactory.create(25, "Madrid"),
                RowFactory.create(10, "Barcelona"),
                RowFactory.create(30, "Bilbao")
        );

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(data, schema);

        Map<String, Dataset<Row>> datasets = new HashMap<>();
        datasets.put("inputFile", dataset);

        try (MockedStatic<JdbcIterableQuery> mockedJdbcQuery = Mockito.mockStatic(JdbcIterableQuery.class)) {
            mockedJdbcQuery.when(() -> JdbcIterableQuery.createQuery(
                            any(MyJdbcHelper.class),
                            eq("oracle.YOUR_UUAA.BATCH"),
                            any(OracleBean.class)))
                    .thenReturn(mock(JdbcIterableQuery.class));

            final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

            assertNotNull(datasetMap);
            assertEquals(1, datasetMap.size());

            Dataset<Row> resultDataset = datasetMap.get("outputFile");
            assertNotNull(resultDataset);
        }
    }
}
```

### MyJdbcHelperTest
Se van a crear los test unitarios de la clase *MyJdbcHelper.java* en la clase *MyJdbcHelperTest.java*.

```java
class MyJdbcHelperTest {

    private MyJdbcHelper myJdbcHelper;

    @BeforeEach
    void setUp() {
        myJdbcHelper = new MyJdbcHelper();
    }

    @Test
    void test_helper() throws SQLException {
        InputData inputData = new InputData();
        inputData.setEdad("30");
        inputData.setCiudad("Madrid");

        myJdbcHelper.setSearchValue(inputData);

        PreparedStatement preparedStatement = mock(PreparedStatement.class);
        myJdbcHelper.prepareBindVariables(preparedStatement);

        ResultSet resultSet = mock(ResultSet.class);
        when(resultSet.getLong("COD_CLIENTE")).thenReturn(123L);
        when(resultSet.getString("NOMBRE")).thenReturn("John Doe");
        when(resultSet.getString("CIUDAD")).thenReturn("Madrid");
        when(resultSet.getString("PAIS")).thenReturn("Spain");
        when(resultSet.getString("TELEFONO")).thenReturn("123456789");
        when(resultSet.getString("EMAIL")).thenReturn("email@email.com");
        when(resultSet.getInt("EDAD")).thenReturn(30);

        OracleData oracleData = myJdbcHelper.processResultSet(resultSet);
        assertNotNull(oracleData);

        OracleData oracleData2 = myJdbcHelper.processResultSet(null);
        assertNotNull(oracleData2);
        assertEquals(30, oracleData2.getEDAD());

        assertEquals("SELECT * FROM PERSONAS WHERE EDAD = ? AND CIUDAD = ?", myJdbcHelper.getQuery());
    }
}
```

# 16-OracleInlineQueries/04-ExecuteJob.md
# 4. Ejecutar el Job
Para lograr ejecutar un job en local es necesario tener una base de datos Oracle con los datos necesarios.

## Ejecutar el job en el clúster
1 - Disponer de una BBDD Oracle.
2 - Hacer push del código del *job* a Bitbucket.
3 - Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 17-ElasticInlineQueries/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se realicen queries inline desde un dataset a un motor de búsquedas Elasticsearch.

# 17-ElasticInlineQueries/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 17-ElasticInlineQueries/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a leer un fichero csv en un dataset, se va a completar con datos de un motor de búsquedas Elasticsearch mediante *inline queries* y se va a escribir en otro fichero csv.

**IMPORTANTE**: Para poder realizar este *codelab* es necesario tener acceso a un motor de búsquedas Elasticsearch en el cluster o disponer de un entorno local con un motor de búsquedas Elasticsearch.

## Datos de entrada

### Esquema del Document de Elasticsearch
En este *codelab*, vamos a trabajar sobre un índice de Elasticsearch llamado **i_lrba_test** ,que contiene documentos como el que se muestra a continuación:

```json
{
  "Data_value": "Consectetur proident eu dolore laborum esse proident esse aliqua cupidatat ut cillum id.",
  "Group": "Gink",
  "Period": "2017",
  "Series_reference": "Cupidatat ad reprehenderit eu cupidatat.",
  "Series_title_1": "Et voluptate sit cillum proident officia sint est Lorem aliqua.",
  "Series_title_2": "Incididunt enim tempor ipsum cillum non consectetur occaecat deserunt in esse voluptate esse.",
  "Status": "4",
  "Subject": "Exercitation dolore minim magna laborum in.",
  "UNITS": "56",
  "apiKey": "9156e988-a09d-4db8-8916-b3f2d06a934e",
  "company": "Zedalis",
  "createdAt": "2017-07-26T17:46:47.873Z",
  "multipleId": "Incididunt Lorem nisi amet duis proident.",
  "name": "Alice Howard",
  "updatedAt": "2017-07-26",
  "upsertDone": "false",
  "uuid": 505
}
```

### Fichero de entrada

Se va a leer un fichero csv que contendrá los campos *year* y *company* separados por comas, los cuales se utilizarán para realizar las consultas a Elasticsearch.
El fichero tendrá el siguiente contenido:

```csv
year, company
2019, Zedalis
2018, Orbaxter
```

**NOTA**: Estos datos son solo para este ejemplo de desarrollo, se pueden utilizar otros datos.

## Implementación del builder

Se va a implementar el *job* en la clase *JobElasticInlineQueryBuilder.java*.

### Source

Se va a leer el fichero csv que se ha creado en el paso anterior. Para ello se va a crear un *source* de tipo *File CSV*.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.CSV.builder()
                    .alias("inputFile")
                    .physicalName("fichero_entrada.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

### Transform

En la clase *JobElasticInlineQueryBuilder.java* no modificar el método *registerTransform* que está por defecto

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Target

Se va a escribir el fichero csv de salida. Para ello se va a crear un *target* de tipo *File CSV*.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.CSV.builder()
                    .alias("outputFile")
                    .physicalName("fichero_salida.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .build())
            .build();
}
```

## Implementación del transformer

En la clase *Transformer.java* se va a modificar el método *transform* para iterar el dataset de entrada y realizar las consultas al índice de Elasticsearch por cada fila.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<SearchBeanElastic> datasetCompanies = datasetsFromRead.get("inputFile").as(Encoders.bean(SearchBeanElastic.class));

    Dataset<ElasticData> elasticResults = datasetCompanies.flatMap((FlatMapFunction<SearchBeanElastic, ElasticData>) row -> ElasticIterableQuery.createQuery(
            new MyElasticHelper(),
            "elastic.YOUR_UUAA.BATCH",
            row), Encoders.bean(ElasticData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    datasetsToWrite.put("outputFile", elasticResults.toDF());

    return datasetsToWrite;
} 
```

## Implementación de las interfaces y beans

Se van a crear las clases *SearchBeanElastic.java* y *ElasticData.java* para mapear los datos de entrada y salida respectivamente. Ambas clases **deben implementar la interfaz Serializable**.

### SearchBeanElastic.java

```java
public class SearchBeanElastic implements Serializable {

    private String year;
    private String company;

    public String getYear() {
        return year;
    }

    public void setYear(String year) {
        this.year = year;
    }

    public String getCompany() {
        return company;
    }

    public void setCompany(String company) {
        this.company = company;
    }
}
```

### ElasticData.java

```java
public class ElasticData implements Serializable {

    private String dataValue;
    private String group;
    private String period;
    private String seriesReference;
    private String seriesTitle1;
    private String seriesTitle2;
    private String status;
    private String subject;
    private String units;
    private String apiKey;
    private String company;
    private String createdAt;
    private String multipleId;
    private String name;
    private String updatedAt;
    private String upsertDone;
    private Integer uuid;

    public String getDataValue() {
        return dataValue;
    }

    public void setDataValue(String dataValue) {
        this.dataValue = dataValue;
    }

    public String getGroup() {
        return group;
    }

    public void setGroup(String group) {
        this.group = group;
    }

    public String getPeriod() {
        return period;
    }

    public void setPeriod(String period) {
        this.period = period;
    }

    public String getSeriesReference() {
        return seriesReference;
    }

    public void setSeriesReference(String seriesReference) {
        this.seriesReference = seriesReference;
    }

    public String getSeriesTitle1() {
        return seriesTitle1;
    }

    public void setSeriesTitle1(String seriesTitle1) {
        this.seriesTitle1 = seriesTitle1;
    }

    public String getSeriesTitle2() {
        return seriesTitle2;
    }

    public void setSeriesTitle2(String seriesTitle2) {
        this.seriesTitle2 = seriesTitle2;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSubject() {
        return subject;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public String getUnits() {
        return units;
    }

    public void setUnits(String units) {
        this.units = units;
    }

    public String getApiKey() {
        return apiKey;
    }

    public void setApiKey(String apiKey) {
        this.apiKey = apiKey;
    }

    public String getCompany() {
        return company;
    }

    public void setCompany(String company) {
        this.company = company;
    }

    public String getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(String createdAt) {
        this.createdAt = createdAt;
    }

    public String getMultipleId() {
        return multipleId;
    }

    public void setMultipleId(String multipleId) {
        this.multipleId = multipleId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(String updatedAt) {
        this.updatedAt = updatedAt;
    }

    public String getUpsertDone() {
        return upsertDone;
    }

    public void setUpsertDone(String upsertDone) {
        this.upsertDone = upsertDone;
    }

    public Integer getUuid() {
        return uuid;
    }

    public void setUuid(Integer uuid) {
        this.uuid = uuid;
    }

    @Override
    public String toString() {
        return "ElasticData{" +
                "dataValue='" + dataValue + '\'' +
                ", group='" + group + '\'' +
                ", period='" + period + '\'' +
                ", seriesReference='" + seriesReference + '\'' +
                ", seriesTitle1='" + seriesTitle1 + '\'' +
                ", seriesTitle2='" + seriesTitle2 + '\'' +
                ", status='" + status + '\'' +
                ", subject='" + subject + '\'' +
                ", units='" + units + '\'' +
                ", apiKey='" + apiKey + '\'' +
                ", company='" + company + '\'' +
                ", createdAt='" + createdAt + '\'' +
                ", multipleId='" + multipleId + '\'' +
                ", name='" + name + '\'' +
                ", updatedAt='" + updatedAt + '\'' +
                ", upsertDone='" + upsertDone + '\'' +
                ", uuid='" + uuid + '\'' +
                '}';
    }

} 
```

Por último, se va a crear la clase *MyElasticHelper.java* que implementará la interfaz *IElasticIterableQueryHandler* para crear las consultas parametrizadas a Elasticsearch, 
setear los parámetros y mapear los resultados a la clase *ElasticData.java*.

```java
public class MyElasticHelper implements IElasticIterableQueryHandler<SearchBeanElastic, ElasticData>, Serializable {
    private static final Logger LOGGER = LoggerFactory.getLogger(MyElasticHelper.class);

    private static final long serialVersionUID = 1L;

    private String year;
    private String company;

    @Override
    public void setSearchValue(SearchBeanElastic searchBeanElastic) {
        this.company = searchBeanElastic.getCompany();
        this.year = searchBeanElastic.getYear();
    }

    @Override
    public String getQuery() {
        return """
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
                """;
    }

    @Override
    public String getIndex() {
        return "i_lrba_test";
    }

    @Override
    public Map<String, Object> getMapBindVariables() {
        return Map.of("year_param", year, "company_param", company);
    }

    @Override
    public ElasticData processResultDocument(Map<String, Object> document) {
        LOGGER.warn("Processing result");
        if (document!=null){
            LOGGER.warn(document.toString());
            ElasticData elasticData = new ElasticData();
            elasticData.setDataValue((String) document.get("Data_value"));
            elasticData.setGroup((String) document.get("Group"));
            elasticData.setPeriod((String) document.get("Period"));
            elasticData.setSeriesReference((String) document.get("Series_reference"));
            elasticData.setSeriesTitle1((String) document.get("Series_title_1"));
            elasticData.setSeriesTitle2((String) document.get("Series_title_2"));
            elasticData.setStatus((String) document.get("Status"));
            elasticData.setSubject((String) document.get("Subject"));
            elasticData.setUnits((String) document.get("UNITS"));
            elasticData.setApiKey((String) document.get("apiKey"));
            elasticData.setCompany((String) document.get("company"));
            elasticData.setCreatedAt((String) document.get("createdAt"));
            elasticData.setMultipleId((String) document.get("multipleId"));
            elasticData.setName((String) document.get("name"));
            elasticData.setUpdatedAt((String) document.get("updatedAt"));
            elasticData.setUpsertDone((String) document.get("upsertDone"));
            elasticData.setUuid((Integer) document.get("uuid"));
            LOGGER.debug("{}",elasticData);
            return elasticData;
        } else {
            LOGGER.warn("No results for the elastic query");
            return new ElasticData();
        }
    }

    @Override
    public boolean processNoData() {
        return true;
    }

}
```

## Test unitarios del job

### JobElasticInlineQueryBuilder

Se van a crear los test unitarios de la clase *JobElasticInlineQueryBuilder.java* en la clase *JobElasticInlineQueryBuilderTest.java*.

```java
class JobElasticInlineQueryBuilderTest {

    private JobElasticInlineQueryBuilder jobElasticInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        this.jobElasticInlineQueryBuilder = new JobElasticInlineQueryBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobElasticInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputFile", source.getAlias());
        assertEquals("fichero_entrada.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobElasticInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobElasticInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("outputFile", target.getAlias());
        assertEquals("fichero_salida.csv", target.getPhysicalName());
    }

}
```

### TransformerTest

Se van a crear los test unitarios de la clase *Transformer.java* en la clase *TransformerTest.java*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("year", DataTypes.StringType, false),
                        DataTypes.createStructField("company", DataTypes.StringType, false)
                });

        final List<Row> data = Arrays.asList(
                RowFactory.create("2019", "Google"),
                RowFactory.create("2020", "Meta"),
                RowFactory.create("2021", "Tesla")
        );

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(data, schema);

        Map<String, Dataset<Row>> datasets = new HashMap<>();
        datasets.put("inputFile", dataset);

        try (MockedStatic<ElasticIterableQuery> mockedElasticQuery = Mockito.mockStatic(ElasticIterableQuery.class)) {
            mockedElasticQuery.when(() -> ElasticIterableQuery.createQuery(
                            any(MyElasticHelper.class),
                            eq("elastic.YOUR_UUAA.BATCH"),
                            any(SearchBeanElastic.class)))
                    .thenReturn(mock(ElasticIterableQuery.class));

            final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

            assertNotNull(datasetMap);
            assertEquals(1, datasetMap.size());

            Dataset<Row> resultDataset = datasetMap.get("outputFile");
            assertNotNull(resultDataset);
        }
    }
}
```

### MyElasticHelper
Se van a crear los test unitarios de la clase *MyElasticHelper.java* en la clase *MyElasticHelperTest.java*.

```java
class MyElasticHelperTest {

    private MyElasticHelper myElasticHelper;

    @BeforeEach
    void setUp() {
        myElasticHelper = new MyElasticHelper();
    }

    @Test
    void test_index() {
        assertEquals("i_lrba_test", myElasticHelper.getIndex());
    }

    @Test
    void test_query() {
        String expectedQuery = """
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
                """;
        assertEquals(expectedQuery, myElasticHelper.getQuery());
    }

    @Test
    void test_search_value() {
        // given
        SearchBeanElastic searchBeanElastic = new SearchBeanElastic();
        searchBeanElastic.setCompany("Google");
        searchBeanElastic.setYear("2019");

        // when
        myElasticHelper.setSearchValue(searchBeanElastic);

        // then
        Map<String, Object> mapBindVariables = myElasticHelper.getMapBindVariables();
        assertEquals("Google", mapBindVariables.get("company_param"));
        assertEquals("2019", mapBindVariables.get("year_param"));
    }

    @Test
    void test_process_no_data() {
        assertTrue(myElasticHelper.processNoData());
    }

    @Test
    void process_result_document() {
        // given
        Map<String, Object> result = new HashMap<>();
        result.put("Data_value", "Consectetur proident eu dolore laborum esse proident esse aliqua cupidatat ut cillum id.");
        result.put("Group", "Gink");
        result.put("Period", "2017");
        result.put("Series_reference", "Cupidatat ad reprehenderit eu cupidatat.");
        result.put("Series_title_1", "Et voluptate sit cillum proident officia sint est Lorem aliqua.");
        result.put("Series_title_2", "Incididunt enim tempor ipsum cillum non consectetur occaecat deserunt in esse voluptate esse.");
        result.put("Status", "4");
        result.put("Subject", "Exercitation dolore minim magna laborum in.");
        result.put("UNITS", "56");
        result.put("apiKey", "9156e988-a09d-4db8-8916-b3f2d06a934e");
        result.put("company", "Zedalis");
        result.put("createdAt", "2017-07-26T17:46:47.873Z");
        result.put("multipleId", "Incididunt Lorem nisi amet duis proident.");
        result.put("name", "Alice Howard");
        result.put("updatedAt", "2017-07-26");
        result.put("upsertDone", "false");
        result.put("uuid", 505);

        // when
        ElasticData elasticData = myElasticHelper.processResultDocument(result);

        // then
        assertEquals("Consectetur proident eu dolore laborum esse proident esse aliqua cupidatat ut cillum id.", elasticData.getDataValue());
        assertEquals("Gink", elasticData.getGroup());
        assertEquals("2017", elasticData.getPeriod());
        assertEquals("Cupidatat ad reprehenderit eu cupidatat.", elasticData.getSeriesReference());
        assertEquals("Et voluptate sit cillum proident officia sint est Lorem aliqua.", elasticData.getSeriesTitle1());
        assertEquals("Incididunt enim tempor ipsum cillum non consectetur occaecat deserunt in esse voluptate esse.", elasticData.getSeriesTitle2());
        assertEquals("4", elasticData.getStatus());
        assertEquals("Exercitation dolore minim magna laborum in.", elasticData.getSubject());
        assertEquals("56", elasticData.getUnits());
        assertEquals("9156e988-a09d-4db8-8916-b3f2d06a934e", elasticData.getApiKey());
        assertEquals("Zedalis", elasticData.getCompany());
        assertEquals("2017-07-26T17:46:47.873Z", elasticData.getCreatedAt());
        assertEquals("Incididunt Lorem nisi amet duis proident.", elasticData.getMultipleId());
        assertEquals("Alice Howard", elasticData.getName());
        assertEquals("2017-07-26", elasticData.getUpdatedAt());
        assertEquals("false", elasticData.getUpsertDone());
        assertEquals(505, elasticData.getUuid());
    }
}
```

# 17-ElasticInlineQueries/04-ExecuteJob.md
# 4. Ejecutar el Job
Para lograr ejecutar un job en local es necesario tener un motor de búsqueda de Elasticsearch con los datos necesarios.

## Ejecutar el job en el clúster
1 - Disponer de un motor de búsqueda de Elasticsearch.
2 - Hacer push del código del *job* a Bitbucket.
3 - Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 18-MongoDBInlineQueries/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se realicen queries inline desde un dataset a una base de datos MongoDB.

# 18-MongoDBInlineQueries/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 18-MongoDBInlineQueries/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

Este job implementará un ejemplo para cada tipo de operación disponible en la funcionalidad de mongoDB (Find y Aggregate).

Ejemplo 1 (Find): Se leerá un fichero csv que contendrá ids de personas y teléfonos, buscará en una BBDD Mongo los datos de esos ids, y escribirá
en un fichero csv los datos de las personas con su teléfono. Si no se encuentra el id, no se escribirá en el fichero de salida. 

Ejemplo 2 (Aggreate): Se leerá un fichero csv que contendrá ciudades, hará la búsqueda en la BBDD Mongo y escribirá
en un fichero csv el número de personas correspondientes a cada ciudad.

**IMPORTANTE**: Para poder realizar este *codelab* es necesario tener acceso a una BBDD Mongo en el cluster o disponer de un entorno local con una BBDD Mongo.

## Datos de entrada

### Esquema de la BBDD

Para ambos ejemplos, la BBDD que se va a utilizar en este *codelab* tendrá documentos con la siguiente estructura:

```json
{
  "_id": "1",
  "city": "Barcelona",
  "age": 25,
  "name": "María López"
}
```

## Ejemplo 1 (Find)

### Fichero de entrada

```csv inputPhones.csv (CASO 1)
_id,phone
1,123456789
3,987654321
4,456789123
5,321654987
8,654321789
```

**NOTA**: Estos datos son solo para este ejemplo de desarrollo, se pueden utilizar otros datos.


### Implementación del builder

Se va a implementar el *job* en la clase *JobMongoInlineQueryBuilder.java*.

#### Source

Se crea el *source* de tipo *File CSV* para leer el fichero de entrada.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("inputPhones")
                    .physicalName("inputPhones.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

#### Transform

En la clase *JobMongoInlineQueryBuilder.java* no modificar el método *registerTransform* que está por defecto. 

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

#### Target

Se crea el *target* de tipo *File CSV* para escribir el fichero de salida.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Csv.builder()
                    .alias("personData")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .physicalName("personData.csv")
                    .humanReadable(true)
                    .delimiter(",")
                    .header(true)
                    .build()).build();
}
```

### Implementación del transformer

En la clase *Transformer.java* se va a modificar el método *transform* para iterar el dataset de entrada y realizar las consultas a la BBDD Mongo por cada fila.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<InputData> inputPhones = map.get("inputPhones").as(Encoders.bean(InputData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<MongoData> mongoResults = inputPhones.flatMap((FlatMapFunction<InputData, MongoData>) searchValue -> MongoIterableQuery.createQuery(
            new MyMongoHelper(),
            "mongodb.YOUR_BBDD.BATCH",
            searchValue), Encoders.bean(MongoData.class));

    datasetsToWrite.put("personData", mongoResults.toDF());
    return datasetsToWrite;
} 
```

### Implementación de las interfaces y beans

Se van a crear las clases *InputData.java* y *MongoData.java* para mapear los datos de entrada y salida respectivamente. Ambas clases **deben implementar la interfaz Serializable**.

#### InputData.java

```java
public class InputData implements Serializable {

    private String _id;
    private String phone;

    public String get_id() {
        return _id;
    }

    public void set_id(String _id) {
        this._id = _id;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}
```

#### MongoData.java

```java
public class MongoData implements Serializable {

    private String _id;
    private String name;
    private String age;
    private String city;
    private String phone;

    public String get_id() {
        return _id;
    }

    public void set_id(String _id) {
        this._id = _id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAge() {
        return age;
    }

    public void setAge(String age) {
        this.age = age;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
} 
```

Por último, se va a crear la clase *MyMongoHelper.java* que implementará la interfaz *IMongoIterableQueryHandler* para crear las consultas parametrizadas a la BBDD Mongo, 
setear los parámetros y mapear los resultados a la clase *MongoData.java*.

```java
public class MyMongoHelper implements IMongoIterableQueryHandler<InputData, MongoData>, Serializable {

    private static final long serialVersionUID = 1L;

    private String _id;
    private String phone;
    
    @Override
    public void setSearchValue(InputData input) {
        this._id = input.get_id();
        this.phone = input.getPhone();
    }

    @Override
    public String getCollection() {
        return "your_collection";
    }

    @Override
    public String getQueryType() {
        return "FIND";
    }

    @Override
    public Document getFindFilter() {
        return new Document("_id", this._id);
    }
    
    @Override
    public List<Document> getAggregatePipeline() {
        return null;
    }
    
    @Override
    public boolean processNoData() {
        return false;
    }

    @Override
    public MongoData processResult(Document document) {
        MongoData mongoData = new MongoData();
        mongoData.set_id(this._id);
        mongoData.setName(document.getString("name"));
        mongoData.setAge(String.valueOf(document.getInteger("age")));
        mongoData.setCity(document.getString("city"));
        mongoData.setPhone(this.phone);
        return mongoData;
    }
}
```

### Test unitarios del job

#### JobMongoInlineQueryBuilder

Se van a crear los test unitarios de la clase *JobMongoInlineQueryBuilder.java* en la clase *JobMongoInlineQueryBuilderTest.java*.

```java
class JobMongoInlineQueryBuilderTest {

    private JobMongoInlineQueryBuilder jobMongoInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        this.jobMongoInlineQueryBuilder = new JobMongoInlineQueryBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobMongoInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputPhones", source.getAlias());
        assertEquals("inputPhones.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobMongoInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobMongoInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("personData", target.getAlias());
        assertEquals("personData.csv", target.getPhysicalName());
    }
}
```

#### TransformerTest

Se van a crear los test unitarios de la clase *Transformer.java* en la clase *TransformerTest.java*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("_id", DataTypes.IntegerType, false),
                        DataTypes.createStructField("phone", DataTypes.StringType, false)
                });

        final List<Row> data = Arrays.asList(
                RowFactory.create(1, "123456789"),
                RowFactory.create(3, "654321987"),
                RowFactory.create(5, "452112359")
        );

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(data, schema);

        Map<String, Dataset<Row>> datasets = new HashMap<>();
        datasets.put("inputPhones", dataset);

        try (MockedStatic<MongoIterableQuery> mockedMongoQuery = Mockito.mockStatic(MongoIterableQuery.class)) {
            mockedMongoQuery.when(() -> MongoIterableQuery.createQuery(
                            any(MyMongoHelper.class),
                            eq("mongodb.YOUR_BBDD.BATCH"),
                            any(InputData.class)))
                    .thenReturn(mock(MongoIterableQuery.class));

            final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

            assertNotNull(datasetMap);
            assertEquals(1, datasetMap.size());

            Dataset<Row> resultDataset = datasetMap.get("personData");
            assertNotNull(resultDataset);
        }
    }
}
```

#### MyMongoHelperTest
Se van a crear los test unitarios de la clase *MyMongoHelper.java* en la clase *MyMongoHelperTest.java*.

```java
class MyMongoHelperTest extends LRBASparkTest {

    private MyMongoHelper myMongoHelper;

    @BeforeEach
    void setUp() {
        myMongoHelper = new MyMongoHelper();
    }

    @Test
    void test_helper() {
        InputData inputData = new InputData();
        inputData.set_id("1");
        inputData.setPhone("123456789");

        myMongoHelper.setSearchValue(inputData);
        Document result = mock(Document.class);
        when(result.getString("name")).thenReturn("Maria Torres");
        when(result.getString("city")).thenReturn("Bilbao");
        when(result.getInteger("age")).thenReturn(28);

        MongoData mongoData = myMongoHelper.processResult(result);
        assertNotNull(mongoData);
        assertEquals("28", mongoData.getAge());
        assertEquals("your_collection", myMongoHelper.getCollection());
        assertEquals("FIND", myMongoHelper.getQueryType());
        assertNull(myMongoHelper.getAggregatePipeline());
        assertFalse(myMongoHelper.processNoData());
        assertEquals(new Document("_id","1"), myMongoHelper.getFindFilter());
    }
}
```

## Ejemplo 2 (Aggregate)

### Fichero de entrada

```csv input_cities.csv (CASO 2)
ciudad
Madrid
Bilbao
Sevilla
Barcelona
```

**NOTA**: Estos datos son solo para este ejemplo de desarrollo, se pueden utilizar otros datos.


### Implementación del builder

Se va a implementar el *job* en la clase *JobMongoInlineQueryBuilder.java*.

#### Source

Se crea el *source* de tipo *File CSV* para leer el fichero de entrada.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Csv.builder()
                    .alias("inputCities")
                    .physicalName("inputCities.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

#### Transform

En la clase *JobMongoInlineQueryBuilder.java* no modificar el método *registerTransform* que está por defecto.

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

#### Target

Se crea el *target* de tipo *File CSV* para escribir el fichero de salida.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Csv.builder()
                    .alias("outputCities")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .physicalName("outputCities.csv")
                    .humanReadable(true)
                    .delimiter(",")
                    .header(true)
                    .build()).build();
}
```

### Implementación del transformer

En la clase *Transformer.java* se va a modificar el método *transform* para iterar el dataset de entrada y realizar las consultas a la BBDD Mongo por cada fila.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<InputData> inputPhones = map.get("inputCities").as(Encoders.bean(InputData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    Dataset<MongoData> mongoResults = inputPhones.flatMap((FlatMapFunction<InputData, MongoData>) searchValue -> MongoIterableQuery.createQuery(
            new MyMongoHelper(),
            "mongodb.YOUR_BBDD.BATCH",
            searchValue), Encoders.bean(MongoData.class));

    datasetsToWrite.put("outputCities", mongoResults.toDF());
    return datasetsToWrite;
} 
```

### Implementación de las interfaces y beans

Se van a crear las clases *InputData.java* y *MongoData.java* para mapear los datos de entrada y salida respectivamente. Ambas clases **deben implementar la interfaz Serializable**.

#### InputData.java

```java
public class InputData implements Serializable {
    
    private String city;

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }
}
```

#### MongoData.java

```java
public class MongoData implements Serializable {

    private String city;
    private int sum;

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public int getSum() {
        return sum;
    }

    public void setSum(int sum) {
        this.sum = sum;
    }
} 
```

Por último, se va a crear la clase *MyMongoHelper.java* que implementará la interfaz *IMongoIterableQueryHandler* para crear las consultas parametrizadas a la BBDD Mongo,
setear los parámetros y mapear los resultados a la clase *MongoData.java*.

```java
public class MyMongoHelper implements IMongoIterableQueryHandler<InputData, MongoData>, Serializable {
    
    private String city;

    @Override
    public void setSearchValue(InputData input) {
        this.city = input.getCity();
    }

    @Override
    public String getCollection() {
        return "your_collection";
    }

    @Override
    public String getQueryType() {
        return "AGGREGATE";
    }
    
    @Override
    public Document getFindFilter() {
        return null;
    }

    @Override
    public List<Document> getAggregatePipeline() {
        Document match = new Document("$match", new Document("city", this.city));
        Document group = new Document("$group", new Document("_id", "$city")
                .append("sum", new Document("$sum", 1)));

        return List.of(match, group);
    }

    @Override
    public boolean processNoData() {
        return true;
    }

    @Override
    public MongoData processResult(Document document) {
        MongoData mongoData = new MongoData();
        mongoData.setCity(this.city);

        if (document == null) {
            LOGGER.warn("No data found for city: " + this.city);
            mongoData.setSum(0);
        }else {
            mongoData.setSum(document.getInteger("sum"));
        }
        return mongoData;
    }
}
```

### Test unitarios del job

#### JobMongoInlineQueryBuilder

Se van a crear los test unitarios de la clase *JobMongoInlineQueryBuilder.java* en la clase *JobMongoInlineQueryBuilderTest.java*.

```java
class JobMongoInlineQueryBuilderTest {

    private JobMongoInlineQueryBuilder jobMongoInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        this.jobMongoInlineQueryBuilder = new JobMongoInlineQueryBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobMongoInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputCities", source.getAlias());
        assertEquals("inputCities.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobMongoInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobMongoInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("outputCities", target.getAlias());
        assertEquals("outputCities.csv", target.getPhysicalName());
    }
}
```

#### TransformerTest

Se van a crear los test unitarios de la clase *Transformer.java* en la clase *TransformerTest.java*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("city", DataTypes.StringType, false),
                });

        final List<Row> data = Arrays.asList(
                RowFactory.create("Madrid"),
                RowFactory.create("Santander")
        );

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(data, schema);

        Map<String, Dataset<Row>> datasets = new HashMap<>();
        datasets.put("inputCities", dataset);

        try (MockedStatic<MongoIterableQuery> mockedMongoQuery = Mockito.mockStatic(MongoIterableQuery.class)) {
            mockedMongoQuery.when(() -> MongoIterableQuery.createQuery(
                            any(MyMongoHelper.class),
                            eq("mongodb.YOUR_BBDD.BATCH"),
                            any(InputData.class)))
                    .thenReturn(mock(MongoIterableQuery.class));

            final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

            assertNotNull(datasetMap);
            assertEquals(1, datasetMap.size());

            Dataset<Row> resultDataset = datasetMap.get("outputCities");
            assertNotNull(resultDataset);
        }
    }
}
```

#### MyMongoHelperTest
Se van a crear los test unitarios de la clase *MyMongoHelper.java* en la clase *MyMongoHelperTest.java*.

```java
class MyMongoHelperTest extends LRBASparkTest {

    private MyMongoHelper myMongoHelper;

    @BeforeEach
    void setUp() {
        myMongoHelper = new MyMongoHelper();
    }

    @Test
    void test_helper() {
        InputData inputData = new InputData();
        inputData.setCity("Madrid");
        
        Document match = new Document("$match", new Document("city", "Madrid"));
        Document group = new Document("$group", new Document("_id", "$city")
                .append("sum", new Document("$sum", 1)));

        List<Document> aggregate = List.of(match, group);

        myMongoHelper.setSearchValue(inputData);
        Document result = mock(Document.class);
        when(result.getString("city")).thenReturn("Madrid");
        when(result.getInteger("sum")).thenReturn(3);

        MongoData mongoData = myMongoHelper.processResult(result);

        assertNotNull(mongoData);
        assertEquals("Madrid", mongoData.getCity());
        assertEquals(3, mongoData.getSum());
        assertEquals("your_collection", myMongoHelper.getCollection());
        assertEquals("AGGREGATE", myMongoHelper.getQueryType());
        assertNull(myMongoHelper.getFindFilter());
        assertTrue(myMongoHelper.processNoData());
        assertEquals(aggregate, myMongoHelper.getAggregatePipeline());

        MongoData noResult = myMongoHelper.processResult(null);
        assertEquals(0, noResult.getSum());
    }
}
```

# 18-MongoDBInlineQueries/04-ExecuteJob.md
# 4. Ejecutar el Job
Para lograr ejecutar un job en local es necesario tener una base de datos Mongo con los datos necesarios.

## Ejecutar el job en el clúster
1 - Disponer de una BBDD Mongo.
2 - Hacer push del código del *job* a Bitbucket.
3 - Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 19-CouchbaseInlineQueries/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se realicen queries inline desde un dataset a una base de datos Couchbase.

# 19-CouchbaseInlineQueries/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Eclipse es un IDE de código abierto. Puede descargarse desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que aconsejamos utilizar. Tiene una versión gratuita que se puede descargar desde aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) te ayuda a generar el esqueleto de ficheros base de tu código, construir el *job*, hacer test y ejecutarlos en un entorno local. En este caso, será necesario el acceso al terminal del sistema.

# 19-CouchbaseInlineQueries/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

En este job se va a leer un fichero csv en un dataset, se va a completar con datos de una BBDD Couchbase mediante *inline queries* y se va a escribir en otro fichero csv.

**IMPORTANTE**: Para poder realizar este *codelab* es necesario tener acceso a una BBDD Couchbase en el cluster o disponer de un entorno local con una BBDD Couchbase.

## Datos de entrada

### Esquema de la BBDD

La colección de ejemplo que se va a utilizar en este *codelab* tiene las siguientes columnas:

```text
COD_CLIENTE, NOMBRE, CIUDAD, PAIS, TELEFONO, EMAIL, EDAD
```

### Fichero de entrada

Se va a leer un fichero csv que contendrá los campos *ciudad* y *edad* separados por comas, los cuales se utilizarán para realizar las consultas a la BBDD Couchbase.
El fichero tendrá el siguiente contenido:

```csv
ciudad,edad
Madrid,25
Bilbao,30
Barcelona,10
```

**NOTA**: Estos datos son solo para este ejemplo de desarrollo, se pueden utilizar otros datos.

## Implementación del builder

Se va a implementar el *job* en la clase *JobCouchbaseInlineQueryBuilder.java*.

### Source

Se va a leer el fichero csv que se ha creado en el paso anterior. Para ello se va a crear un *source* de tipo *File CSV*.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.CSV.builder()
                    .alias("inputFile")
                    .physicalName("fichero_entrada.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .sql("SELECT * FROM inputFile")
                    .build())
            .build();
}
```

### Transform

En la clase *JobCouchbaseInlineQueryBuilder.java* no modificar el método *registerTransform* que está por defecto. 

```java
@Override
public TransformConfig registerTransform() {
    return TransformConfig.TransformClass.builder().transform(new Transformer()).build();
}
```

### Target

Se va a escribir el fichero csv de salida. Para ello se va a crear un *target* de tipo *File CSV*.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.CSV.builder()
                    .alias("outputFile")
                    .physicalName("fichero_salida.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .build())
            .build();
}
```

## Implementación del transformer

En la clase *Transformer.java* se va a modificar el método *transform* para iterar el dataset de entrada y realizar las consultas a la BBDD Couchbase por cada fila.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<InputData> datasetEdades = datasetsFromRead.get("inputFile").as(Encoders.bean(InputData.class));

    Dataset<CouchbaseData> CouchbaseResults = datasetEdades.flatMap((FlatMapFunction<InputData, CouchbaseData>) row -> CouchbaseIterableQuery.createQuery(
            new MyCouchbaseHelper(),
            "couchbase.YOUR_UUAA.BATCH",
            row), Encoders.bean(CouchbaseData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    datasetsToWrite.put("outputFile", CouchbaseResults.toDF());

    return datasetsToWrite;
} 
```

## Implementación de las interfaces y beans

Se van a crear las clases *InputData.java* y *CouchbaseData.java* para mapear los datos de entrada y salida respectivamente. Ambas clases **deben implementar la interfaz Serializable**.

### InputData.java

```java
public class InputData implements Serializable {
    
    private String ciudad;
    private int edad;

    public String getCiudad() {
        return ciudad;
    }

    public void setCiudad(String ciudad) {
        this.ciudad = ciudad;
    }

    public int getEdad() {
        return edad;
    }

    public void setEdad(int edad) {
        this.edad = edad;
    }
}
```

### CouchbaseData.java

```java
public class CouchbaseData implements Serializable {

    private long COD_CLIENTE;
    private String NOMBRE;
    private String CIUDAD;
    private String PAIS;
    private String TELEFONO;
    private String EMAIL;
    private int EDAD;

    public long getCOD_CLIENTE() {
        return COD_CLIENTE;
    }
    
    public void setCOD_CLIENTE(long codCliente) {
        COD_CLIENTE = codCliente;
    }
    
    public String getNOMBRE() {
        return NOMBRE;
    }
    
    public void setNOMBRE(String nombre) {
        NOMBRE = nombre;
    }
    
    public String getCIUDAD() {
        return CIUDAD;
    }
    
    public void setCIUDAD(String ciudad) {
        CIUDAD = ciudad;
    }
    
    public String getPAIS() {
        return PAIS;
    }
    
    public void setPAIS(String pais) {
        PAIS = pais;
    }
    
    public String getTELEFONO() {
        return TELEFONO;
    }
    
    public void setTELEFONO(String telefono) {
        TELEFONO = telefono;
    }
    
    public String getEMAIL() {
        return EMAIL;
    }
    
    public void setEMAIL(String email) {
        EMAIL = email;
    }
    
    public int getEDAD() {
        return EDAD;
    }
    
    public void setEDAD(int edad) {
        EDAD = edad;
    }

} 
```

Por último, se va a crear la clase *MyCouchbaseHelper.java* que implementará la interfaz *ICouchbaseIterableQueryHandler* para crear las consultas parametrizadas a la BBDD Couchbase, 
setear los parámetros y mapear los resultados a la clase *CouchbaseData.java*.

```java
public class MyCouchbaseHelper implements ICouchbaseIterableQueryHandler<InputData, CouchbaseData>, Serializable {

    private static final long serialVersionUID = 1L;

    private String edad;
    private String ciudad;
    
    @Override
    public void setSearchValue(Bean s) {
       this.edad = s.getEdad();
       this.ciudad = s.getCiudad();
    }

    @Override
    public String getQuery() {
       return "SELECT * FROM PERSONAS WHERE EDAD = $edad AND CIUDAD = $ciudad";
    }

    @Override
    public Map<String, Object> getQueryParameters() {
        return Map.of(
            "edad", edad,
            "ciudad", ciudad
        );
    }

    @Override
    public CouchbaseData processResultDocument(Map<String, Object> document) {
        CouchbaseData couchbaseData = new CouchbaseData();
        if (document != null) {
            couchbaseData.setCOD_CLIENTE((Long) document.get("COD_CLIENTE"));
            couchbaseData.setNOMBRE((String) document.get("NOMBRE"));
            couchbaseData.setCIUDAD((String) document.get("CIUDAD"));
            couchbaseData.setPAIS((String) document.get("PAIS"));
            couchbaseData.setTELEFONO((String) document.get("TELEFONO"));
            couchbaseData.setEMAIL((String) document.get("EMAIL"));
            couchbaseData.setEDAD((Integer) document.get("EDAD"));
        } else {
            couchbaseData.setEDAD(Integer.parseInt(this.edad));
        }
    }

    @Override
    public boolean processNoData() {
       return true;
    }

}
```

## Test unitarios del job

### JobCouchbaseInlineQueryBuilder

Se van a crear los test unitarios de la clase *JobCouchbaseInlineQueryBuilder.java* en la clase *JobCouchbaseInlineQueryBuilderTest.java*.

```java
class JobCouchbaseInlineQueryBuilderTest {

    private JobCouchbaseInlineQueryBuilder jobCouchbaseInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        this.jobCouchbaseInlineQueryBuilder = new JobCouchbaseInlineQueryBuilder();
    }

    @Test
    void registerSources_na_SourceList() {
        final SourcesList sourcesList = this.jobCouchbaseInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertNotNull(sourcesList.getSources());
        assertEquals(1, sourcesList.getSources().size());

        final Source source = sourcesList.getSources().get(0);
        assertNotNull(source);
        assertEquals("inputFile", source.getAlias());
        assertEquals("fichero_entrada.csv", source.getPhysicalName());
    }

    @Test
    void registerTransform_na_Transform() {
        final TransformConfig transformConfig = this.jobCouchbaseInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
        assertNotNull(transformConfig.getTransform());
    }

    @Test
    void registerTargets_na_TargetList() {
        final TargetsList targetsList = this.jobCouchbaseInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertNotNull(targetsList.getTargets());
        assertEquals(1, targetsList.getTargets().size());

        final Target target = targetsList.getTargets().get(0);
        assertNotNull(target);
        assertEquals("outputFile", target.getAlias());
        assertEquals("fichero_salida.csv", target.getPhysicalName());
    }

}
```

### TransformerTest

Se van a crear los test unitarios de la clase *Transformer.java* en la clase *TransformerTest.java*.

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        this.transformer = new Transformer();
    }

    @Test
    void transform_Output() {
        StructType schema = DataTypes.createStructType(
                new StructField[]{
                        DataTypes.createStructField("edad", DataTypes.IntegerType, false),
                        DataTypes.createStructField("ciudad", DataTypes.StringType, false)
                });

        final List<Row> data = Arrays.asList(
                RowFactory.create(25, "Madrid"),
                RowFactory.create(10, "Barcelona"),
                RowFactory.create(30, "Bilbao")
        );

        DatasetUtils<Row> datasetUtils = new DatasetUtils<>();
        Dataset<Row> dataset = datasetUtils.createDataFrame(data, schema);

        Map<String, Dataset<Row>> datasets = new HashMap<>();
        datasets.put("inputFile", dataset);

        try (MockedStatic<CouchbaseIterableQuery> mockedCouchbaseQuery = Mockito.mockStatic(CouchbaseIterableQuery.class)) {
            mockedCouchbaseQuery.when(() -> CouchbaseIterableQuery.createQuery(
                            any(MyCouchbaseHelper.class),
                            eq("couchbase.YOUR_UUAA.BATCH"),
                            any(CouchbaseBean.class)))
                    .thenReturn(mock(CouchbaseIterableQuery.class));

            final Map<String, Dataset<Row>> datasetMap = this.transformer.transform(datasets);

            assertNotNull(datasetMap);
            assertEquals(1, datasetMap.size());

            Dataset<Row> resultDataset = datasetMap.get("outputFile");
            assertNotNull(resultDataset);
        }
    }
}
```

### MyCouchbaseHelperTest
Se van a crear los test unitarios de la clase *MyCouchbaseHelper.java* en la clase *MyCouchbaseHelperTest.java*.

```java
class MyCouchbaseHelperTest {

    private MyCouchbaseHelper myCouchbaseHelper;

    @BeforeEach
    void setUp() {
        myCouchbaseHelper = new MyCouchbaseHelper();
    }

    @Test
    void test_helper() throws SQLException {
        InputData inputData = new InputData();
        inputData.setEdad("30");
        inputData.setCiudad("Madrid");

        myCouchbaseHelper.setSearchValue(inputData);

        PreparedStatement preparedStatement = mock(PreparedStatement.class);
        myCouchbaseHelper.getQueryParameters().forEach((key, value) -> {
            try {
                when(preparedStatement.setObject(key, value)).thenReturn(null);
            } catch (SQLException e) {
                fail("Failed to set parameter: " + key);
            }
        });

        ResultSet resultSet = mock(ResultSet.class);
        when(resultSet.getLong("COD_CLIENTE")).thenReturn(123L);
        when(resultSet.getString("NOMBRE")).thenReturn("John Doe");
        when(resultSet.getString("CIUDAD")).thenReturn("Madrid");
        when(resultSet.getString("PAIS")).thenReturn("Spain");
        when(resultSet.getString("TELEFONO")).thenReturn("123456789");
        when(resultSet.getString("EMAIL")).thenReturn("email@email.com");
        when(resultSet.getInt("EDAD")).thenReturn(30);

        CouchbaseData CouchbaseData = myCouchbaseHelper.processResultDocument(resultSet);
        assertNotNull(CouchbaseData);

        CouchbaseData CouchbaseData2 = myCouchbaseHelper.processResultDocument(null);
        assertNotNull(CouchbaseData2);
        assertEquals(30, CouchbaseData2.getEDAD());

        assertEquals("SELECT * FROM PERSONAS WHERE EDAD = $edad AND CIUDAD = $ciudad", myCouchbaseHelper.getQuery());
    }
}
```

# 19-CouchbaseInlineQueries/04-ExecuteJob.md
# 4. Ejecutar el Job
Para lograr ejecutar un job en local es necesario tener una base de datos Couchbase con los datos necesarios.

## Ejecutar el job en el clúster
1 - Disponer de una BBDD Couchbase.
2 - Hacer push del código del *job* a Bitbucket.
3 - Ejecutar el *job* en el clúster. Para ello, despliegue el *job* siguiendo [esta guía](../../developerexperience/03-EtherConsoleDevelopment.md).

# 20-MixDBInlineQueries/01-Introduction.md
# 1. Introducción

Este *codelab* tiene como objetivo ayudar a los desarrolladores a implementar un job en el que se realicen queries inline combinando múltiples bases de datos. 

El objetivo es demostrar cómo integrar datos provenientes de diferentes fuentes, como Oracle, MongoDB y Elasticsearch, en un único flujo de procesamiento. Esto permitirá realizar consultas parametrizadas en cada base de datos, procesar los resultados y consolidar la información en un formato unificado.

Se implementarán ejemplos prácticos que mostrarán cómo interactuar con cada base de datos, configurar las consultas y manejar los datos de entrada y salida de manera eficiente.

# 20-MixDBInlineQueries/02-Prerequisites.md
# 2. Requisitos previos

## Java IDEs
Es necesario contar con un IDE para desarrollar el código. Se recomiendan las siguientes opciones:

- **Eclipse**: Un IDE de código abierto que puedes descargar desde aquí: [Descargar Eclipse](https://www.eclipse.org/downloads/packages/).
- **IntelliJ IDEA**: Otro IDE recomendado, con una versión gratuita disponible aquí: [Descargar IntelliJ IDEA Community Edition](https://www.jetbrains.com/es-es/idea/download/).

## LRBA CLI
La [interfaz de línea de comandos LRBA](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content5) es esencial para generar el esqueleto de los ficheros base, construir el *job*, realizar pruebas y ejecutarlo en un entorno local. Asegúrate de tener acceso al terminal del sistema.

## Bases de datos necesarias
Para este ejemplo, se requiere acceso a las siguientes bases de datos:

1. **Oracle**: Configura una instancia de Oracle y asegúrate de tener las credenciales necesarias para conectarte.
2. **MongoDB**: Asegúrate de tener una base de datos MongoDB configurada y accesible.
3. **Elasticsearch**: Configura un clúster de Elasticsearch y verifica que esté operativo.

Estas dependencias pueden añadirse al archivo `pom.xml` si utilizas Maven o al archivo `build.gradle` si utilizas Gradle.

## Acceso a datos
Es necesario contar con los esquemas, colecciones y/o índices configurados en cada base de datos para realizar las consultas inline. Asegúrate de que los datos estén preparados para las pruebas.

# 20-MixDBInlineQueries/03-HowToImplementTheJob.md
# 3. Cómo implementar el job

Este job implementará un ejemplo que combina las tres bases de datos (Oracle, MongoDB y Elasticsearch) en un único flujo de procesamiento. Se leerá un fichero CSV con datos de entrada, se realizarán consultas a cada base de datos utilizando las clases `IJdbcIterableQueryHandler`, `IMongoIterableQueryHandler` y `IElasticIterableQueryHandler`, y se consolidarán los resultados en un fichero CSV de salida.

**IMPORTANTE**: Para poder realizar este *codelab* es necesario tener acceso a las tres bases de datos (Oracle, MongoDB y Elasticsearch) en el cluster o disponer de un entorno local con estas bases de datos configuradas.

## Datos de entrada

### Fichero de entrada

El fichero CSV contendrá los siguientes campos:

```csv
ciudad,edad,empresa,anio,id_persona,telefono
Madrid,25,Zedalis,2019,1,123456789
Bilbao,30,Orbaxter,2018,3,987654321
Barcelona,10,Google,2020,5,654321789
```

Estos datos se utilizarán para realizar consultas a las tres bases de datos.

## Implementación del builder

El *job* será implmentado en la clase *JobMixInlineQueryBuilder.java*.

### Source

Se crea el *source* de tipo *File CSV* para leer el fichero de entrada.

```java
@Override
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.CSV.builder()
                    .alias("inputFile")
                    .physicalName("input_data.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

### Transform

Cada builder realizará consultas a su respectiva base de datos:

1. **Consultas a Oracle**: Utilizando `IJdbcIterableQueryHandler` y `MyJdbcHelper`.
2. **Consultas a MongoDB**: Utilizando `IMongoIterableQueryHandler` y `MyMongoHelper`.
3. **Consultas a Elasticsearch**: Utilizando `IElasticIterableQueryHandler` y `MyElasticHelper`.

Los resultados de cada consulta se consolidarán en un único dataset.

```java
@Override
public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> datasetsFromRead) {
    Dataset<InputData> inputDataset = datasetsFromRead.get("inputFile").as(Encoders.bean(InputData.class));

    // Consultas a Oracle
    Dataset<OracleData> oracleResults = inputDataset.flatMap(
            (FlatMapFunction<InputData, OracleData>) row -> JdbcIterableQuery.createQuery(
                    new MyJdbcHelper(),
                    "oracle.YOUR_UUAA.BATCH",
                    row), Encoders.bean(OracleData.class));

    // Consultas a MongoDB
    Dataset<MongoData> mongoResults = inputDataset.flatMap(
            (FlatMapFunction<InputData, MongoData>) row -> MongoIterableQuery.createQuery(
                    new MyMongoHelper(),
                    "mongodb.YOUR_BBDD.BATCH",
                    row), Encoders.bean(MongoData.class));

    // Consultas a Elasticsearch
    Dataset<ElasticData> elasticResults = inputDataset.flatMap(
            (FlatMapFunction<InputData, ElasticData>) row -> ElasticIterableQuery.createQuery(
                    new MyElasticHelper(),
                    "elastic.YOUR_UUAA.BATCH",
                    row), Encoders.bean(ElasticData.class));

    // Consolidar resultados
    Dataset<ConsolidatedData> consolidatedResults = oracleResults
            .join(mongoResults, "id")
            .join(elasticResults, "id")
            .map(row -> new ConsolidatedData(row), Encoders.bean(ConsolidatedData.class));

    Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
    datasetsToWrite.put("outputFile", consolidatedResults.toDF());

    return datasetsToWrite;
}
```

### Target

Se escribirá el fichero CSV consolidado de salida.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.CSV.builder()
                    .alias("outputFile")
                    .physicalName("output_data.csv")
                    .serviceName("bts.YOUR_UUAA.BATCH")
                    .header(true)
                    .delimiter(",")
                    .build())
            .build();
}
```

## Implementación de las interfaces y beans

Se crearán las clases `InputData.java`, `OracleData.java`, `MongoData.java`, `ElasticData.java` y `ConsolidatedData.java` para mapear los datos de entrada, salida y resultados consolidados.

### InputData.java

```java
public class InputData implements Serializable {
    private String ciudad;
    private int edad;
    private String empresa;
    private String anio;
    private String id_persona;
    private String telefono;

    // Getters y setters
}
```

### ConsolidatedData.java

```java
public class ConsolidatedData implements Serializable {
    private String ciudad;
    private int edad;
    private String empresa;
    private String anio;
    private String id_persona;
    private String telefono;
    private String nombreCompleto;
    private String proyectoAsignado;
    private String antiguedad;

    // Constructor, getters y setters
}
```
### OracleData.java
```java
public class OracleData implements Serializable {
    private String id;
    private String nombreCompleto;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getNombreCompleto() {
        return nombreCompleto;
    }

    public void setNombreCompleto(String nombreCompleto) {
        this.nombreCompleto = nombreCompleto;
    }
}
```

### MongoData.java
```java
public class MongoData implements Serializable {
    private String id;
    private String proyectoAsignado;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getProyectoAsignado() {
        return proyectoAsignado;
    }

    public void setProyectoAsignado(String proyectoAsignado) {
        this.proyectoAsignado = proyectoAsignado;
    }
}
```

### ElasticData.java
```java
public class ElasticData implements Serializable {
    private String id;
    private String antiguedad;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getAntiguedad() {
        return antiguedad;
    }

    public void setAntiguedad(String antiguedad) {
        this.antiguedad = antiguedad;
    }
}
```
## Implementación de los helpers

Se implementarán las clases `MyJdbcHelper`, `MyMongoHelper` y `MyElasticHelper` para realizar las consultas a las bases de datos. Estas clases deben implementar las interfaces correspondientes (`IJdbcIterableQueryHandler`, `IMongoIterableQueryHandler` e `IElasticIterableQueryHandler`).

### MyJdbcHelper.java

```java
public class MyJdbcHelper implements IJdbcIterableQueryHandler<InputData, OracleData>, Serializable {

    private static final long serialVersionUID = 1L;

    private String id;

    @Override
    public void setSearchValue(InputData s) {
        this.id = s.getId();
    }

    @Override
    public String getQuery() {
        return "SELECT * FROM PERSONAS WHERE ID = ?";
    }

    @Override
    public void prepareBindVariables(PreparedStatement pst) throws SQLException {
        pst.setString(1, id);
    }

    @Override
    public OracleData processResultSet(ResultSet rs) {
        OracleData rowData = new OracleData();

        if (rs != null) {
            try {
                rowData.setId(rs.getString("ID"));
                rowData.setNombreCompleto(rs.getString("NOMBRE_COMPLETO"));
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
        return rowData;
    }

    @Override
    public boolean processNoData() {
        return true;
    }
}
```

### MyMongoHelper.java

```java
public class MyMongoHelper implements IMongoIterableQueryHandler<InputData, MongoData>, Serializable {

    private static final long serialVersionUID = 1L;

    private String id;

    @Override
    public void setSearchValue(InputData input) {
        this.id = input.getId();
    }

    @Override
    public String getCollection() {
        return "your_collection";
    }

    @Override
    public String getQueryType() {
        return "FIND";
    }

    @Override
    public Document getFindFilter() {
        return new Document("id", this.id);
    }

    @Override
    public List<Document> getAggregatePipeline() {
        return Collections.emptyList();
    }

    @Override
    public boolean processNoData() {
        return false;
    }

    @Override
    public MongoData processResult(Document document) {
        MongoData mongoData = new MongoData();
        mongoData.setId(this.id);
        mongoData.setProyectoAsignado(document.getString("proyectoAsignado"));
        return mongoData;
    }
}
```

### MyElasticHelper.java
```java
public class MyElasticHelper implements IElasticIterableQueryHandler<SearchBeanElastic, ElasticData>, Serializable {
    private static final Logger LOGGER = LoggerFactory.getLogger(MyElasticHelper.class);

    private static final long serialVersionUID = 1L;

    private String id;

    @Override
    public void setSearchValue(SearchBeanElastic searchBeanElastic) {
        this.id = searchBeanElastic.getId();
    }

    @Override
    public String getQuery() {
        return """
                {
                   "query": {
                     "match_phrase": {
                       "id": "{{id_param}}"
                     }
                   }
                 }
                """;
    }

    @Override
    public String getIndex() {
        return "i_lrba_test";
    }

    @Override
    public Map<String, Object> getMapBindVariables() {
        return Map.of("id_param", id);
    }

    @Override
    public ElasticData processResultDocument(Map<String, Object> document) {
        LOGGER.warn("Processing result");
        if (document != null) {
            ElasticData elasticData = new ElasticData();
            elasticData.setId((String) document.get("id"));
            elasticData.setAntiguedad((String) document.get("antiguedad"));
            return elasticData;
        } else {
            LOGGER.warn("No results for the elastic query");
            return null;
        }
    }

    @Override
    public boolean processNoData() {
        return true;
    }
}

```
## Test unitarios del job

Se crearán los test unitarios para las clases `JobMixInlineQueryBuilder`, `Transformer` y los helpers (`MyJdbcHelper`, `MyMongoHelper`, `MyElasticHelper`) siguiendo los ejemplos de los casos anteriores.
### `JobMixInlineQueryBuilderTest`

```java
class JobMixInlineQueryBuilderTest {

    private JobJMixInlineQueryBuilder jobMixInlineQueryBuilder;

    @BeforeEach
    void setUp() {
        jobMixInlineQueryBuilder = new JobMixInlineQueryBuilder();
    }

    @Test
    void testRegisterSources() {
        SourcesList sourcesList = jobMixInlineQueryBuilder.registerSources();
        assertNotNull(sourcesList);
        assertEquals(1, sourcesList.getSources().size());
    }

    @Test
    void testRegisterTransform() {
        TransformConfig transformConfig = jobMixInlineQueryBuilder.registerTransform();
        assertNotNull(transformConfig);
    }

    @Test
    void testRegisterTargets() {
        TargetsList targetsList = jobMixInlineQueryBuilder.registerTargets();
        assertNotNull(targetsList);
        assertEquals(1, targetsList.getTargets().size());
    }
}
```


### `TransformerTest`

```java
class TransformerTest extends LRBASparkTest {

    private Transformer transformer;

    @BeforeEach
    void setUp() {
        transformer = new Transformer();
    }

    @Test
    void testTransform() {
        Map<String, Dataset<Row>> datasets = new HashMap<>();
        Dataset<Row> inputDataset = mock(Dataset.class);
        datasets.put("inputFile", inputDataset);

        Map<String, Dataset<Row>> result = transformer.transform(datasets);
        assertNotNull(result);
        assertTrue(result.containsKey("outputFile"));
    }
}
```

### `MyJdbcHelperTest`

```java
class MyJdbcHelperTest {

    private MyJdbcHelper myJdbcHelper;

    @BeforeEach
    void setUp() {
        myJdbcHelper = new MyJdbcHelper();
    }

    @Test
    void testQuery() {
        assertEquals("SELECT * FROM PERSONAS WHERE ID = ?", myJdbcHelper.getQuery());
    }

    @Test
    void testProcessResultSet() throws SQLException {
        ResultSet resultSet = mock(ResultSet.class);
        when(resultSet.getString("ID")).thenReturn("1");
        when(resultSet.getString("NOMBRE_COMPLETO")).thenReturn("John Doe");

        OracleData result = myJdbcHelper.processResultSet(resultSet);
        assertNotNull(result);
        assertEquals("1", result.getId());
        assertEquals("John Doe", result.getNombreCompleto());
    }
}
```

### `MyMongoHelperTest`

```java
class MyMongoHelperTest {

    private MyMongoHelper myMongoHelper;

    @BeforeEach
    void setUp() {
        myMongoHelper = new MyMongoHelper();
    }

    @Test
    void testGetFindFilter() {
        InputData inputData = new InputData();
        inputData.setId("123");
        myMongoHelper.setSearchValue(inputData);

        Document filter = myMongoHelper.getFindFilter();
        assertNotNull(filter);
        assertEquals("123", filter.getString("id"));
    }

    @Test
    void testProcessResult() {
        Document document = new Document("proyectoAsignado", "Proyecto A");
        MongoData result = myMongoHelper.processResult(document);

        assertNotNull(result);
        assertEquals("Proyecto A", result.getProyectoAsignado());
    }
}
```

### `MyElasticHelperTest`

```java
class MyElasticHelperTest {

    private MyElasticHelper myElasticHelper;

    @BeforeEach
    void setUp() {
        myElasticHelper = new MyElasticHelper();
    }

    @Test
    void testQuery() {
        String expectedQuery = """
                {
                   "query": {
                     "match_phrase": {
                       "id": "{{id_param}}"
                     }
                   }
                 }
                """;
        assertEquals(expectedQuery, myElasticHelper.getQuery());
    }

    @Test
    void testProcessResultDocument() {
        Map<String, Object> document = Map.of("id", "123", "antiguedad", "5 años");
        ElasticData result = myElasticHelper.processResultDocument(document);

        assertNotNull(result);
        assertEquals("123", result.getId());
        assertEquals("5 años", result.getAntiguedad());
    }
}
```

