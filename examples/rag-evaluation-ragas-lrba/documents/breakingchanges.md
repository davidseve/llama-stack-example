En este documento se describen los cambios que afectan a los aplicativos por funcionalidades que rompen con el uso normal de la arquitectura en cada una de las versiones de LRBA.

# Breaking changes LRBA 2.1

Con la actualización de LRBA 2.1, se han producido ciertas actualizaciones que modifican el comportamiento de la Arquitectura. A continuación, se describen las modificaciones, cómo localizarlas y cómo subsanar los posibles errores:
- No se permite el uso de librerías transitivas.
- Input params mal formados
- Eliminación definitva de la clase SparkHttpData


## 1. Prohibido el uso de librerías transitivas.
Está prohibido usar librerías de dependencias transitivas. Solo se podrán usar las librerías especificadas en la documentación.
Hay ciertas librerías de terceros que en el pasado (LRBA<=2.1) han quedado expuestas erróneamente para uso por parte del aplicativo. Debido a que no eran librerías que desde LRBA estuvieramos exponiendo de forma directa, si no a través de dependencias transitivas de terceros, si estos terceros modifican sus dependencias, se rompen el API del SDK.
Para que esto no vuelva a pasar, se han modificado los pom-parent de LRBA a partir de esta release, de forma que queden excluidas las dependencias transitivas.
Si algún aplicativo estuviera usando alguna librería transitiva que crea que debería de exponerse directamente en el pom-parent, debe de ponerse en contacto con nosotros para su evaluación. 

- Ejemplo KO: `import org.apache.commons.lang.StringUtils`
- Ejemplo Corregido: `import org.apache.commons.lang3.StringUtils`

Cómo localizar el problema: 
- En BitBucket `import org.apache.commons.lang.*`
- En Atenea, en caso de error, por `message = java.lang.NoClassDefFoundError: org/apache/commons/lang/StringUtils`.


## 2. Input params mal formados
Los jobs LRBA aceptan parámetros de entrada. Estos deben ser configurados desde el planificador, en el caso de Control-M en el campo input-parameters del lrba_launcher_controlm. El formato obligatorio es el siguiente: 

```
    [
        {"key": "PARAM_NAME_1", "value": "PARAM_VALUE_1"}, 
        {"key": "PARAM_NAME_2", "value": "PARAM_VALUE_2"}, 
        {"key": "PARAM_NAME_3", "value": "PARAM_VALUE_3"}, 
        ...
    ]
```

En diversas ocasiones se han recibido parámetros que no han cumplido con la definición, como por ejemplo values no-string. Esto ha generado incidencias en kubernetes. En LRBA 2.1, se ha añadido una validación en el lrba_launcher_controlm para controlar que no puedan llegar parámetros que no cumplan el formato.

Se dan por válidas estas combinaciones:
- input-parameters: []
- input-parameters: [{}]
- input-parameters: [{"key":"miclave", "value": "mivalor"}]
- input-parameters: [{"key":"miclave", "value": ""}]
- input-parameters: [{"key":"miclave", "value": "mivalor"},{"key":"miclave2", "value": "mivalor2"}]

Sin embargo las siguientes darán error
- Key vacias => input-parameters: [{"key":"", "value": "mivalor"}]
- Keys no-string => input-parameters: [{"key": 5, "value": 2}]
- Values no string => input-parameters: [{"key":"miclave", "value": 2}]
- Cualquier otra combinación que no cumpla con el formato

## 3. Eliminación definitva de la clase SparkHttpData
Se elimina la interfaz SparkHttpData deprecada en la versión 0.14.1 de LRBA. En su lugar se disponibiliza la interfaz ISparkHttpdata. Los jobs que no se hayan adaptado fallarán al no encontrar la clase SparkHttpData. 

Para buscar estos posibles errores: 
- En Bitbucket: buscar en los repositorios por `extends SparkHttpData`.
- En Atenea, para encontrar jobs afectados buscar por `message = "%SparkHttpData%" and level = "ERROR"`.


# Breaking changes Spark 3.5

Con la actualización del motor de LRBA (que es Spark), de la versión 3.3.x a la versión 3.5.x, y que se producirá en un futuro, se generan ciertos impactos que precisan de cambios en los códigos aplicativos que se vean afectados. A continuación, se describen cada uno de los impactos posibles, cómo localizarlos y cómo subsanar los posibles errores:
- No se permite usar datasets formados con genéricos
- No se permite el uso de SQL Alias con punto
- No se permite el uso de Encoders.bean con clase Scala
- No se permite el uso de la clase RowEncoder
- Eliminación definitiva del `mongo-spark-connector 3.x`

## 1. Datasets con Genericos

Desde Spark 3.4, si se quiere hacer un Encoder de una clase genérica con parámetros en runtime, el job fallará al no ser capaz de inferir los tipos. Se soluciona reemplazando los genéricos en tiempo en compilación. Mismo caso por lo que se deprecó SparkHttpData.

- Ejemplo KO:
```java
 public class Company<T> {

 private String name;
 private Team<T> team;

 public Company() {}

 public Company(String name, Team<T> team) {
        this.name = name;
        this.team = team;
    }

 public String getName() {
  return name;
}

 public void setName(String name) {
   this.name = name;
 }

 public Team<T> getTeam() {
   return team;
 }


 public void setTeam(Team<T> team) {
   this.team = team;
}
```

- Ejemplo OK:
```java
public class Company<PersonData> {

 private String name;
 private Team<PersonData> team;

 public Company() {}

 public Company(String name, Team<PersonData> team) {
        this.name = name;
        this.team = team;
 }

 public String getName() {
   return name;
 }

 public void setName(String name) {
   this.name = name;
 }

 public Team<PersonData> getTeam() {
    return team;
 }

    public void setTeam(Team<PersonData> team) {
        this.team = team;
    }
}
```
Cómo localizar el problema: buscando en BitBucket clases de modelo aplicativos que contengan genéricos. 
El error en tiempo de ejecución será del estilo `java.util.NoSuchElementException: key not found: T`

## 2. SQL Alias con punto
Con esta nueva versión, Spark 3.4 no acepta crear vistas sql cuya nomenclatura contenga un punto. Esto afecta en los builders a la declaración de alias y SQLs:

Ejemplo KO:
```java
    return Source.Jdbc.Basic.builder()
    .alias("UUAA.TABLA")
    .physicalName("UUAA.TABLA")
    .serviceName("oracle.UUAA.BATCH")
    .sql("SELECT * FROM UUAA.TABLA WHERE ")
    .build();
```
Ejemplo OK:
```java
    return Source.Jdbc.Basic.builder()
    .alias("mi_alias")
    .physicalName("UUAA.TABLA")
    .serviceName("oracle.UUAA.BATCH")
    .sql("SELECT * FROM mi_alias WHERE ..")
    .build();
```



Aclaración: El `alias` y el `from` del SQL son partículas lógicas en SparkSQL y no tienen porqué coincidir con el nombre real físico en la base de datos.

Cómo localizar el problema:  partir de LRBA 2.1, buscando la traza en Atenea con el filtro `message = "%Spark >= 3.4 is incompatible with view names that are separated (Error TEMP_VIEW_NAME_TOO_MANY_NAME_PARTS). Aliases cannot contain a dot.%"`

## 3. Uso de Encoders.bean con clase Scala

Desde esta versión de Spark, al llamar a ese método, por debajo se usa el método javaSerialization para generar el bean correspondiente y por lo tanto la clase del bean tiene que ser 100% Java e implementar la interfaz Serializable. Por ello con esta nueva versión de Spark falla al hacer Encoders.bean(Row.class).

Por otro lado, en muchos casos donde se está usando el Encoders.bean(Row.class) no es correcto, ya que ese dataset ya está en formato Dataset<Row>. Por ejemplo, el contenido del map que entrega la arquitectura a los transforms ya tiene ese tipo y sobran conversiones como la siguiente:

`Dataset<Row> dataset = datasetsFromRead.get(“alias”).as(Encoders.bean(Row.class));`

Para el caso de transformaciones lícitas a Dataset<Row> se tiene que hacer `dataset.toDF()`.

Ejemplo 1 KO:
```java
Dataset<MyBean> dsPeriod = (...)
Dataset<Row> dsPeriodificacionMid = dsPeriod.as(Encoders.bean(Row.class));
```
Ejemplo 2 Corregido:
```java
Dataset<MyBean> dsPeriod = (...)
Dataset<Row> dsPeriodificacionMid = dsPeriod.toDF();
```
Ejemplo 2 KO:
```java
    datasetsToWrite.put(Constants.TARGET_T_GDEL_EXPERIMENT, datasetsFromRead.get(Constants.SOURCE_T_GDEL_EXPERIMENT).as(Encoders.bean(Row.class)).toDF());
```
Ejemplo 2 Corregido:
```java
    datasetsToWrite.put(Constants.TARGET_T_GDEL_EXPERIMENT, datasetsFromRead.get(Constants.SOURCE_T_GDEL_EXPERIMENT));
```

Aclaraciones:
- En caso de tener que transformar desde un Dataset<MyBean> a un Dataset<Row>, no se debe hacer un dataset.as(Encoders.bean(Row.class)) . Debe usarse  dataset.toDF().
- Los datasets que llegan en el mapa datasetsFromRead son todos de tipo Row, por lo tanto no es necesario transformarlos nuevamente a Dataset<Row>.
- Solo se debe de usar el Encoders.bean para transformar los Dataset<Row> a tipos aplicativos Dataset<MyBean>.

Cómo localizar el problema: buscando en BitBucket por `Encoders.bean(Row.class)`.

## 4. Uso de RowEncoder
`RowEncoder` es una clase interna e indocumentada de Spark que obtiene Encoder de diferentes tipos para rows. Al estar dentro del paquete catalyst es una clase que no se tiene que usar desde fuera ya que puede recibir actualizaciones sin ser retrocompatibles con versiones anteriores.
En varios jobs aplicativos se está utilizando el método `RowEncoder.apply(schema)` para obtener el encoder para una Row. Desde Spark 3.5 han cambiado esa clase y ya no existe ese método apply, por lo que se tiene que sustituir por el `Encoders.row(schema)` que se ha añadido en esa misma versión y que se encuentra expuesta en el paquete SQL.
Para evitar confusiones se va a bloquear en versiones futuras el uso de clases del paquete catalyst y solo se podrá usar lo que esté fuera de él.

Ejemplo KO
```java
Dataset<Row> datasetOutput = candidates.map((MapFunction<TDBC2, Row>) row -> {
return RowFactory.create(PAIS, row.getCOD_ENTALFA(), row.getCOD_PERSCTPN());
}, RowEncoder.apply(schema));
```

Ejemplo Corregido
```java
Dataset<Row> datasetOutput = candidates.map((MapFunction<TDBC2, Row>) row -> {
return RowFactory.create(PAIS, row.getCOD_ENTALFA(), row.getCOD_PERSCTPN());
}, Encoders.row(schema));
```

Aclaraciones:
- Para cualquier encoder que se quiera conseguir hay que usar siempre la clase Encoders.
- Este cambio solo se puede aplicar compilando contra Spark 3.5.x, en versiones anteriores no existe Encoders.row().

Cómo localizar el problema: buscando en BitBucket por `RowEncoder.apply`.


## 5. Eliminación definitiva del `mongo-spark-connector 3.x`

Con la versión 0.12 de LRBA se incluyó el mongo-spark-connector 10.x, y se mantuvo en paralela la versión 3.x para los procesos que tenían una fuerte dependencia con su forma de trabajar. La duplicidad de la versión del conector se estableció de forma excepcional, para dar tiempo a los aplicativos a adaptarse de una versión del conector a otra.

Con Spark 3.5 se eliminará el soporte de forma definitiva al mongo-spark-connector 3.x. En platform se encuentra la [guía de migración](https://platform.bbva.com/lra-batch/documentation/fbbdb2946815638f32e964c90d17093b/lrba-architecture/utilities/spark/connectors/mongodb#content10).


## 6. Target Jdbc Transactional sin clase InternalRow
En el conector Jdbc Transactional se pide implementar una clase abstracta JdbcTransactionWriterHandler donde se definen las operaciones a realizar contra la base de datos. Esas operaciones se implementan dentro del método write que recibe un objeto de tipo InternalRow, que es una clase abstracta de Spark SQL (en el paquete org.apache.spark.sql.catalyst) que representa una fila interna de datos en el motor Catalyst. Esta clase es utilizada internamente por Spark para optimizar el procesamiento de datos, evitando la sobrecarga de las clases de alto nivel como Row.

Actualmente si se quieren obtener los datos de un objeto InternalRow se tiene que hacer algo como esto siguiendo el ejemplo de los codelabs:

```java
String movement_id = 
internalRow.getString((int)structType.getFieldIndex("id").get());

int account_id = internalRow.getInt((Integer)structType.getFieldIndex("account_id").get());

double amount = 
internalRow.getDouble((int)structType.getFieldIndex("amount").get());

String movement_type = internalRow.getString((int)structType.getFieldIndex("type").get());
```

Para evitar usar esa clase interna de Spark que puede dar problemas en futuras versiones, se ofrece en este método write un Map<String, Object> en lugar de InternalRow con el nombre de las columnas como clave y el valor correspondiente como valor.

```java
String movement_id = (String) row.get("id");

int account_id = (Integer) row.get("account_id");

double amount = (Double) row.get("amount");

String movement_type = (String) row.get("type");
```

# 7. Source HTTP sin clases internas de Spark

En el conector HTTP de lectura se pide implementar una clase abstracta HttpRequestReaderHandler donde se define como hacer las peticiones HTTP e iterar la respuesta. Uno de los métodos a implementar es el get() que devuelve cada elemento del iterador mapeando los resultados en un JavaBean, por ejemplo. Esto hace que la clase `InternalRow` y la clase `ExpressionEncoder`, que son clases internas de Spark, no se puedan usar directamente.

Actualmente, en este método se tiene que implementar haciendo algo como esto siguiendo el ejemplo de los codelabs:

Ejemplo código actual:

```java
@Override
public InternalRow get() {
    return getRowEncoder().createSerializer().apply(iterator.next());
}

private ExpressionEncoder<PersonData> getRowEncoder() {
    if (rowEncoder == null) {
        rowEncoder = ExpressionEncoder.javaBean(PersonData.class);
    }
    return rowEncoder;
}
```

Para dejar de usar estas clases internas, este método get pasa a estar gestionado por la arquitectura de forma que en el lado aplicativo solo se tiene que implementar la forma de recorrer el iterador con el método next. Por tanto, la clase quedaría así siguiendo el ejemplo de los codelabs.

Ejemplo LRBA 3.0:

```java
public class ApiProvider extends HttpRequestReaderHandler<PersonData> {

    private transient Iterator<PersonData> iterator;

    public ApiProvider(StructType schema, String url, Authentication authentication, Proxy proxy) {
        super(schema, url, authentication, proxy);
    }

    @Override
    public boolean next() {
        if (iterator == null) {
            iterator = getIterator();
        }
        if (iterator.hasNext()) {
            iterator.next(); // Consume the next element
            super.setIterator(iterator); // IMPORTANT: Update the iterator in the parent class
            return true;
        }
        return false;
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

# 8. Bloqueo paquete spark.sql.catalyst

Para evitar problemas como el detallado en el punto 4 con la clase interna en el paquete catalyst de Spark, se ha decidido bloquear el uso de estas clases mediante una regla de Sonar. No se podrá usar nada de `org.apache.spark.sql.catalyst`.

De esta forma se fuerza a que solo se usen las clases públicas que estén en `org.apache.spark.sql` como por ejemplo Encoders que es la interfaz principal.

# LRBA MultiSpark Version

LRBA MultiSpark Version se trata de dar la capacidad de ejecutar en el cluster de Batch la Arquitectura de LRBA con diferentes versiones de Spark. En este caso, versión 3.3 y versión 3.5 de Spark. 

Este cambio se produce con la implantación de las versiones de LRBA 2.3 (que lleva Spark 3.3) y LRBA 3.0 (que lleva Spark 3.5).

Este cambio será transparente para los aplicativos, ya que será la propia arquitectura la que decida con qué versión ejecutar los jobs a partir del pom que se utilizó para compilar:
- Si un job se ha compilado con LRBA inferior a 3.0, se ejecutará con Spark 3.3.
- Si un job se ha compilado con LRBA igual o superior a 3.0, se ejecutará con Spark 3.5.

Durante el Q3 de 2025, se disponibilizará una versión intermedia de LRBA con las 2 versiones mencionadas, que esencialmente contendrán las mismas funcionalidades, con algunas excepciones que se describen a continuación:

## Limitaciones
- A partir de esta versión, cualquier característica nueva de arquitectura sólo será incluída en la versión de LRBA con Spark 3.5.
- Desde el momento en que se implante esta versión de arquitectura en todos los entornos, se establecerá en Sonar como versión mínima para compilar. Es decir, los nuevos desarrollos y evolutivos solo podrán compilarse contra Spark 3.5. 
- Lo que ya estuviera compilado se seguirá ejecutando con Spark 3.3, mientras dure la convivencia de versiones.
- Se establecerá un periodo grande de convivencia, que durará hasta finales de Q2 de 2026 (Junio de 2026).

## Cambios en LRBA 3.0
- Se eliminará por completo el conector de Mongo 3.x. Ningún aplicativo que compile con esta versión podrá utilizar el conector de Mongo en la versión 3.x.
- Se actualizará el conector de Couchbase para que sea compatible con Spark 3.5.
- Se añade el Conector Inline Query para Couchbase.
- Los Breaking Changes de Spark 3.5 que obligan a cambiar el funcionamiento de LRBA en esta versión.
- Más información en Release Notes

