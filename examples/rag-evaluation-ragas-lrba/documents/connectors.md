# connectors/01-File.md
# File
LRBA Spark permite leer y escribir grandes archivos en diferentes formatos para distintos sistemas de almacenamiento.

## Persistencia de almacenamiento de objetos
### Entorno local
El entorno local es util para probar un *job* en el *host* local del desarrollador. Este almacenamiento esta completamente prohibido fuera de las pruebas locales. Los archivos deben estar en `{directorio_job}/local-execution/files`.

Los valores de los campos utilizados en los *builders* son:
```
{YOUR_INVENTORY_SERVICE_NAME} = local.logicalDataStore.batch
{YOUR_PHYSICAL_NAME} = {YOUR_FILE_NAME}.{FILE_FORMAT}
```

### BTS
*BTS (Bucket Temporary Storage)* es un servicio de  **almacenamiento de objetos**  que permite guardar datos como 
objetos (archivos) dentro de *buckets* usando *Scality S3*.

BTS debe utilizarse para **compartir archivos entre diferentes UUAAs** dependiendo de las etiquetas (etiqueta *fileVisibility*) asociadas a los archivos almacenados. Estos ficheros se eliminarán automáticamente.  

Echa un vistazo a nuestro [*Codelab* de Impersonación](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Compartir%20ficheros%20entre%20UUAAs%20%28ESP%29/Introducci%C3%B3n/) para ver como utilizarlo.

El servicio de inventario del BTS se crea por defecto. Los valores de los campos utilzados en los *builders* son:
```
{YOUR_INVENTORY_SERVICE_NAME} = bts.{UUAA}.BATCH
{YOUR_PHYSICAL_NAME} = {YOUR_FILE_NAME}.{FILE_FORMAT}
```

Desde el equipo de Data Governance, se requiere la siguiente [nomenclatura](https://docs.google.com/document/d/1DACWNfjutc8gYAn7JnslPn8vsE8ZlqJ-pAjrMPHZnUA/edit?tab=t.0) de ficheros para las aplicaciones BASDM (Beyond Analytical Single Data Model). [Más información](https://platform.bbva.com/single-data-model/documentation/1uW8IoRvn8O4DuUqd1lcz5laYJieAKuFjXjOaLsADzyw/informational/operative-model/operative-model)

## Formatos de archivo

Cada formato de fichero tiene su propio *builder* dependiendo de si el fichero es el origen (*source*) 
o el destino (*target*) de los datos. Estos ***builders*** deben utilizarse en la clase ***JobBuilder***. 
Al declarar un archivo de origen, el desarrollador puede seleccionar solo algunos campos o filtrar filas en base 
a los campos necesarios utilizando SQL.

### Parquet

[Apache Parquet](https://parquet.apache.org/) es un formato de almacenamiento por columnas disponible para 
cualquier proyecto en el ecosistema Hadoop, independientemente de la elección del *framework*, el modelo de datos 
o el lenguaje de programación. Apache Parquet esta diseñado para aportar eficiencia, es mas rápido y mas pequeño,
en comparación con archivos basados en filas como CSV.

Este formato es el mejor para compartir información entre *jobs* debido a su **eficiencia, velocidad y pequeño tamaño**.

#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo. 
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo *alias*, no es el nombre real de la tabla.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark Parquet](https://spark.apache.org/docs/latest/sql-data-sources-parquet.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del *job* si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.Parquet.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .sql({YOUR_SQL})
        .addOption({{KEY}}, {{VALUE}})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Target builder

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de salida. Depende del almacenamiento del objeto.
- **fileVisibility *(OPCIONAL)***: Indica quién tiene acceso al fichero. Por defecto, *PRIVATE*. Valores permitidos: *PRIVATE, PUBLIC y GROUP_SHARED*.
- **fileAvailability *(OPCIONAL)***: Indica el tiempo que esta el archivo disponible en BTS. Por defecto, 3 días.
Valores permitidos: 1 día, 2 días, 3 días y una semana.
- **informationType *(OPCIONAL)***: Este campo se utiliza para indicar el tipo de la información que contiene el fichero. Por defecto, es *NOT_PROTECTED_DATA*. Valores permitidos: *INTERNAL_USE, SECRETS_AND_KEYS, PERSONAL_IDENTIFICATION, NOT_PROTECTED_DATA, SENSITIVE_PERSONAL_DATA y FRAUD_ENABLERS*.
- **repartitionColumn *(OPCIONAL)***: Este campo se utiliza para indicar cuál es la columna por la que se va a reparticionar y guardar el *Dataset*.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark Parquet](https://spark.apache.org/docs/latest/sql-data-sources-parquet.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
  
Ejemplo de código:
```java
Target.File.Parquet.builder()
        .alias({YOUR_TARGET_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .fileAvailability({AvailabilityType.ONE_DAY|TWO_DAYS|THREE_DAYS|WEEK})
        .fileVisibility({VisibilityType.PUBLIC|PRIVATE|GROUP_SHARED})
        .informationContentType({InformationContentType.INTERNAL_USE|SECRETS_AND_KEYS|PERSONAL_IDENTIFICATION|
                        NOT_PROTECTED_DATA|SENSITIVE_PERSONAL_DATA|FRAUD_ENABLERS})
        .repartitionColumn({YOUR_REPARTITION_COLUMN})
        .addOption({{KEY}}, {{VALUE}})
        .build()
```

### CSV

Un [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) es un archivo de texto delimitado que utiliza una coma para separar los valores.

No se recomienda el uso de archivos CSV. Por rendimiento es mejor utilizar archivos Parquet. No es una prohibición, pero se deben utilizar sólo si es necesario.

#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo *alias*, no es el nombre real de la tabla.
- **header *(OPCIONAL)***: Este campo se utiliza para incluir las cabeceras en el *dataset* durante la lectura. 
Por defecto, *true*.
- **delimiter *(OPCIONAL)***: Indica el delimitador utilizado en el fichero. Por defecto, ",".
- **preserveWhiteSpaces *(OPCIONAL)***: Conservar los espacios al leer el archivo CSV. Por defecto, *false*.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark  csv](https://spark.apache.org/docs/latest/sql-data-sources-csv.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del job si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.Csv.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME}) 
        .physicalName({YOUR_PHYSICAL_NAME})
        .sql({YOUR_SQL})
        .header({true|false})
        .delimiter({YOUR_DELIMITER}) 
        .preserveWhiteSpaces({true|false})
        .addOption({{KEY}}, {{VALUE}})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Target builder

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**:  Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el fichero de salida. Depende del almacenamiento del objeto.
- **header *(OPCIONAL)***: Este campo se utiliza para incluir las cabeceras en el *dataset* durante la lectura. Por defecto, *true*.
- **delimiter *(OPCIONAL)***: Indica el delimitador utilizado en el fichero. Por defecto, ",".
- **preserveWhiteSpaces *(OPCIONAL)***: Conservar los espacios al generar el archivo CSV. Por defecto, *false*.
- **humanReadable *(OPCIONAL)***: Este campo se utiliza para indicar si desea escribir un único archivo sin particiones. Por defecto, *false*. Tenga cuidado al utilizar esta opción, si el conjunto de datos es demasiado grande puede comprometer el rendimiento y causar problemas de memoria.
- **fileVisibility *(OPCIONAL)***: Indica quién tiene acceso al fichero. Por defecto, *PRIVATE*.
Valores permitidos: *PRIVATE, PUBLIC y GROUP_SHARED*.
- **fileAvailability *(OPCIONAL)***: Indica el tiempo que esta el archivo disponible en BTS. Por defecto, 3 días.
Valores permitidos: 1 día, 2 días, 3 días y una semana.
- **informationType *(OPCIONAL)***: Este campo se utiliza para indicar el tipo de la información que contiene el fichero. Por defecto, *NOT_PROTECTED_DATA*. Valores permitidos: *INTERNAL_USE, SECRETS_AND_KEYS, PERSONAL_IDENTIFICATION, NOT_PROTECTED_DATA, SENSITIVE_PERSONAL_DATA y FRAUD_ENABLERS*.
- **repartitionColumn *(OPCIONAL)***: Este campo se utiliza para indicar cuál es la columna por la que se va a reparticionar y guardar el *Dataset*.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark csv](https://spark.apache.org/docs/latest/sql-data-sources-csv.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.

Ejemplo de código:
```java
Target.File.Csv.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .header({true|false}) 
        .delimiter({YOUR_DELIMITER}) 
        .preserveWhiteSpaces({true|false})
        .humanReadable({true|false})
        .fileAvailability({AvailabilityType.ONE_DAY|TWO_DAYS|THREE_DAYS|WEEK})
        .fileVisibility({VisibilityType.PUBLIC|PRIVATE|GROUP_SHARED})
        .informationContentType({InformationContentType.INTERNAL_USE|SECRETS_AND_KEYS|PERSONAL_IDENTIFICATION|
                        NOT_PROTECTED_DATA|SENSITIVE_PERSONAL_DATA|FRAUD_ENABLERS})
        .repartitionColumn({YOUR_REPARTITION_COLUMN})
        .addOption({{KEY}}, {{VALUE}})
        .build()
```

### Texto plano

El texto plano es un archivo sin formato que permite al desarrollador trabajar con archivos de estructura personalizada. En Spark sólo es posible escribir *Datasets* como archivos de texto plano cuando tienen una sola columna. 


#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de texto plano de Spark](https://spark.apache.org/docs/latest/sql-data-sources-text.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del *job* si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.PlainText.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .addOption({{KEY}}, {{VALUE}})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Target builder

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el fichero de salida. Depende del almacenamiento del objeto.
- **humanReadable *(OPCIONAL)***: Este campo se utiliza para indicar si desea escribir un único archivo sin particiones. Por defecto, *false*. Tenga cuidado al utilizar esta opción, si el conjunto de datos es demasiado grande puede comprometer el rendimiento y causar problemas de memoria.
- **fileVisibility *(OPCIONAL)***: Indica quién tiene acceso al fichero. Por defecto, *PRIVATE*. Valores permitidos: *PRIVATE, PUBLIC y GROUP_SHARED*.
- **fileAvailability *(OPCIONAL)***: Indica el tiempo que esta el archivo disponible en BTS. Por defecto, 3 días.
Valores permitidos: 1 día, 2 días, 3 días y una semana.
- **informationContentType *(OPCIONAL)***: Este campo se utiliza para indicar el tipo de la información que contiene el fichero. Por defecto,*NOT_PROTECTED_DATA*. Valores permitidos: *INTERNAL_USE, SECRETS_AND_KEYS, PERSONAL_IDENTIFICATION, NOT_PROTECTED_DATA, SENSITIVE_PERSONAL_DATA y FRAUD_ENABLERS*.
- **repartitionColumn *(OPCIONAL)***: Este campo se utiliza para indicar cuál es la columna por la que se va a reparticionar y guardar el *Dataset*.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de texto plano de Spark](https://spark.apache.org/docs/latest/sql-data-sources-text.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
  
Ejemplo de código:
```java
Target.File.PlainText.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .humanReadable({true|false})
        .fileAvailability({AvailabilityType.ONE_DAY|TWO_DAYS|THREE_DAYS|WEEK})
        .fileVisibility({VisibilityType.PUBLIC|PRIVATE|GROUP_SHARED})
        .informationContentType({InformationContentType.INTERNAL_USE|SECRETS_AND_KEYS|PERSONAL_IDENTIFICATION|
                        NOT_PROTECTED_DATA|SENSITIVE_PERSONAL_DATA|FRAUD_ENABLERS})
        .repartitionColumn({YOUR_REPARTITION_COLUMN})
        .addOption({{KEY}}, {{VALUE}})
        .build()
```
### JSON

Un [JSON](https://es.wikipedia.org/wiki/JSON) es un fichero de texto sencillo para el intercambio de datos.

No se recomienda el uso de archivos JSON. Por rendimiento es mejor utilizar archivos Parquet. No es una prohibición, pero se deben utilizar sólo si es necesario.

#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo *alias*, no es el nombre real de la tabla.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark json](https://spark.apache.org/docs/latest/sql-data-sources-json.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del job si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.Json.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME}) 
        .physicalName({YOUR_PHYSICAL_NAME})
        .sql({YOUR_SQL})
        .addOption({{KEY}}, {{VALUE}})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Target builder

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**:  Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el fichero de salida. Depende del almacenamiento del objeto.
- **humanReadable *(OPCIONAL)***: Este campo se utiliza para indicar si desea escribir un único archivo sin particiones. Por defecto, *false*. Tenga cuidado al utilizar esta opción, si el conjunto de datos es demasiado grande puede comprometer el rendimiento y causar problemas de memoria.
- **fileVisibility *(OPCIONAL)***: Indica quién tiene acceso al fichero. Por defecto, *PRIVATE*.
Valores permitidos: *PRIVATE, PUBLIC y GROUP_SHARED*.
- **fileAvailability *(OPCIONAL)***: Indica el tiempo que esta el archivo disponible en BTS. Por defecto, 3 días.
Valores permitidos: 1 día, 2 días, 3 días y una semana.
- **informationType *(OPCIONAL)***: Este campo se utiliza para indicar el tipo de la información que contiene el fichero. Por defecto, *NOT_PROTECTED_DATA*. Valores permitidos: *INTERNAL_USE, SECRETS_AND_KEYS, PERSONAL_IDENTIFICATION, NOT_PROTECTED_DATA, SENSITIVE_PERSONAL_DATA y FRAUD_ENABLERS*.
- **repartitionColumn *(OPCIONAL)***: Este campo se utiliza para indicar cuál es la columna por la que se va a reparticionar y guardar el *Dataset*.
- **addOption *(OPCIONAL)***: Añadir opción de [Opciones de fichero de Spark json](https://spark.apache.org/docs/latest/sql-data-sources-json.html#data-source-option). Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de fichero" al final de este documento.

Ejemplo de código:
```java
Target.File.Json.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .humanReadable({true|false})
        .fileAvailability({AvailabilityType.ONE_DAY|TWO_DAYS|THREE_DAYS|WEEK})
        .fileVisibility({VisibilityType.PUBLIC|PRIVATE|GROUP_SHARED})
        .informationContentType({InformationContentType.INTERNAL_USE|SECRETS_AND_KEYS|PERSONAL_IDENTIFICATION|
                        NOT_PROTECTED_DATA|SENSITIVE_PERSONAL_DATA|FRAUD_ENABLERS})
        .repartitionColumn({YOUR_REPARTITION_COLUMN})
        .addOption({{KEY}}, {{VALUE}})
        .build()
```

### Cobol

Cobol es un fichero en EBCDIC y posiciones fijas generado por el lenguaje de programación homónimo, que contiene una colección de registros relacionados. Su formato viene definido por una *COPY*. Generalmente se crean en el mainframe del banco a través de la arquitectura host. 

#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **copybook**: El nombre del archivo del *copybook*. Debe incluirse en la carpeta *resources* del *job*.
- **dropValueFillers *(OPCIONAL)***: Si es *true*, todos los campos que no sean *GROUP FILLER* se eliminarán del esquema de salida. Si es *false*, estos campos se conservarán. Por defecto, es *true*.
- **recordLength *(OPCIONAL)***: Permite modificar la longitud del registro (en bytes). Normalmente, el tamaño se deriva del *copybook*. Especificar explícitamente el tamaño del registro puede ser útil para depurar archivos registro de longitud fija.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del *job* si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.Cobol.Fixed.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .copybook({YOUR_COPYBOOK_NAME})
        .dropValueFillers({true|false})
        .recordLength({RECORD_LENGTH})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Consejos para pruebas y ejecución en local

Para ejecutar localmente o probar el *builder* de Cobol, es necesario declarar dos variables de entorno de arquitectura utilizadas por el *builder*.
```
LRBA_APPLICATION_COUNTRY=gl
LRBA_COBOL_CHARSETS="{\"gl\": \"IBM284\"}"
```
Para más información sobre cómo declararlas en una ejecución local, consulte "Declarar variables en el entorno local" en la documentación [LRBA properties](../../01-LRBAProperties.md) y para declararlas para tests consulte "Mock para variables de entorno en tests" en [Utils](../01-Utils.md).  

*IMPORTANTE:* Por favor, no declare estas variables de arquitectura en la Consola Ether. El despliegue fallará.

### BINARIO

Un Binario es un fichero que contiene información de cualquier tipo codificada en binario.

#### Source builder

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo *alias*, no es el nombre real de la tabla.
- **ignoreMissingFiles *(OPCIONAL)***: Continuar con la ejecución del job si no se encuentra el archivo. Por defecto, es *false* y el *job* termina con un error de archivo no encontrado. Cuando el fichero no existe y la ejecución continua, no habrá ningún registro con ese alias en el mapa de *DataSet* del *transformer* ya que no se ha añadido. Será necesario verificar su existencia utilizando la función *containsKey*.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **moveFilePath *(OPCIONAL)***: Mueve el archivo de origen a la ruta especificada en el BTS. Este parámetro no se puede utilizar si `deleteFile` está a *true*.  El uso de *wildcards* para el path de destino no está permitido.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

Ejemplo de código:
```java
Source.File.Binary.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME}) 
        .physicalName({YOUR_PHYSICAL_NAME})
        .sql({YOUR_SQL})
        .ignoreMissingFiles({true|false})
        .deleteFile({true|false})
        .moveFilePath({FILE_NEW_PATH})
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```

#### Target builder

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName *(OPCIONAL)***: Nombre utilizado para alojar los ficheros de salida en una ruta común. Dentro de esta ruta, los ficheros seguirán un path individual especificado. En caso de que este valor esté vacío, los ficheros se escribirán desde la raíz. Depende del almacenamiento de los objetos. Por defecto, *vacío*.
- **fileVisibility *(OPCIONAL)***: Indica quién tiene acceso a los ficheros. Por defecto, *PRIVATE*.
Valores permitidos: *PRIVATE, PUBLIC y GROUP_SHARED*.
- **fileAvailability *(OPCIONAL)***: Indica el tiempo que están los archivos disponibles en BTS. Por defecto, 3 días.
  Valores permitidos: 1 día, 2 días, 3 días y una semana.
- **informationType *(OPCIONAL)***: Este campo se utiliza para indicar el tipo de la información que contienen los ficheros. Por defecto, *NOT_PROTECTED_DATA*. Valores permitidos: *INTERNAL_USE, SECRETS_AND_KEYS, PERSONAL_IDENTIFICATION, NOT_PROTECTED_DATA, SENSITIVE_PERSONAL_DATA y FRAUD_ENABLERS*.

Ejemplo de código:
```java
Target.File.Binary.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName({YOUR_INVENTORY_SERVICE_NAME})
        .physicalName({YOUR_PHYSICAL_NAME})
        .fileAvailability({AvailabilityType.ONE_DAY|TWO_DAYS|THREE_DAYS|WEEK})
        .fileVisibility({VisibilityType.PUBLIC|PRIVATE|GROUP_SHARED})
        .informationContentType({InformationContentType.INTERNAL_USE|SECRETS_AND_KEYS|PERSONAL_IDENTIFICATION|
                        NOT_PROTECTED_DATA|SENSITIVE_PERSONAL_DATA|FRAUD_ENABLERS})
        .build()
```

**IMPORTANTE**: Desde la arquitectura se proporciona la clase **BinaryFileBean**. Esta clase contiene todos los campos necesarios para poder indicarle al conector que ficheros binarios escribir y en qué ruta relativa dentro del *physicalName* especificado. Es necesario que el dataset que llegue al Target sea de este tipo para el correcto funcionamiento del conector.

## Wildcards
Spark permite la lectura de múltiples archivos utilizando *wildcards*. La arquitectura soporta el uso de *wildcards* en el campo *physicalName* de los *builders* de *Source*. Es importante entender como se comportan los *wildcards* en Spark y en la arquitectura al usar los parámetros *deleteFile* y *moveFilePath*.

### Wildcard en el campo *physicalName*
Dado el siguiente sistema de ficheros:

```shell
s3://files/inputs/
  ├── fileName_1.parquet
  ├── fileName_2.parquet
  ├── fileName_3.parquet
  ├── fileName.parquet
```

Se realiza la lectura de los ficheros con el siguiente builder:

```java
Source.File.Parquet.builder()
        .alias("alias")
        .serviceName("bts.UUAA.BATCH")
        .physicalName("files/inputs/fileName_*.parquet")
        .moveFilePath("files/processed/")
        .build()
```

El dataset resultante será la unión de los ficheros `fileName_1.parquet`, `fileName_2.parquet` y `fileName_3.parquet` mientras que el sistema de ficheros quedará de la siguiente manera:

```shell
s3://files/
    ├── inputs/
    │   ├── fileName.parquet
    ├── processed/
    │   ├── fileName_1.parquet
    │   ├── fileName_2.parquet
    │   ├── fileName_3.parquet
```

### Lectura de un directorio
Dado el siguiente sistema de ficheros con un parquet particionado:

```shell
s3://files/
    ├── inputs/
    │   ├── fileName_1.parquet/
    │   │   ├── part-00001.parquet
    │   │   ├── part-00002.parquet
    │   │   ├── part-00003.parquet
    │   │   ├── _SUCCESS
    │   ├── data.parquet
```

Si intentamos leer por `files/inputs/` Spark falla porque no es capaz de inferir el esquema de los ficheros al encontarse un árbol de ficheros. Para leer un directorio completo se debe especificar el nombre del directorio y el *wildcard* `*`:

```java
Source.File.Parquet.builder()
        .alias("alias")
        .serviceName("bts.UUAA.BATCH")
        .physicalName("files/inputs/*")
        .moveFilePath("files/processed/")
        .build()
```

Se creará un dataset los ficheros `fileName_1.parquet` y `data.parquet` y el sistema de ficheros quedará de la siguiente manera:

```shell
s3://files/
    ├── processed/
    │   ├── fileName_1.parquet/
    │   │   ├── part-00001.parquet
    │   │   ├── part-00002.parquet
    │   │   ├── part-00003.parquet
    │   │   ├── _SUCCESS
    │   ├── data.parquet
```


## Deadletter [](#deadletter)

Un deadletter es una serie de eventos que no logran entregarse de manera convencional en lo que respecta a la arquitectura [BEA](https://platform.bbva.com/bea/documentation/1ULLDbeJBpIz5DANLctgzbF_SdGArroPWsrk42e-Z2mY/01-que-es-bea), estos son almacenados en un bucket de la propia arquitectura BEA y puede ser recuperados
a través de un proceso LRBA.

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión del sistema de almacenamiento de objetos que esté usando el aplicativo.
- **physicalName**: Nombre utilizado para identificar el archivo de entrada. Depende del almacenamiento del objeto.
- **deleteFile *(OPCIONAL)***: Elimina el archivo origen del BTS. Por defecto, su valor es *false*.
- **ignoreCreatedFilesAfterExecution *(OPCIONAL)***: No procesa los ficheros creados posteriormente al arranque del *job*. Por defecto, es *false*.

### Ejemplo de código:
```java
Source.File.Parquet.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .serviceName(bea_deadletter.{UUAA}.BATCH)
        .physicalName("{id_publisher}/*.parquet")        
        .deleteFile({true|false})        
        .ignoreCreatedFilesAfterExecution({true|false})
        .build()
```
Nota: El valor por defecto al omitir la propiedad *deleteFile* e *ignoreCreatedFilesAfterExecution* es FALSE.

### Estructura ejemplo de un mensaje de deadletter:

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

## Physical name dinámicos

Los *physical names* dinámicos pueden utilizarse de tres formas distintas. 

### LRBAProperties

Esta forma es útil para usar un *physical name* guardado en la [configuración de despliegue](../../../developerexperience/03-EtherConsoleDevelopment.md) que cambiará con poca frecuencia o en función del entorno.   
Puede ser recuperado desde el contexto de ejecución, utilizando [LRBA properties](../../01-LRBAProperties.md).  

```java
@Override
public TargetsList registerTargets() {
		return TargetsList.builder()
            .add(Target.File.Parquet.builder()
            .alias({YOUR_SOURCE_ALIAS})
            .serviceName({YOUR_INVENTORY_SERVICE_NAME})
            .physicalName(lrbaProperties.getDefault("TARGET_FILE_NAME", "file-default-name.parquet"))
            .build())
		.build();
}
```

### InputParameters

Este método permite utilizar como parámetro un *physical name* que proviene del planificador y que puede cambiar en cada ejecución.

```java
@Override
public TargetsList registerTargets() {
		return TargetsList.builder()
            .add(Target.File.Parquet.builder()
            .alias({YOUR_SOURCE_ALIAS})
            .serviceName({YOUR_INVENTORY_SERVICE_NAME})
            .physicalName(InputParams.get("TARGET_FILE_NAME"))
            .build())
		.build();
}
```

### ApplicationContext

Utilizando el contexto de la aplicación, es posible establecer un *physical name* dinámico de un valor generado en un paso anterior como *Prepare Transformation* gracias al [comportamiento *lazy* del *builder*](../../../quickstart/gettingstarted/01-LRBASpark.md).  

Por ejemplo, se establece un valor en el *transform* a partir de un origen de datos en [*ApplicationContext*](../../03-LRBAApplicationContext.md).  
```java
@Override
public Map<String, Dataset<Row>>transform(Map<String, Dataset<Row>> datasetsFromRead) {
		Map<String, Dataset<Row>>datasetsToWrite = new HashMap<>();
		//transformation code . . .
		ApplicationContext.put("TARGET_FILE_NAME", datasetsFromRead.get("dataset").first().getAs("column"));
		return datasetsToWrite;
}
```

En el método *registerTargets* es posible obtener el valor del *ApplicationContext*.  
```java
@Override
public TargetsList registerTargets() {
		return TargetsList.builder()
            .add(Target.File.Parquet.builder()
            .alias({YOUR_SOURCE_ALIAS})
            .serviceName({YOUR_INVENTORY_SERVICE_NAME})
            .physicalName((String)ApplicationContext.get("TARGET_FILE_NAME"))
            .build())
		.build();
}
```

## Opciones de fichero

Con el método *addOption* puedes añadir opciones de lectura/escritura que Spark permite para diferentes formatos de archivo. Pero desde la arquitectura, hay opciones que no se pueden utilizar y otras que se han configurado con un valor por defecto diferente al de Spark.

### Opciones prohibidas

Actualmente, la única opción que está prohibida para todos los formatos de archivo es la compresión, que es una característica controlada por la arquitectura.

### Valores por defecto

Esta es una tabla con los valores por defecto que la arquitectura establece para algunas opciones.
Las opciones que no aparezcan en la tabla tendrán el valor por defecto especificado en la documentación de Spark.

#### CSV

|  Nombre de la propiedad  | Valor por defecto | 
|:------------------------:|:-----------------:|
|        delimiter         |         ,         |
|          header          |       true        |
| ignoreLeadingWhiteSpace  |       true        |
| ignoreTrailingWhiteSpace |       true        |

#### Parquet

| Nombre de la propiedad | Valor por defecto | 
|:----------------------:|:-----------------:|
|   datetimeRebaseMode   |     CORRECTED     |
|    int96RebaseMode     |     CORRECTED     |


## Repartición por columnas para escribir archivos

Con el método *repartitionColumn*, pudes definir la columna con la que se particiona y guarda el *Dataset*. 
[*Repartition*](https://spark.apache.org/docs/latest/rdd-programming-guide.html#RepartitionLink) reordena los datos basándose en la columna seleccionada para crear más o menos particiones para reagrupar los datos por cada valor individual de la columna seleccionada.
Esto significa que cada partición del *Dataset* estará compuesta por los datos con el mismo valor de la columna seleccionada.

El comportamiento del método cambiará dependiendo de si *humanReadable* está habilitado o no, y sólo si se va a habilitar la opción *humanReadable* habria que preocuparse de la configuración del *Target*.
En este caso, cuando *humanReadable* está habilitado, el *physicalName* debe contener una almohadilla (#) y el nombre de la *repartitionColumn* para diferenciar entre los ficheros que se van a guardar.

Ejemplo:

```java
@Override
public TargetsList registerTargets() {
		return TargetsList.builder()
            .add(Target.File.Csv.builder()
            .alias("myalias")
            .serviceName("bts.UUAA.BATCH")
            .physicalName("/path/file_#city.ext")
            .repartitionColumn("city")
            .humanReadable(true)
            .build())
		.build();
}
```


# connectors/02-JDBC.md
# JDBC

La arquitectura LRBA Spark permite leer y escribir *datasets* en diferentes bases de datos relacionales.

## Persistencias JDBC

### Oracle

Oracle es un servidor de base de datos desarrollado por la compañía homónima, comúnmente usado para ejecutar procesamiento de transacciones online (OLTP), *data warehousing* (DW) y un uso mixto (OLTP & DW).  
En el parámetro *serviceName* se debe usar:

```
persistenceKey = oracle
```

### DB2

DB2 es un servidor de base de datos desarrollado por IBM. Es un sistema de base de datos relacional, que está diseñado para almacenar, analizar y recuperar datos eficientemente.  
En el parámetro *serviceName* se debe usar:

```
persistenceKey = db2
```

## Tipos de Source

### Basic

El *builder* de tipo *JDBC Basic* puede ser usado para recuperar datos de una base de datos relacional sin especificar ninguna configuración.

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Parámetro que usa la arquitectura para identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo alias, no es el nombre real de la tabla.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.
  
Código de ejemplo:
```java
Source.Jdbc.Basic.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql({YOUR_SQL})
    .addOption({{KEY}},{{VALUE}})
    .build();
```

### Native query

El builder de tipo *JDBC NativeQuery* permite escribir sentencias SQL que serán enviadas directamente a la base de datos.

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**:  Parámetro que usa la arquitectura para identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`
- **sql**: Sentencia SQL utilizando la sintaxis de la base de datos. En este caso, se utiliza el nombre real de la tabla a consultar y no el indicado en el campo alias.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Source.Jdbc.NativeQuery.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .sql({YOUR_SQL})
    .addOption({{KEY}},{{VALUE}})
    .build();
```

### Partitioned

El builder de tipo *JDBC Partitioned* permite indicar la cantidad de particiones que Spark usará y como debe realizar esas particiones.

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **serviceName**:  Parámetro que usa la arquitectura para identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos. Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo alias, no es el nombre real de la tabla.
- **column**: El nombre de la columna usada para generar las particiones. Debe ser una columna de tipo numérico o fecha.
- **lowerBound**: Debe ser similar al valor mínimo esperado para la columna de particionado en la tabla dada.
- **upperBound**: Debe ser similar al valor máximo esperado para la columna de particionado en la tabla dada.
- **numPartitions**: El número máximo de particiones que se pueden usar para el paralelismo en la lectura de la tabla. Esto también determina el número máximo de conexiones JDBC concurrentes.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Source.Jdbc.Partitioned.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql({YOUR_SQL}) 
    .column({PARTITION_COLUMN})
    .lowerBound({LOWER_BOUND_VALUE})
    .upperBound({UPPER_BOUND_VALUE})
    .numPartitions({NUM_PARTITON})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

Ejemplo de un caso particular con lo valores *lowerBound = 0, upperBound = 45000000 y numPartitions = 4*:
```java
Source.Jdbc.Partitioned.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql("SELECT * FROM ALIAS") 
    .column("COLUNM")
    .lowerBound(0)
    .upperBound(45000000)
    .numPartitions(4)
    .build()
```

La base de datos recibirá las siguientes consultas:
``` sql
SELECT * FROM TABLE WHERE COLUMN < 11250000
SELECT * FROM TABLE WHERE COLUMN >= 11250000 AND COLUMN < 22500000
SELECT * FROM TABLE WHERE COLUMN >= 22500000 AND COLUMN < 33750000
SELECT * FROM TABLE WHERE COLUMN >= 33750000
```

Ejemplo de particionado por una columna de tipo fecha:
```java
Source.Jdbc.Partitioned.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql("SELECT * FROM ALIAS") 
    .column("DATE_COLUNM")
    .lowerBound(LocalDate.of(2017, 10, 1))
    .upperBound(LocalDate.of(2022, 10, 31))
    .numPartitions(4)
    .build()
```

## Tipos de Target

### Insert

Este tipo de target inserta o ignora los datos, dependiendo de si la clave primaria del registro existe o no.  
Esta operación está implementada únicamente para Oracle. 

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`.
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **bulkSize *(OPCIONAL)***: Establece el tamaño de *bulk*. Debe estar en un rango entre 10 y 10000. Por defecto, es 4096.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Target.Jdbc.Insert.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .bulkSize({BULK_SIZE})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

### Update

Este tipo de target actualiza los datos con la clave primaria del registro.  
Esta operación está implementada únicamente para Oracle.

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`.
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **bulkSize *(OPCIONAL)***: Establece el tamaño de *bulk*. Debe estar en un rango entre 10 y 10000. Por defecto, es 4096.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Target.Jdbc.Update.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .bulkSize({BULK_SIZE})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

### Upsert

Este tipo de *target* inserta o actualiza los datos, dependiendo de si la clave primaria del registro existe o no.  
Esta operación está implementada únicamente para Oracle.

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**:  Parámetro que usa la arquitectura para identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **bulkSize *(OPCIONAL)***: Establece el tamaño de *bulk*. Debe estar en un rango entre 10 y 10000. Por defecto, es 4096.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Target.Jdbc.Upsert.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .bulkSize({BULK_SIZE})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

### Delete

Este *target* elimina datos de la base de datos. La arquitectura construye la sentencia de *DELETE* usando todas las columnas que contiene el *dataset* que se le indica.

Parameters:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**:  Parámetro que usa la arquitectura para identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`
- **physicalName**: Tabla con esquema. *{SCHEMA.TABLE}*
- **bulkSize *(OPCIONAL)***: Establece el tamaño de *bulk*. Debe estar en un rango entre 10 y 10000. Por defecto, es 4096.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de Ejemplo:
```java
Target.Jdbc.Delete.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .bulkSize({BULK_SIZE})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

### Transactional

Este tipo de target se utilizará para ejecutar multiples querys contra múltiples tablas en el mismo contexto transaccional de la BBDD (misma unidad de commit).
Es importante que se utilice de forma **idempotente**, ya que debido al comportamiento de Spark no se garantiza que no se repitan tareas.

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato es: `{persistenceKey}.{UUAA}.BATCH`.
- **jdbcTransactionWriter**: Implementación propia de la clase abstracta `JdbcTransactionWriterHandler`.
- **addOption *(OPCIONAL)***: Añadir opción de las [configuraciones de Spark JDBC](https://spark.apache.org/docs/3.5.1/sql-data-sources-jdbc.html) o configuraciones propias del driver utilizado.

Código de ejemplo:
```java
Target.Jdbc.Transactional.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_INVENTORY_SERVICE_NAME})
    .jdbcTransactionWriter({JDBC_WRITER_CLASS})
    .addOption({{KEY}},{{VALUE}})
    .build()
```

#### Implementar la clase `JdbcTransactionWriterHandler`

El desarrollador debe implementar una clase que extienda de `JdbcTransactionWriterHandler` para poder realizar las *querys* contra la base de datos.
Esta clase debe implementar el método `write`.
Se ejecutará por cada uno de los registros del Dataset y su información vendrá en el parámetro de entrada `row` que será un `Map<String, Object>` con el nombre de las columnas como clave y el valor correspondiente como valor.
Por si fuera necesario, el parámetro `structType` contiene la estructura del *dataset* que se está procesando.

Para facilitar el trabajo del desarrollador, LRBA provee del método `createPreparedStatement` que recibe la query por parámetro y que se encargará de
gestionar la conexión con la base de datos, devolviendo un `PrearedStatement` para que se establezcan los parámetros necesarios y el desarrollador pueda ejecutar la query.

Es importante tener en cuenta que todo lo que se codifique en esta clase tiene que ser serializable, ya que se va a ejecutar en un *job* de Spark con ejecutores.
Aunque esto ya se valida en runtime y saldrá un error si no es así, es importante tenerlo en cuenta por si en pruebas locales funciona y en el cluster no.

Código de ejemplo:
```java
public class JdbcTransactional extends JdbcTransactionWriterHandler {

    @Override
    public void write(Map<String, Object> row, StructType structType) {
    
    }
}
```

## Sequence

Se habilita el uso de secuencias; sin embargo, tiene algunas limitantes y condiciones. A continuación se abordan las premisas y las Bases de Datos que ya implementan el uso de sequence. 

### Base de Datos que implementan Sequence
- Oracle

#### Premisas

- Tener declarado el campo secuencia en la BD.
- El campo secuencia debe ser numérico.
- La funcionalidad trabaja con tres insumos "column, sequenceName y useSequenceInUpdate".
- Se pueden usar 'n' secuencias.
- Solo está disponible para insert, upsert y update.
- **Insert**
	- El dataset no debe contener la(s) columna(s) secuencia.
- **Upsert**
	- La secuencia no puede formar parte de la clave primaria.
	- El uso de secuencias es opcional al realizar el update (useSequenceInUpdate), permitiendo elegir si usar el valor de la secuencia o el de la columna.
- **Update**
	- La secuencia no puede formar parte de la clave primaria.


#### Parámetros:

- **column**: columna donde se almacenará la secuencia.
- **sequenceName**: nombre de la secuencia.
- **useSequenceInUpdate**: valor booleano para definir si se utilizara la secuencia o el valor de **column**; solo para Upsert.

Código de ejemplo (insert):
```java
Target.Jdbc.Insert.builder()
	.alias({YOUR_SOURCE_ALIAS})
	.serviceName({YOUR_INVENTORY_SERVICE_NAME})
	.physicalName({YOUR_PHYSICAL_NAME})
	.addSequence({YOUR_COLUMN},{YOUR_SEQUENCE_NAME})
	.build()
```

Código de ejemplo (upsert):
```java
Target.Jdbc.Upsert.builder()
	.alias({YOUR_SOURCE_ALIAS})
	.serviceName({YOUR_INVENTORY_SERVICE_NAME})
	.physicalName({YOUR_PHYSICAL_NAME})
	.addSequence({YOUR_COLUMN},{YOUR_SEQUENCE_NAME},{YOUR_BOOLEAN_PARAM_FOR_SEQUENCE_USE})
	.build()
```
Código de ejemplo (update):
```java
Target.Jdbc.Update.builder()
	.alias({YOUR_SOURCE_ALIAS})
	.serviceName({YOUR_INVENTORY_SERVICE_NAME})
	.physicalName({YOUR_PHYSICAL_NAME})
	.addSequence({YOUR_COLUMN},{YOUR_SEQUENCE_NAME})
	.build()
```




# connectors/03-MongoDB.md
# MongoDB

**MongoDB** es un sistema de gestión de bases de datos de código abierto y **no relacional** que utiliza documentos flexibles en lugar de tablas y filas para procesar y almacenar diversas formas de datos. Como solución NoSQL, MongoDB proporciona un modelo de almacenamiento de datos flexible que permite a los usuarios almacenar y consultar diferentes tipos de datos con facilidad.

## Tipos de Source

Este *builder*, al igual que el de JDBC, también admite el particionado. También se pueden indicar la clave y el tamaño. Además, el desarrollador puede indicar la preferencia de lectura (si desea ir contra los nodos maestros o secundarios en el conjunto de réplicas).

Cuando se utiliza Spark para procesar datos en MongoDB, se utiliza el particionado de MongoDB para dividir la colección de datos en fragmentos y distribuir esos fragmentos en diferentes servidores o máquinas. Esto permite que Spark procese los datos de manera más eficiente y en paralelo, ya que cada fragmento se procesa por separado y los resultados se combinan al final.

Existen diferentes formas de controlar el número de particiones o fragmentos utilizados para procesar los datos con Spark y MongoDB. Es importante tener en cuenta que el particionado de MongoDB no es el único factor que afecta el rendimiento y la escalabilidad al utilizar Spark con MongoDB. También se deben considerar otros factores, como el tamaño de los fragmentos, la distribución de los datos dentro de los fragmentos y la configuración del clúster de Spark. Ajustando adecuadamente estos factores, se puede lograr un rendimiento óptimo al procesar grandes cantidades de datos con Spark y MongoDB.

Soporta **diferentes tipos de particionado**, los cuales se pueden utilizar para cambiar el tamaño de documento predeterminado, el muestreo o el número de particiones.

### Partitioner por defecto

Utiliza el tamaño medio del documento y el muestreo aleatorio de la colección para determinar particiones adecuadas para la colección.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos.  
  Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo "alias", no es el nombre real de la tabla.
- **readPreference *(OPCIONAL)***: La [preferencia de lectura](https://docs.mongodb.com/manual/core/read-preference/#replica-set-read-preference-modes) a utilizar. Por defecto, "secondaryPreferred".
- **sampleSize *(OPCIONAL)***: Número de documentos que utiliza Spark para inferir el esquema. Por defecto, 1000.
- **schema *(OPCIONAL)***: Permite proporcionar un Bean o un StructType indicando el esquema a leer.

Código de ejemplo:
```java
Source.Mongo.DefaultPartitioner.builder()
      .alias({YOUR_SOURCE_ALIAS})
      .serviceName({YOUR_SERVICE_NAME})
      .physicalName({YOUR_PHYSICAL_NAME})
      .sql({YOUR_SQL})
      .readPreference({READ_PREFERENCE})
      .sampleSize({SAMPLE_SIZE})
      .build()
```
    
### Sample Partitioner

Permite configurar el particionado.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos.
Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo "alias", no es el nombre real de la tabla.
- **readPreference *(OPCIONAL)***: La [preferencia de lectura](https://docs.mongodb.com/manual/core/read-preference/#replica-set-read-preference-modes) a utilizar. Por defecto, "secondaryPreferred".
- **sampleSize *(OPCIONAL)***: Número de documentos que utiliza Spark para inferir el esquema. Por defecto, 1000.
- **partitionKey *(OPCIONAL)***: El campo por el que se van a particionar los datos. Tiene que estar indexado y contener valores únicos. Por defecto, "_id".
- **partitionSizeMB *(OPCIONAL)***: El tamaño (en MB) para cada partición. Por defecto, 64.
- **samplesPerPartition *(OPCIONAL)***: El número de documentos para cada partición. Por defecto, 10.
- **schema *(OPCIONAL)***: Permite proporcionar un Bean o un StructType indicando el esquema a leer.

Código de ejemplo:
```java
Source.Mongo.SamplePartitioner.builder()
      .alias({YOUR_SOURCE_ALIAS})
      .serviceName({YOUR_SERVICE_NAME})
      .physicalName({YOUR_PHYSICAL_NAME})
      .sql({YOUR_SQL})
      .readPreference({READ_PREFERENCE})
      .sampleSize({SAMPLE_SIZE})
      .partitionKey({PARTITION_KEY})
      .partitionSizeMB({PARTITION_SIZE_MB})
      .samplesPerPartition({SAMPLES_PER_PARTITION})
      .build()
```

### Sharded Partitioner

MongoDB usa el [shard key](https://docs.mongodb.com/manual/core/sharding-shard-key/) para distribuir los documentos de la colección entre los shards. Solo funciona con clusters/colecciones fragmentados.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos.
Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo "alias", no es el nombre real de la tabla.
- **readPreference *(OPCIONAL)***: La [preferencia de lectura](https://docs.mongodb.com/manual/core/read-preference/#replica-set-read-preference-modes) a utilizar. Por defecto, "secondaryPreferred".
- **sampleSize *(OPCIONAL)***: Número de documentos que utiliza Spark para inferir el esquema. Por defecto, 1000.
- **shardKey *(OPCIONAL)***: El campo utilizado para dividir la colección. Tiene que estar indexado y contener valores únicos. Por defecto, "\_id". **Deprecado** para la versión del conector 10.1.1. Si utiliza la versión del conector 3.0.2 debe seguir usando este campo.
- **schema *(OPCIONAL)***: Permite proporcionar un Bean o un StructType indicando el esquema a leer.

Código de ejemplo:
```java
Source.Mongo.ShardedPartitioner.builder()
      .alias({YOUR_SOURCE_ALIAS})
      .serviceName({YOUR_SERVICE_NAME})
      .physicalName({YOUR_PHYSICAL_NAME})
      .sql({YOUR_SQL})
      .readPreference({READ_PREFERENCE})
      .sampleSize({SAMPLE_SIZE})
      .shardKey({SHARD_KEY})
      .build()
```

### Single Partition Partitioner

Se utiliza para crear una única partición.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos.
  Recuerda que el nombre de la tabla a consultar es el mismo que se indica en el campo "alias", no es el nombre real de la tabla.
- **readPreference *(OPCIONAL)***: La [preferencia de lectura](https://docs.mongodb.com/manual/core/read-preference/#replica-set-read-preference-modes) a utilizar. Por defecto, "secondaryPreferred".
- **sampleSize *(OPCIONAL)***: Número de documentos que utiliza Spark para inferir el esquema. Por defecto, 1000.
- **schema *(OPCIONAL)***: Permite proporcionar un Bean o un StructType indicando el esquema a leer.

Código de ejemplo:
```java
Source.Mongo.SinglePartitionPartitioner.builder()
      .alias({YOUR_SOURCE_ALIAS})
      .serviceName({YOUR_SERVICE_NAME})
      .physicalName({YOUR_PHYSICAL_NAME})
      .sql({YOUR_SQL})
      .readPreference({READ_PREFERENCE})
      .sampleSize({SAMPLE_SIZE})
      .build()
```

### Inferencia del esquema

Como MongoDB no tiene esquema, cuando se leen datos, MongoDB obtiene el esquema a través de una muestra aleatoria de datos. En esa muestra, se leen todos los datos y se asignan los tipos a las etiquetas en función de los datos encontrados. Por ejemplo, si todos los datos encontrados para un campo son de tipo string, se asignará ese tipo en el esquema.

Por ejemplo, puede ocurrir que en algún campo todos los datos que se estén tomando sean nulos y se asigne el valor Null, provocando errores cuando se reciban otro tipo de datos durante la ejecución. Existen dos soluciones para este comportamiento:
- La primera es indicar a través del constructor que utilice una muestra de datos mayor `sampleSize({SAMPLE_SIZE})`.
- La segunda, también a través del constructor, estableciendo el esquema `schema({SCHEMA})` para que no lo tenga que inferir.

## Operaciones Target

Si el desarrollador quiere escribir una colección tiene varias formas de hacerlo:

### Upsert

Inserta o actualiza datos si ya existe la clave primaria.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **addQueryKey *(OPCIONAL)***: Campo del *dataset* que se utiliza como índice ID. Si no se indica, se usa el `_id` como filtro de las operaciones. Si el filtro indicado mediante este método no es único, la operación *Upsert* podría provocar un comportamiento inesperado, ya que actualiza la primera fila encontrada.
- **bulkSize *(OPCIONAL)***: Se utiliza para establecer el tamaño de "bulk" en la operación upsert, debe estar en un rango entre 10 y 10000. Por defecto, 4096.
- **replaceDocument *(OPCIONAL)***: El documento se puede reemplazar o no. Por defecto, true.

**IMPORTANTE**: Si la colección de MongoDB está fragmentada, todos los campos que forman parte de la shardKey deben añadirse utilizando el método constructor `addQueryKey()`.
Además, se pueden indicar más campos si la shardKey no es una clave única.
Si no se indican los campos que forman parte de la shardKey, se producirá el siguiente error: *Failed to target upsert by query :: could not extract exact shard key*.

Código de ejemplo:
```java
Target.Mongo.Upsert.builder()
            .alias({YOUR_TARGET_ALIAS})
            .serviceName({YOUR_SERVICE_NAME})
            .physicalName({YOUR_COLLECTION_NAME})
            .addQueryKey({PRIMARY_KEY_FIELD})
            .bulkSize({BULK_SIZE})
            .replaceDocument({REPLACE_DOCUMENT})
            .build()
```

#### Ejemplo Shardkey 

Es necesario invocar el método `addQueryKey` una vez por cada campo de filtro (que debe incluir la shardKey).

Ejemplos:

Shardkey: `(uniqueField)`.
```java
Target.Mongo.Upsert.builder()
            .alias({YOUR_TARGET_ALIAS})
            .serviceName({YOUR_SERVICE_NAME})
            .physicalName({YOUR_COLLECTION_NAME})
            .addQueryKey("uniqueField")
            .bulkSize({BULK_SIZE})
            .build()
```

Shardkey: `(field1,field2)` ninguno es clave única. Por eso es necesario especificar campos adicionales. Como resultado, el filtro aplicado formado por todos los campos indicados mediante el método constructor `addQueryKey()` son una clave única. En la mayoría de los casos, `_id` es suficiente para que el filtro sea una clave única.
```java
Target.Mongo.Upsert.builder()
            .alias({YOUR_TARGET_ALIAS})
            .serviceName({YOUR_SERVICE_NAME})
            .physicalName({YOUR_COLLECTION_NAME})
            .addQueryKey("field1")
            .addQueryKey("field2")
            .addQueryKey("uniqueField")
            .bulkSize({BULK_SIZE})
            .build()
```

### Delete

Borrar datos en base a los documentos indicados.

Parámetros:
- **alias**: Nombre usado en la clase "Transformer" para recuperar el *Dataset* del mapa de entrada.
- **serviceName**: Se usa para que la arquitectura pueda identificar los datos de conexión de la base de datos aplicativa. El formato será: *mongodb.{BD_SIN_PAIS}.BATCH*. Ejemplo: *mongodb.BMG_UUAA_XXX.BATCH*.
- **physicalName**: Nombre de la colección.
- **bulkSize *(OPCIONAL)***: Se utiliza para establecer el tamaño "bulk" en la operación de borrado, debe estar en un rango entre 10 y 10000. Por defecto, 4096.
  
Código de ejemplo:
```java
Target.Mongo.Delete.builder()
            .alias({YOUR_TARGET_ALIAS})
            .serviceName({YOUR_SERVICE_NAME})
            .physicalName({YOUR_INDEX_NAME})
            .bulkSize({BULK_SIZE})
            .build()
```

# Guía de migración a la nueva versión del conector de MongoDB

Con la nueva versión del conector de MongoDB han tomado la decisión de no mapear datos que no sean nativos de java/spark a estructuras de datos.  
En lugar de ello, devuelven ciertos datos en un formato llamado [extended json](https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/). 
Llegando en la columna un *String* con ese json.  
Desde la arquitectura se ha estado revisando el tratamiento de estos datos y cuales son las diferencias que existen para leer/escribir.
Esto se produce principalmente con tres tipos de datos que si se usan habrá que realizar alguna modificación en el job.  
En todas las propuestas de transformación que se realicen, se incluirá el ejemplo de qué cambios habría que realizar sobre una fila o un campo. 
Este ejemplo se debe combinar con una función map o con lo que el usuario considere, para transformar el modelo de entrada al que 
se esté utilizando o el que se esté utilizando al de salida, según las necesidades de ese proceso concreto.

## ObjectId

### Version 3.0.2

Con la versión 3.0.2 del conector, tanto si se infiere el esquema, como si se fija al leer/escribir, el conector usa la siguiente estructura para trabajar con él:
```java
DataTypes.createStructField("_id", new StructType().add("oid",DataTypes.StringType, true), true)
```
### Versión 10.1.1

Con la versión 10.1.1, sin embargo, el esquema con el que mapea un **ObjectId** es:
```java
DataTypes.StringType
```
Siendo el contenido de ese *String* el siguiente:
```json
{ "$oid": "64a692bfe0487733869dea39" }
```

### Cambios a realizar

#### Lectura

Con apoyo de la librería **Gson** se puede obtener el valor del **ObjectId**:
```java
Map<String, String> objectId = gson.fromJson((String) row.getAs("_id"), new TypeToken<Map<String, String>>() {}.getType());
String oid = objectId.get("$oid");
```

#### Escritura

Normalmente, no es necesario escribir un **ObjectId**, ya que si no se indica campo "_id", la base de datos genera uno automáticamente.
En caso de que se quiera realizar una actualización sobre ciertos campos o eliminar ciertos documentos en base al "_id", 
es importante que en la columna "_id" vaya un *String* con un json en el formato que se ha indicado anteriormente.   

Se puede componer de dos formas, realizando una concatenación de *String* manualmente:
```java
String _id = "{\"$oid\": \"" + oid + "\"}";
```
O con apoyo de la librería **Gson**:
```java
Map<String, String> auxId = new HashMap<>();
auxId.put("$oid", oid);
String _id = gson.toJson(auxId);
```

## Timestamp

En MongoDB existen para manejar fechas los tipos bson **Date/ISODate** y **Timestamp**.  
En la mayoría de los casos se usa y se recomienda el tipo **Date**, por lo que va a ser muy raro encontrarse en una situación en la que se esté usando el tipo bson **Timestamp**.  
Aun así, se dejarán indicadas las diferencias y cambios a acometer.

### Version 3.0.2

Con la versión 3.0.2 del conector, tanto si se infiere el esquema, como si se fija al leer/escribir, el conector usa la siguiente estructura para trabajar con él:
```java
new StructType().add("time", DataTypes.IntegerType, true).add("inc", DataTypes.IntegerType, true), true)
```
### Versión 10.1.1

Con la versión 10.1.1 hay dos formas de leer un **Timestamp**.  
Si no se necesita la parte del incremental del **Timestamp** se puede inferir el esquema o forzarlo a un *java.sql.Timestamp*.  
Este formato también es al que se mapea un **Date**.
```java
DataTypes.TimestampType
```

Si se va a hacer uso del incremental, es necesario forzar el esquema a *String*:
```java
DataTypes.StringType
```
Siendo el contenido de ese *String* el siguiente:
```json
{ "$timestamp": { "t": 1687960502, "i": 1 } }
```
### Cambios a realizar

#### Lectura

Con apoyo de la librería **Gson** se puede obtener el valor del **Timestamp**:
```java
Map<String, Map<String, Integer>> timestamp = new Gson().fromJson(timestampFiled, new TypeToken<Map<String, Map<String, Integer>>>() {}.getType());
int time = timestamp.get("$timestamp").get("t");
int inc = timestamp.get("$timestamp").get("i");
```

#### Escritura

Para escribir un **Timestamp**, se puede componer de dos formas, realizando una concatenación de *String* manualmente:
```java
String timestamp = "{\"$timestamp\": {\"t\": " + time + ", \"i\": " + inc + "}}";
```
O con apoyo de la librería **Gson**:
```java
Map<String, Map<String, Integer>> auxTimestamp = new HashMap<>();
auxTimestamp.put("$timestamp", new HashMap<>());
auxTimestamp.get("$timestamp").put("t", time);
auxTimestamp.get("$timestamp").put("i", inc);
String timestamp = new Gson().toJson(auxTimestamp);
```

## Expresiones Regulares

En los tipos bson de MongoDB, existe uno que se usa para guardar expresiones regulares.  
Nuevamente, es un tipo el cual es raro su uso, pero aun así, se dejarán indicadas las diferencias y cambios a acometer.

### Version 3.0.2

Con la versión 3.0.2 del conector, tanto si se infiere el esquema, como si se fija al leer/escribir, el conector usa la siguiente estructura para trabajar con él:
```java
new StructType().add("regex", DataTypes.StringType, true).add("options", DataTypes.StringType, true), true)
```
### Versión 10.1.1

Con la versión 10.1.1, sin embargo, el esquema con el que mapea es:
```java
DataTypes.StringType
```
Siendo el contenido de ese *String* el siguiente:
```json
{ "$regularExpression": { "pattern": "tu{4}a", "options": "i" } }
```

### Cambios a realizar

#### Lectura

Con apoyo de la librería **Gson** se puede obtener el valor del tipo **Regex**:
```java
Map<String, Map<String, String>> regex = new Gson().fromJson(regexField, new TypeToken<Map<String, Map<String, String>>>() {}.getType());
String pattern = regex.get("$regularExpression").get("pattern");
String options = regex.get("$regularExpression").get("options");
```

#### Escritura

Para escribir un tipo **Regex**, se puede componer de dos formas, realizando una concatenación de *String* manualmente:
```java
String regex = "{\"$regularExpression\": {\"pattern\": \"" + pattern + "\", \"options\": \"" + options + "\"}}";
```
O con apoyo de la librería **Gson**:
```java
Map<String, Map<String, String>> auxRegex = new HashMap<>();
auxRegex.put("$regularExpression", new HashMap<>());
auxRegex.get("$regularExpression").put("pattern", pattern);
auxRegex.get("$regularExpression").put("options", options);
String regex = new Gson().toJson(auxRegex);
```




# connectors/04-Elastic.md
# Elasticsearch

**Elasticsearch** es un motor de búsqueda y análisis distribuido basado en NoSQL, gratuito y de código abierto,
diseñado para todo tipo de datos, incluyendo datos textuales, numéricos, geoespaciales, estructurados y no
estructurados.

LRBA permite **leer** y **escribir** *datasets* en **Elasticsearch**.

## Tipos de *Source*

### Basic

La arquitectura LRBA Spark permite leer de **cualquier índice Elastic**.

Parámetros:

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *dataset* del mapa de entrada.
- **serviceName**: Expresión utilizada para recuperar la información de la base de datos a conectar. El formato es:
  *elastic.{UUAA}.BATCH*.
- **physicalName**: Índice/Documento de Elastic.
- **sql *(OPCIONAL)***: Sentencia SQL para filtrar datos en la lectura. Por defecto, recupera todos los datos.  
  Recuerda que el nombre del índice a consultar es el indicado en el campo *alias*, no es el nombre real del índice.
- **retrieveMetadata *(OPCIONAL)***: Especifica si se quieren recuperar los metadatos de un documento de
  Elastic. (`_id`, `_type`, `_index`, ...) bajo el campo `_metadata`. Por defecto, false, no se recuperan.
- **routingField *(OPCIONAL)***: Especifica el *RoutingField* del documento. Rellenarlo mejora el rendimiento de la
  operación. Más información puede encontrarse
  en: [Routing Field](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-routing-field.html). Por
  defecto, no se utiliza ningún campo.
- **shardPreference *(OPCIONAL)***: Especifica si se consultan datos en un nodo específico de Elastic. Más información
  puede encontrarse
  en: [Search Shard Routing Preference](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-shard-routing.html#shard-and-node-preference).
  Por defecto, las consultas no se dirigen a nodos específicos.
- **addElasticFieldAsArray *(OPCIONAL)***: El campo indicado mediante esta propiedad se trata como array. Solo aplica a
  campos de tipo *keyword*.
- **docsPerPartition *(OPCIONAL)***: El número de documentos para cada partición. Por defecto, este valor no está
  establecido y las particiones de entrada se calculan en función del número de fragmentos en los que esten divididos
  los indices que se leen.
- **useRichDateObject *(OPCIONAL)***: Especifica si se quiere crear *RichDateObjects* para campos de tipo fecha o si se
  quiere que estos sean tratados como tipos primitivos. Por defecto, true. **Si se pone esta propiedad a `false`, todas
  las fechas serán tratadas como tipo String o long**. Más información sobre esto puede encontrarse
  en: [Mapping Date Rich](https://www.elastic.co/guide/en/elasticsearch/hadoop/8.6/configuration.html#cfg-field-info)
- **addCustomElasticHadoopConfig *(OPCIONAL)***: Añadir opción
  de [Opciones de configuración de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html).
  Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de
  configuración" al final de este documento.

Código de ejemplo:

```java
Source.Elastic.Basic.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_INDEX_NAME})
    .sql({YOUR_SQL})
    .retrieveMetadata({RETRIEVE_METADATA})
    .routingField({ROUTING_FIELD})
    .shardPreference({SHARD_PREFERENCE})
    .addElasticFieldAsArray({ARRAY_FIELD_NAME})
    .docsPerPartition({docsPerPartition})
    .addCustomElasticHadoopConfig({{KEY}},{{VALUE}})
    .build()
```

## Tipos de *Target*

### Truncate

Esta operación, **trunca el contenido** del índice indicado, **reemplazándolo con el contenido del *dataset* de entrada
**
Si el índice tiene muchos documentos, el proceso puede ser lento.

Parámetros:

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *dataset* del mapa de entrada.
- **serviceName**: Expresión utilizada para recuperar la información de la base de datos a conectar. El formato es:
  *elastic.{UUAA}.BATCH*.
- **physicalName**: Índice/Documento de Elastic.
- **pkField *(OPCIONAL)***: Especifica el campo utilizado como ID. Si no se indica, el `_id` es el autogenerado por
  Elastic. Por defecto, ningún campo es usado como PK.
- **routingField *(OPCIONAL)***: Especifica el *RoutingField* del documento. Rellenarlo mejora el rendimiento de la
  operación. Más información puede encontrarse
  en: [Routing Field](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-routing-field.html). Por
  defecto, no se utiliza ningún campo.
- **bulkSize *(OPCIONAL)***: Especifica el *bulkSize* en una operación de truncado, debe de estar dentro del rango 10 - 10000. Por defecto, 4096.
- **bulkSizeMB *(OPCIONAL)***: Especifica el tamaño de bulk en *mb*. Por defecto, 4mb.
- **addCustomElasticHadoopConfig *(OPCIONAL)***: Añadir opción
  de [Opciones de configuración de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html).
  Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de
  configuración" al final de este documento.

Código de ejemplo:

```java
Target.Elastic.Truncate.builder()
    .alias({YOUR_TARGET_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_INDEX_NAME})
    .pkField({PRIMARY_KEY_FIELD})
    .routingField({ROUTING_FIELD})
    .bulkSize({BULK_SIZE})
    .bulkSizeMB({BULK_SIZE_MB})
    .addCustomElasticHadoopConfig({{KEY}},{{VALUE}})
    .build()
```

### Upsert

Esta operación, **crea o actualiza** datos dependiendo de si `_id` existe o no.
Sin embargo, este comportamiento puede ser configurado de diferentes formas.
Si en el builder *Upsert* no se especifica `pkField`, entonces los datos serán insertados y el `_id` será autogenerado
por Elastic.
Si por contra, se especifica `pkField`, los documentos existentes se actualizarán con los nuevos datos que vengan en el
*dataset* de entrada.
Los campos que no vengan informados en el *dataset* no se modificaran. Si los documentos tienen que ser completamente
reemplazados, el campo `replaceDocument` debe ser indicado.

Parámetros:

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *dataset* del mapa de entrada.
- **serviceName**: Expresión utilizada para recuperar la información de la base de datos a conectar. El formato es:
  *elastic.{UUAA}.BATCH*.
- **physicalName**: Índice/Documento de Elastic.
- **pkField *(OPCIONAL)***: Especifica el campo utilizado como ID. Si no se indica, el `_id` es autogenerado por
  Elastic. Por defecto, ningún campo es usado como PK.
- **routingField *(OPCIONAL)***: Especifica el *RoutingField* del documento. Rellenarlo mejora el rendimiento de la
  operación. Más información puede encontrarse
  en: [Routing Field](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-routing-field.html). Por
  defecto, no se utiliza ningún campo.
- **replaceDocument *(OPCIONAL)***: Especifica si el documento debe ser completamente reemplazado o no. Por defecto, false.
- **bulkSize *(OPCIONAL)***: Especifica el *bulkSize* en una operación de truncado, debe de estar dentro del rango 10 - 10000. Por defecto, 4096.
- **bulkSizeMB *(OPCIONAL)***: Especifica el tamaño de bulk en *mb*. Por defecto, 4mb.
- **addCustomElasticHadoopConfig *(OPCIONAL)***: Añadir opción
  de [Opciones de configuración de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html).
  Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de
  configuración" al final de este documento.

Código de ejemplo:

```java
Target.Elastic.Upsert.builder()
    .alias({YOUR_TARGET_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_INDEX_NAME})
    .pkField({ PRIMARY_KEY_FIELD})
    .routingField({ROUTING_FIELD})
    .replaceDocument({REPLACE_DOCUMENT})
    .bulkSize({BULK_SIZE})
    .bulkSizeMB({BULK_SIZE_MB})
    .addCustomElasticHadoopConfig({{KEY}},{{VALUE}})
    .build()
```

### Delete

Esta operación, borra datos de un índice Elastic.

Parámetros:

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *dataset* del mapa de entrada.
- **serviceName**: Expresión utilizada para recuperar la información de la base de datos a conectar. El formato es:
  *elastic.{UUAA}.BATCH*.
- **physicalName**: Índice/Documento de Elastic.
- **pkField *(OPCIONAL)***: Especifica el campo utilizado como ID. Si no se indica, el *dataset* a borrar solo debe
  contener una única columna que será tratada como el `_id`
- **routingField *(OPCIONAL)***: Especifica el *RoutingField* del documento. Rellenarlo mejora el rendimiento de la
  operación. Más información puede encontrarse
  en: [Routing Field](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-routing-field.html). Por
  defecto, no se utiliza ningún campo.
- **bulkSize *(OPCIONAL)***: Especifica el *bulkSize* en una operación de truncado, debe de estar dentro del rango 10 - 10000. Por defecto, 4096.
- **bulkSizeMB *(OPCIONAL)***: Especifica el tamaño de bulk en *mb*. Por defecto, 4mb.
- **addCustomElasticHadoopConfig *(OPCIONAL)***: Añadir opción
  de [Opciones de configuración de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html).
  Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de
  configuración" al final de este documento.

Código de ejemplo:

```java
Target.Elastic.Delete.builder()
    .alias({YOUR_TARGET_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_INDEX_NAME})
    .pkField({PK_FIELD})
    .routingField({ROUTING_FIELD})
    .bulkSize({BULK_SIZE})
    .bulkSizeMB({BULK_SIZE_MB})
    .addCustomElasticHadoopConfig({{KEY}},{{VALUE}})
    .build()
```

### Update

Esta operación actualiza registros en un índice de Elastic. 
Este conector permite guardar los errores en un índice especificando el nombre del índice a través de la propiedad de Elastic con `es.write.rest.error.handler.es.client.resource` 
siendo necesario añadir el valor `es` en la propiedad `es.write.rest.error.handlers` a través del atributo `addCustomElasticHadoopConfig`especificado más abajo. Quedando de la siguiente manera:

```java
Target.Elastic.Update.builder()
.alias("targetAlias")
.serviceName(serviceName)
.physicalName(elasticIndexName)
.pkField("uuid")
.addCustomElasticHadoopConfig("es.write.rest.error.handlers", "es")
.addCustomElasticHadoopConfig("es.write.rest.error.handler.es.client.resource", "i_error_index")
.build()
```

Se puede encontrar más información sobre las opciones de configuración en el tratamiento de errores en Elastic en el siguiente enlace: 
[Opciones de configuración de Error Handler de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/errorhandlers.html)


Parámetros:

- **alias**: Nombre usado en la clase *Transformer* para recuperar el *dataset* del mapa de entrada.
- **serviceName**: Expresión utilizada para recuperar la información de la base de datos a conectar. El formato es:
  *elastic.{UUAA}.BATCH*.
- **physicalName**: Índice/Documento de Elastic.
- **pkField *(OBLIGATORIO)***: Especifica el campo utilizado como ID.
- **routingField *(OPCIONAL)***: Especifica el *RoutingField* del documento. Rellenarlo mejora el rendimiento de la
  operación. Más información puede encontrarse
  en: [Routing Field](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-routing-field.html). Por
  defecto, no se utiliza ningún campo.
- **bulkSize *(OPCIONAL)***: Especifica el *bulkSize* en una operación de truncado, debe de estar dentro del rango 10 - 10000. Por defecto, 4096.
- **bulkSizeMB *(OPCIONAL)***: Especifica el tamaño de bulk en *mb*. Por defecto, 4mb.
- **addCustomElasticHadoopConfig *(OPCIONAL)***: Añadir opción
  de [Opciones de configuración de Elastic](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/configuration.html).
  Consulte los valores por defecto de la arquitectura y las opciones prohibidas en la sección "Opciones de
  configuración" al final de este documento.

Código de ejemplo:

```java
Target.Elastic.Update.builder()
    .alias({YOUR_TARGET_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_INDEX_NAME})
    .pkField({PK_FIELD})
    .routingField({ROUTING_FIELD})
    .bulkSize({BULK_SIZE})
    .bulkSizeMB({BULK_SIZE_MB})
    .addCustomElasticHadoopConfig({{KEY}},{{VALUE}})
    .build()
```



## Opciones de configuración

Con el método *addCustomElasticHadoopConfig* puedes añadir opciones de lectura/escritura que Spark permite para Elastic.
Pero desde la arquitectura, hay opciones que no se pueden utilizar y otras que se han configurado con un valor por
defecto diferente al de Spark.

### Opciones prohibidas

Esta tabla contiene un listado con los valores prohibidos.

|     Nombre de la propiedad      | 
|:-------------------------------:|
|       es.batch.size.bytes       |
|      es.batch.size.entries      |
|     es.batch.write.refresh      | 
|         es.http.timeout         | 
|      es.index.auto.create       | 
| es.input.max.docs.per.partition | 
|      es.keystore.location       | 
|      es.mapping.date.rich       | 
|          es.mapping.id          | 
|      es.net.http.auth.pass      | 
|      es.net.http.auth.user      | 
|           es.net.ssl            | 
|            es.nodes             | 
|      es.nodes.client.only       | 
|       es.nodes.data.only        | 
|       es.nodes.discovery        | 
|        es.nodes.wan.only        | 
|             es.port             | 
| es.read.field.as.array.include  | 
|        es.read.metadata         | 
|    es.read.shard.preference     | 
|           es.resource           | 
|         es.scroll.size          | 
|       es.write.operation        |
|       es.mapping.routing        |

### Valores por defecto

En la siguiente tabla se muestran los valores por defecto que la arquitectura establece para algunas opciones.
Las opciones que no aparezcan en la tabla tendrán el valor por defecto especificado en la documentación de Spark.

| Nombre de la propiedad | Valor por defecto | 
|:----------------------:|:-----------------:|
|  es.batch.size.bytes   |        4mb        |
|  es.index.auto.create  |       false       |
|     es.scroll.size     |       1000        |


# connectors/05-HTTP.md
# HTTP API

**API** es el acrónimo de **Application Programming Interface (Interfaz de Programación de Aplicaciones en castellano)**, el cual es un programa intermediario que **permite dos aplicaciones comunicarse entre ellas**.
Cada vez que se usa una app como BBVA, un mensaje instantáneo es enviado, o cuando se comprueba el tiempo con un dispositivo electrónico una API esta siendo usada.

## Tipos de *Source*

Si el desarrollador desea crear un dataset mediante llamadas a una API, LRBA provee de un *Source* para ese propósito. 
En este caso el desarrollador deberá implementar una clase que realice las llamadas API, así como la lectura de los datos devueltos por la API. Este paso lo explicaremos mas adelante.

**IMPORTANTE**: Como estamos usando Spark para ejecutar las llamadas de la API, hay una serie de elementos relevantes que deben ser tenidos en cuenta:

- A diferencia de otros procesos de la arquitectura, no es posible ejecutar de forma paralela debido a que las llamadas a API son secuenciales. Por lo tanto, el desarrollador deberá tener en cuenta que el tiempo de ejecución de este *job* será mayor que otro tipo de *jobs* y que solo levantará un ejecutor.
- Como el desarrollador va a implementar una clase que realice las llamadas API, será el responsable de conocer como se estructura la respuesta de la API y como se debe procesar, así como de manejar los errores que puedan surgir en las llamadas.

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*. El Dataset debe de ser una implementación de la interfaz `ISparkHttpData`.
- **serviceName**: Este campo no debería ser rellenado en el builder porque es ignorado.
- **physicalName**: Este campo no debería ser rellenado en este builder porque es ignorado.
- **schema**: Esquema del *Dataset* que va a ser creado. Puede ser un *Bean* o un *StructType*.
- **url**: URL de la API que va a ser llamada.
- **apiReaderClass**: Implementación propia de la clase `HttpReaderRequestHandler`. Ver la sección de más abajo para más detalles de como implementar esta clase.
- **authentication *(OPCIONAL)***: Instancia de autenticación. Actualmente, sólo OAuth y mTLS son admitidas como métodos de autenticación. Si este campo no es informado las llamadas serán ejecutadas con ninguna autenticación. Ver la sección de Autenticación más abajo para más detalles de como usar este parámetro.
- **proxy *(OPCIONAL)***: Configuración del proxy a un servicio externo (fuera de la red interna del BBVA) va a ser solicitado.

Código de ejemplo:
```java
Source.Http.builder()
        .alias({YOUR_SOURCE_ALIAS})
        .schema({BEAN|STRUCTYPE})
        .url({YOUR_API_URL})
        .apiReaderClass({YOUR_API_READER_CLASS})
        .authentication(Authentication.OAuth.builder()
                .uri({OAUTH_TOKEN_ENDPOINT})
                .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
                .request({OAUTH_REQUEST_INSTANCE})
                .responseClass({AUTH_RESPONSE_CLASS})
                .authInHeader({AUTH_IN_HEADER})
                .method({REQUEST_METHOD})
                .tokenExpiredStatusCode({TOKEN_EXPIRED_STATUS_CODE})
                .contentTypeToken({PAYLOAD_CONTENT_TYPE})
                .build())
        .proxy(Proxy.Http.builder()
                .type({PROXY_TYPE})
                .authentication(Authentication.Proxy.Basic.builder()
                        .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
                        .build())
                .build())
        .build()
```

Para un ejemplo completo usando este *Source*, ver el *codelab* [Lectura API HTTP](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Lectura%20API%20HTTP%20%28ESP%29/Introducci%C3%B3n/).  
Para ejecutar lecturas paginada, ver el *codelab* [Lectura API HTTP paginada](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Lectura%20API%20HTTP%20con%20paginaci%C3%B3n%20%28ESP%29/Introducci%C3%B3n/).

### Implementar la clase `HttpReaderRequestHandler`

El desarrollador debe implementar una clase que extienda de `HttpReaderRequestHandler` para realizar las llamadas API y procesar los datos devueltos por la API. Esta clase debe implementar un método para controlar el iterador de elementos de la respuesta de la API. Este método es el `next`.
También se debe definir el iterador con el formato de la respuesta del api. Por ejemplo, construir un método `getIterator` que define un iterador que utiliza el formato de la respuesta del API. Primero, se crea un objeto URI a partir de la URL proporcionada. 
Luego, se construye una solicitud API (ApiRequest) con el tipo de respuesta esperado (ApiResponseWrapper). Posteriormente, se ejecuta la solicitud y se obtiene la respuesta (ApiResponse). 
A partir del cuerpo de la respuesta (ApiResponseWrapper), se accede a los resultados y se devuelve un iterador sobre ellos.

Una vez creado el iterador es importante actualizar el mismo en la clase padre. Esto asegura que la lógica definida en 
el método setIterator de la clase base se ejecute, mientras te permite extender o modificar el comportamiento en la clase hija.

Para facilitar el trabajo del desarrolador, LRBA provee de un método `execute` que se encarga de realizar la llamada API pasando la petición `ApiRequest` y el *wrapper* para mapear la respuesta, devolviendo un objeto `ApiResponse<MiWrapper>`.
Además se tienen dos métodos `getUrl` y `getSchema` que devuelven la URL y el esquema indicados en el *Source* para ser utilizados si es necesario.
De cara a los test unitarios se podrá simular la llamada API y la respuesta devuelta, mediante el *mock* del método `execute` de la interfaz `IHttpConnector`. 

Es importante tener en cuenta que todo lo que se codifique en esta clase tiene que ser serializable, ya que se va a ejecutar en un *job* de Spark con ejecutores.
Aunque esto ya se valida en runtime y saldrá un error si no es así, es importante tenerlo en cuenta por si en pruebas locales funciona y en el cluster no.

Código de ejemplo:
```java
public class ApiProvider extends HttpRequestReaderHandler {
    Iterator<PersonData> iterator;
    
    public ApiProvider(StructType schema, String url, Authentication authentication, Proxy proxy) {
        super(schema, url, authentication, proxy);
        this.iterator = null;
    }

    @Override
    public boolean next() {
        // Controlar si hay más resultados o páginas
        // 1. Obtener el interador
        // 2. super.setIterator(iterator)
      if (hasMoreResults()) {
          iterator = getIterator();
        super.setIterator(iterator);
        return true;
      }
      return false;
    }
    

}
```

En el constructor de la clase, el desarrollador debe de llamar al constructor de la clase padre con el esquema, la URL, la autenticación y el proxy que se han pasado en el *Source*. 
Los dos primeros se utilizan para que el desarrollador pueda acceder a ellos en los métodos `getUrl` y `getSchema` respectivamente, mientras que los dos últimos se utilizan internamente para realizar la llamada API.

En los codelab mencionados en la sección previa se puede encontrar un ejemplo completo de como implementar esta clase, aunque el desarrollador tiene libertad para maperar los resultados de la API como desee.

### Autenticación

La mayoría de las APIs HTTP tiene algún tipo de autenticación. La más corriente es OAuth, pero a mTLS también se le da soporte.
A diferencia del conector *Target*, la paquetería para la autenticación se encuentra en `com.bbva.lrba.domain.http.model.*`.

#### OAuth

Para usar la autenticación OAuth, es necesario implementar dos clases: `OAuthRequest` and `OAuthResponse`.

Parámetros:
- **uri**: Endpoint OAuth que debe ser llamado para obtener el token.
- **credentialsKey**: Clave del *Vault* donde LRBA buscara la *clientId* y el *clientSecret*. Las credenciales deben de ser **exactamente** el alias indicado cuando se realiza la petición del credencial.
  Encontrará más detalles de como solicitar credenciales en la sección *Servicios Externos* aquí: [Crear Credenciales](../../../commonoperations/01-CreateCredentials.md).
- **request**: Instancia de una clase que hereda de `OAuthRequest`. Ver más detalles en la sección de más abajo.
- **responseClass**: Instancia que hereda de `OAuthResponse`. Ver más detalles en la sección de más abajo.
- **authInHeader *(OPCIONAL)***: Indica si la autenticación contra un servidor de OAuth esta hecha a través de *Basic authentication* o usando *Body Payload*. Por defecto: `false`.
- **method *(OPCIONAL)***: Endpoint y forma de la petición para el token OAuth. Por defecto: `HttpMethod.POST`.
- **tokenExpiredStatusCode *(OPCIONAL)***: Código de status devuelto cuando se ejecutan las llamadas a la API si el token de autenticación espira. Por defecto: `401`.
- **contentTypeToken *(OPCIONAL)***: Si la autenticación contra el servidor de OAuth es hecha usando *payload*, indicar si es *JSON* o *WWW Form Encoded*. Por defecto: `SparkContentType.WWW_FORM_URLENCODED`.

Código de Ejemplo:
```java
Authentication.OAuth.builder()
        .uri({OAUTH_TOKEN_ENDPOINT})
        .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
        .request({OAUTH_REQUEST_INSTANCE})
        .responseClass({OAUTH_RESPONSE_CLASS})
        .authInHeader({AUTH_IN_HEADER})
        .method({REQUEST_METHOD})
        .tokenExpiredStatusCode({TOKEN_EXPIRED_STATUS_CODE})
        .contentTypeToken({PAYLOAD_CONTENT_TYPE})
        .build()
```

##### OAuthRequest
SparkOAuthRequest declara dos atributos: `cIdAttrName` and `cSecretAttrName`. Éstos indican el nombre de aquellos parámetros que se llaman cuando se invoca al *endpoint* del token de OAuth
si la autenticación contra el servidor de OAuth no se realiza a través de *Basic authentication*. Los valores por defecto son: `client_id` y `client_secret` respectivamente.

Estos atributos pueden ser modificados en el constructor. Los parámetros adicionales necesitan ser informados, por ejemplo `grant_type` o `scopes`. Estos pueden ser también declarados en esta clase y pueden ser inicializados en el constructor.

##### OAuthResponse
SparkOAuthResponse declara tres atributos: `accessTokenAttrName`, `expiresInAttrName` y `tokenTypeAttrName` los cuales indican el nombre de esos parámetros cuando se procesa la respuesta del endpoint del token OAuth. Los valores por defecto son: `access_token`, `expires_in` y `token_type` respectivamente.
De forma similar a `OAuthRequest` pueden ser modificados en el constructor.

#### Mutual TLS (mTLS)

LRBA actualmente también usa la autenticación Mutual TLS. Este tipo de autenticación requiere un certificado por parte del cliente (bot) para autentificar las llamadas.

Parámetros:
- **botKey**: Clave del bot del Vault donde el certificado del cliente es guardado. La clave del bot debe de ser **exactamente**  el alias indicado cuando se solicita el certificado. Es decir, que si el certificado generado es de la forma `UUAA.alias.p12`, **sólo** se debe introducir el valor de alias.

  Para más detalles sobre solicitar certificados, vayan a la sección *Solicitar certificados para Http Mutual TLS* aquí: [Crear credenciales](../../../commonoperations/01-CreateCredentials.md).

Código de Ejemplo:
```java
Authentication.MTLS.builder()
        .botKey({MTLS_BOT_KEY})
        .build()
```

### Proxy

#### HTTP Proxy

Las API REST que existen fuera de la red interna del BBVA deben ser invocadas usando un Proxy HTTP.

Parámetros:
- **type *(OPCIONAL)***: Algunas APIs pueden usar el proxy `BUSINESS` y otras podrían usar el proxy `ARCHITECTURE`. Por defecto: `BUSINESS`.
- **authentication *(OPCIONAL)***: Las APIs externas pueden requerir Autenticación de proxy básica para que esas llamadas puedan ser usadas con un proxy. Ver la sección _Autenticación Proxy_ más abajo para más detalles.

Código de Ejemplo:
```java
Proxy.Http.builder()
        .type({PROXY_TYPE})
        .authentication(Authentication.Proxy.Basic.builder()
                .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
                .build())
        .build()
```

##### Autenticación Proxy

Para la mayoría de las APIs externas es necesario el tener credenciales para que esta manera el proxy las acepte y redirija estas llamadas. Actualmente, solo la Autenticación de acceso básica es aceptada.

Parámetros:
- **credentialsKey**: Clave del *Vault* donde la autenticación básica es guardada. La clave de la credencial debe de ser **exactamente** el alias indicado cuando se solicita el credencial.
  Para más detalle sobre la solicitud de credenciales, vaya a la sección *Servicios Externos* aquí: [Crear credenciales](../../../commonoperations/01-CreateCredentials.md).

Código de Ejemplo:
```java
Authentication.Proxy.Basic.builder()
        .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
        .build()
```

## Tipos de *Target*

Si el desarrollador desea ejecutar llamadas a una API, LRBA provee de un *Target* para ese propósito. Actualmente, soporta llamadas API a través de HTTP REST que usan formato JSON o WWW_FORM_URLENCODED para intercambio de datos.  
Es posible utilizar diferentes tipos de datos indicando un String con la correcta estructura en el body de la petición. De esta manera la arquitectura no los serializará a tipos soportados y respetará la información recibida. Encontrará más información sobre esto al final de esta sección. 


**IMPORTANTE**: Como estamos usando Spark para ejecutar las llamadas de la API de una forma paralela, hay una serie de elementos relevantes que deben ser tenidos en cuenta:

- Los *executors* de Spark pueden fallar. Como resultado, algunas llamadas a API pueden ser ejecutadas más de una vez. Recomendamos encarecidamente usar esta funcionalidad con APIs idempotentes. 
- Debido al paralelismo de Spark, la API puede recibir muchas llamadas por segundo por lo que hay que estar seguro de que la API se escala apropiadamente y es capaz de procesar toda la carga generada por el *job*.


### REST

Ejecutar una petición HTTP REST contra una la URI indicada.

Antes de usar este destino, el Dataset debe de ser convertido a la implementación propia de `ISparkHttpData` para que el Target sepa el tipo de autenticación, endpoint de la API, etc. Compruebe [Ejecutar llamadas a API](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Ejecutar%20peticiones%20HTTP%20%28ESP%29/Introduction/) en el *codelab* para más información sobre como implementarlo.

Si el desarrollador quiere procesar las llamadas REST en el mismo *job*, por ejemplo para almacenar peticiones erróneas, es posible usar la [Utilidad HTTP: Enviando Datasets a API HTTP](../01-Utils.md) en el Transform del Dataset.
Este destino almacena todos los resultados de las llamadas a API HTTP REST, incluidos el body y el resultado.
Sin embargo, aunque el implementar todas esas clases pueda parecer complejo, después de hacerlo, este destino es fácil de utilizar y muy potente.
Si no se necesita más procesamiento para las llamadas HTTP API en el mismo *job*, nosotros recomendamos encarecidamente usar con [Utilidad HTTP](../01-Utils.md).

Parámetros:
- **alias**: Nombre con el que se inserta el *Dataset* en el mapa en la clase *Transformer* para poder identificarlo en el *target*. El Dataset debe de ser una implementación de la interfaz `ISparkHttpData`.
- **serviceName**: Este campo no debería ser rellenado en el builder porque es ignorado.
- **physicalName**: Este campo no debería ser rellenado en este builder porque es ignorado.
- **authentication *(OPCIONAL)***: Instancia de autenticación. Actualmente, sólo OAuth y mTLS son admitidas como métodos de autenticación. Si este campo no es informado las llamadas serán ejecutadas con ninguna autenticación. Ver la sección de Autenticación más abajo para más detalles de como usar este parámetro.
- **proxy *(OPCIONAL)***: Configuración del proxy a un servicio externo (fuera de la red interna del BBVA) va a ser solicitado.
- **httpDataClass**: Implementación propia de la interfaz `ISparkHttpData`. Esta clase debe de ser la misma que el Dataset va a procesar en el *target*.
- **responseBodyClass *(OPCIONAL)***: La respuesta JSON será deserializada en esta clase para su posterior procesamiento. Puede ser interesante añadir un atributo de error (el nombre depende de la API) donde los mensajes de error serán escritos en caso de que la API falle. Si una `String.class` es indicada, el JSON no será convertido y será devuelto directamente.
- **responseTarget *(OPCIONAL)***: Instancia de *Target* donde los datos de la API van a ser almacenados. Se almacenan usando el atributo `httpDataClass` del *Target*. Si es indicado este campo, `responseBodyClass` debe ser informado.
- **semaasHeaders *(OPCIONAL)***: Parámetro booleano que permite escribir encabezados SEMaaS en los *logs* del *job*. Si no se especifica los encabezados no se escribirán.

Código de ejemplo:
```java
Target.Http.REST.builder()
        .alias({YOUR_TARGET_ALIAS})
        .authentication(Authentication.OAuth.builder()
                .uri({OAUTH_TOKEN_ENDPOINT})
                .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
                .request({SPARK_OAUTH_REQUEST_INSTANCE})
                .responseClass({SPARK_OAUTH_RESPONSE_CLASS})
                .authInHeader({AUTH_IN_HEADER})
                .method({REQUEST_METHOD})
                .tokenExpiredStatusCode({TOKEN_EXPIRED_STATUS_CODE})
                .contentTypeToken({PAYLOAD_CONTENT_TYPE})
                .build()
        .proxy(Proxy.Http.builder()
                .type({PROXY_TYPE})
                .authentication(Authentication.Proxy.Basic.builder()
                        .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
                        .build())
                .build())
        )
        .httpDataClass({SPARK_API_IMPL_CLASS})
        .responseBodyClass({SPARK_API_RESPONSE_CLASS})
        .responseTarget(Target.File.Parquet.builder()
                .alias({YOUR_TARGET_ALIAS})
                .serviceName({YOUR_INVENTORY_SERVICE_NAME})
                .physicalName({YOUR_PHYSICAL_NAME})
                .build())
        .semaasHeaders(true)
        .build()
```

Para un completo ejemplo usando este *Target*, ver [Ejecutar llamadas API](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Ejecutar%20peticiones%20HTTP%20%28ESP%29/Introduction/) *codelab*.  
Para utilizar el conector HTTP con otro tipo de dato que no sea JSON ver [Ejecutar llamadas con XML](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Ejecuci%C3%B3n%20de%20peticiones%20HTTP%20con%20XML%20%28ESP%29/Introducci%C3%B3n/) *codelab*.  

#### Autenticación

La mayoría de las APIs HTTP tiene algún tipo de autenticación. La más corriente es OAuth, pero a mTLS también se le da soporte.

##### OAuth

Para usar la autenticación OAuth, es necesario implementar dos clases: `SparkOAuthRequest` and `SparkOAuthResponse`.

Parámetros:
- **uri**: Endpoint OAuth que debe ser llamado para obtener el token.
- **credentialsKey**: Clave del *Vault* donde LRBA buscara la *clientId* y el *clientSecret*. Las credenciales deben de ser **exactamente** el alias indicado cuando se realiza la petición del credencial.
  Encontrará más detalles de como solicitar credenciales en la sección *Servicios Externos* aquí: [Crear Credenciales](../../../commonoperations/01-CreateCredentials.md).
- **request**: Instancia de una clase que hereda de `SparkOAuthRequest`. Ver más detalles en la sección de más abajo.
- **responseClass**: Instancia que hereda de `SparkOAuthResponse`. Ver más detalles en la sección de más abajo.
- **authInHeader *(OPCIONAL)***: Indicar si la autenticación contra un servidor de OAuth esta hecha a través de *Basic authentication* o usando *Body Payload*. Por defecto: `false`.
- **method *(OPCIONAL)***: Endpoint y forma de la petición para el token OAuth. Por defecto: `HttpMethod.POST`.
- **tokenExpiredStatusCode *(OPCIONAL)***: Código de status devuelto cuando se ejecutan las llamadas a la API si el token de autenticación espira. Por defecto: `401`.
- **contentTypeToken *(OPCIONAL)***: Si la autenticación contra el servidor de OAuth es hecha usando *payload*, indicar si es *JSON* o *WWW Form Encoded*. Por defecto: `SparkContentType.WWW_FORM_URLENCODED`.

Código de Ejemplo:
```java
Authentication.OAuth.builder()
        .uri({OAUTH_TOKEN_ENDPOINT})
        .credentialsKey({OAUTH_CREDENTIALS_VAULT_KEY})
        .request({SPARK_OAUTH_REQUEST_INSTANCE})
        .responseClass({SPARK_OAUTH_RESPONSE_CLASS})
        .authInHeader({AUTH_IN_HEADER})
        .method({REQUEST_METHOD})
        .tokenExpiredStatusCode({TOKEN_EXPIRED_STATUS_CODE})
        .contentTypeToken({PAYLOAD_CONTENT_TYPE})
        .build()
```

###### SparkOAuthRequest
SparkOAuthRequest declara dos atributos: `cIdAttrName` and `cSecretAttrName`. Éstos indican el nombre de aquellos parámetros que se llaman cuando se invoca al *endpoint* del token de OAuth
si la autenticación contra el servidor de OAuth no se realiza a través de *Basic authentication*. Los valores por defecto son: `client_id` y `client_secret` respectivamente.

Estos atributos pueden ser modificados en el constructor. Los parámetros adicionales necesitan ser informados, por ejemplo `grant_type` o `scopes`, pueden ser también declarados en esta clase y pueden ser inicializados en el constructor.

###### SparkOAuthResponse
SparkOAuthResponse declara tres atributos: `accessTokenAttrName`, `expiresInAttrName` y `tokenTypeAttrName` los cuales indican el nombre de esos parámetros cuando se procesa la respuesta del endpoint del token OAuth. Los valores por defecto son: `access_token`, `expires_in` y `token_type` respectivamente.
De forma similar a `SparkOAuthRequest` pueden ser modificados en el constructor.

##### Mutual TLS (mTLS)

LRBA actualmente también usa la autenticación Mutual TLS. Este tipo de autenticación requiere un certificado por parte del cliente (bot) para autentificar las llamadas.

Parámetros:
- **botKey**: Clave del bot del Vault donde el certificado del cliente es guardado. La clave del bot debe de ser **exactamente**  el alias indicado cuando se solicita el certificado. Es decir, que si el certificado generado es de la forma `UUAA.alias.p12`, **sólo** se debe introducir el valor de alias.

  Para más detalles sobre solicitar certificados, vayan a la sección *Solicitar certificados para Http Mutual TLS* aquí: [Crear credenciales](../../../commonoperations/01-CreateCredentials.md).

Código de Ejemplo:
```java
Authentication.MTLS.builder()
        .botKey({MTLS_BOT_KEY})
        .build()
```

#### Proxy

##### HTTP Proxy

Las API REST que existen fuera de la red interna del BBVA deben ser invocadas usando un Proxy HTTP.

Parámetros:
- **type *(OPCIONAL)***: Algunas APIs pueden usar el proxy `BUSINESS` y otras podrían usar el proxy `ARCHITECTURE`. Por defecto: `BUSINESS`.
- **authentication *(OPCIONAL)***: Las APIs externas pueden requerir Autenticación de proxy básica para que esas llamadas puedan ser usadas con un proxy. Ver la sección _Autenticación Proxy_ más abajo para más detalles.

Código de Ejemplo:
```java
Proxy.Http.builder()
        .type({PROXY_TYPE})
        .authentication(Authentication.Proxy.Basic.builder()
                .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
                .build())
        .build()
```

###### Autenticación Proxy

Para la mayoría de las APIs externas es necesario el tener credenciales para que esta manera el proxy las acepte y redirija estas llamadas. Actualmente, solo la Autenticación de acceso básica es aceptada.

Parámetros:
- **credentialsKey**: Clave del *Vault* donde la autenticación básica es guardada. La clave de la credencial debe de ser **exactamente** el alias indicado cuando se solicita el credencial. 
  Para más detalle sobre la solicitud de credenciales, vaya a la sección *Servicios Externos* aquí: [Crear credenciales](../../../commonoperations/01-CreateCredentials.md).

Código de Ejemplo:
```java
Authentication.Proxy.Basic.builder()
        .credentialsKey({PROXY_BASIC_CREDENTIALS_KEY})
        .build()
```


# connectors/06-Couchbase.md
# Couchbase

**Couchbase** es un un sistema de código abierto de manejo de bases de datos **NoSQL** que utiliza documentos flexibles en lugar de tablas y filas, para procesar y almacenar varios tipos de datos.

## Tipo de Source

LRBA Architecture permite *jobs* que lean desde **cualquier colección de Couchbase**

### Query

El *builder* de tipo *Couchbase Query* permite leer datos de una colección mediante una consulta SQL.

Parámetros:
- **alias**: Nombre utilizado en la clase Transformer para identificar el *Dataset* recuperado desde el *Map*.
- **serviceName**: Se emplea para recuperar información de la base de datos. El formato deberá ser: *`couchbase.BCB_{UUAA}_{COUNTRY}_{BUCKET}.BATCH`*.
- **physicalName**: Colección de documentos Couchbase.
- **sql *(OPCIONAL)***: Consulta datos utilizando una *query* SQL para filtar los datos leídos. Por defecto, recupera todos los datos. Recuerda que el nombre de la colleción en la *query* es el mismo que se indica en el campo del alias, no el nombre real de la colección.
- **schema *(OPCIONAL)***: Permite aportar un *Bean* o *StructType* indicando el esquema a ser leído.

  Código de ejemplo:
```java
Source.Couchbase.Query.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql({YOUR_SQL})
    .schema({BEAN|STRUCTYPE})
    .build()
```

### Partitioned

El *builder* de tipo *Couchbase Partitioned* permite indicar la cantidad de particiones que Spark usará y como debe realizar esas particiones.

Parámetros:
- **alias**: Nombre utilizado en la clase Transformer para identificar el *Dataset* recuperado desde el *Map*.
- **serviceName**: Se emplea para recuperar información de la base de datos. El formato deberá ser: *couchbase.{UUAA}_{BUCKET}.BATCH*.
- **physicalName**: Colección de documentos Couchbase.
- **sql *(OPCIONAL)***: Consulta datos utilizando una *query* SQL para filtar los datos leídos. Por defecto, recupera todos los datos. Recuerda que el nombre de la colleción en la *query* es el mismo que se indica en el campo del alias, no el nombre real de la colección.
- **schema *(OPCIONAL)***: Permite aportar un *Bean* o *StructType* indicando el esquema a ser leído.
- **column**: El nombre de la columna usada para generar las particiones. Debe ser una columna de tipo numérico o fecha.
- **lowerBound**: Debe ser similar al valor mínimo esperado para la columna de particionado en la tabla dada.
- **upperBound**: Debe ser similar al valor máximo esperado para la columna de particionado en la tabla dada.
- **numPartitions**: El número máximo de particiones que se pueden usar para el paralelismo en la lectura de la tabla. Esto también determina el número máximo de conexiones JDBC concurrentes.

  Código de ejemplo:
```java
Source.Couchbase.Query.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql({YOUR_SQL})
    .schema({BEAN|STRUCTYPE})
    .column({PARTITION_COLUMN})
    .lowerBound({LOWER_BOUND_VALUE})
    .upperBound({UPPER_BOUND_VALUE})
    .numPartitions({NUM_PARTITON})
    .build()
```

Ejemplo de un caso particular con lo valores *lowerBound = 0, upperBound = 45000000 y numPartitions = 4*:
```java
Source.Couchbase.Query.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql("SELECT * FROM ALIAS") 
    .column("COLUNM")
    .lowerBound(0)
    .upperBound(45000000)
    .numPartitions(4)
    .build()
```

La base de datos recibirá las siguientes consultas N1QL:
``` sql
SELECT * FROM TABLE WHERE COLUMN < 11250000
SELECT * FROM TABLE WHERE COLUMN >= 11250000 AND COLUMN < 22500000
SELECT * FROM TABLE WHERE COLUMN >= 22500000 AND COLUMN < 33750000
SELECT * FROM TABLE WHERE COLUMN >= 33750000
```

Ejemplo de particionado por una columna de tipo fecha:
```java
Source.Couchbase.Query.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .sql("SELECT * FROM ALIAS") 
    .column("DATE_COLUNM")
    .lowerBound(LocalDate.of(2017, 10, 1))
    .upperBound(LocalDate.of(2022, 10, 31))
    .numPartitions(4)
    .build()
```

## Operaciones en Destino

### Upsert

Inserta datos o los actualiza si la clave del documento ya existe. Couchbase almacena documentos por clave-valor. Esta clave tiene como nombre "__META_ID" y no es autogenerada.

Parámetros:
- **alias**: Nombre utilizado en la clase *Transformer* para identificar el *Dataset* recuperado desde el *Map*.
- **serviceName**: Se emplea para recuperar información de la base de datos. El formato deberá ser: *`couchbase.BCB_{UUAA}_{COUNTRY}_{BUCKET}.BATCH`*.
- **physicalName**: Colección de documentos Couchbase.
- **idField *(OPCIONAL)**: Nombre del campo que contiene el identificador del documento. Si no se especifica, se usará la columna "__META_ID" del dataset.

  Código de ejemplo:
```java
Target.Couchbase.Upsert.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .idField({ID_FIELD}) 
    .build()
```

### Delete

Borra datos en base a unos **identificadores de documentos** dados. Al igual que en la operación *Upsert*, es necesario tener un dataset que contenga la columna "__META_ID" con los identificadores de los documentos a borrar. Si no se tiene esta columna, el proceso borrará por la columna 0.

Parámetros:
- **alias**: Nombre utilizado en la clase *Transformer* para identificar el *Dataset* recuperado desde el *Map*.
- **serviceName**: Se emplea para recuperar información de la base de datos. El formato deberá ser: *`couchbase.BCB_{UUAA}_{COUNTRY}_{BUCKET}.BATCH`*.
- **physicalName**: Colección de documentos Couchbase.
- **bulkSize *(OPCIONAL)***: Se utiliza para establecer el tamaño "bulk" en la operación de borrado, debe estar en un rango entre 10 y 10000. Por defecto, 4096.

  Código de ejemplo:
```java
Target.Couchbase.Delete.builder()
    .alias({YOUR_SOURCE_ALIAS})
    .serviceName({YOUR_SERVICE_NAME})
    .physicalName({YOUR_PHYSICAL_NAME})
    .bulkSize({BULK_SIZE})
    .build()
```

# connectors/07-BEA.md
# GRPC BEA

**BEA** es el acrónimo de **Business Events Architecture (Arquitectura de Eventos de Negocio en castellano)**, es la evolución 
de las arquitecturas de Eventos de BBVA, que no sustituye si no que complementa la Arquitectura de Eventos actual basada en **Upsilon** y **PSI**

## Tipos de *Target*

Actualmente **LRBA** es arquitectura productora y no consumidora de eventos, por lo que solo se pone a disposición del desarrollador un **Target** para este propósito. Sin embargo, se permite consumir eventos de manera indirecta al procesar las [Deadletter](01-File.md#deadletter).


### Publish

Parámetros:
- **alias**: Nombre usado en la clase *Transformer* para recuperar el *Dataset* del mapa de entrada.
- **eventId**: Identificador único del evento.
- **majorVersion**: Número de versión major del evento que se quiere publicar.
- **minorVersion**: Número de versión minor del evento que se quiere publicar.
- **bulkSize *(OPCIONAL)***: Establece el tamaño de *bulk* de eventos. Debe estar en un rango entre 10 y 10000. . Por defecto, 100.


Código de ejemplo:
```java
Target.Bea.Publish.builder()
        .alias({YOUR_TARGET_ALIAS})
        .eventId({EVENT_ID})
        .majorVersion({MAJOR_VERSION})
        .minorVersion({MINOR_VERSION})
        .bulkSize({BULK_SIZE})
        .build()
```

**IMPORTANTE**: Desde la arquitectura se proporciona la clase **SparkEventBean**. <br>
Esta clase contiene todos los campos referentes al contenido y a las cabeceras del evento. <br>
Es importante que el dataset que llegue al Target sea de este tipo para el correcto funcionamiento del conector.
#### Cabeceras del evento
A continuación se muestra una tabla con las cabeceras de un evento de BEA.

| Nombre campo             | Valor por defecto | Validación Regex |
|--------------------------|-------------------|------------------|
| aap                      |                   | '^.{0,12}$'      |
| authorizationCode        | '000000000'       | '^[0-9]{9}$'     |
| authorizationVersion     | '00'              | '^[0-9]{2}$'     |
| branchCode               | '9999'            | '^[0-9]{4}$'     |
| channelCode              | '00'              | '^[0-9]{2}$'     |
| clientDocument           |                   | '^.{0,25}$'      |
| clientIdentificationType |                   | '^.{0,1}$'       |
| contactIdentifier        |                   | '^.{0,40}$'      |
| countryCode              | 'ZZ'              | '^.{0,2}$'       |
| currencyCode             | 'ZZZ'             | '^.{0,3}$'       |
| entityCode               | '9999'            | '^[0-9]{4}$'     |
| environCode              | '00'              | '^[0-9]{2}$'     |
| languageCode             | 'ZZ'              | '^.{0,2}$'       |
| operativeBranchCode      | '0000'            | '^[0-9]{4}$'     |
| operativeEntityCode      | '0000'            | '^[0-9]{4}$'     |
| productCode              | '0000'            | '^[0-9]{4}$'     |
| secondaryCurrencyCode    | 'ZZZ'             | '^.{0,3}$'       |



