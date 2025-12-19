# developerexperience/06-BTSVisor.md
# Servicio *BTS Visor 1.0 (Postman)*
El servicio *BTS Visor* está diseñado para lanzar consultas a ficheros almacenados en BTS. También permite subir ficheros al entorno de desarrollo.  

Es obligatorio solicitar unas credenciales para usar el servicio a través de *AppStream*.  

## Acceso a AppStream

### Gestión de credenciales
Las credenciales se deben solicitar a través del [portal de gestion de credenciales](https://bbva-credentials-vault.ew.r.appspot.com/#/personal/scality). Se debe especificar el **entorno**, **país** y la **UUAA** del *bucket* BTS al que se desea acceder. Se recibirá en el correo del usuario un correo electrónico confirmando el acceso.

![CredentialsManagement](../resources/img/CredentialsBTS.png)

**IMPORTANTE:** El código INC/CRQ se debe rellenar con un String cualquiera para los entornos de Work, pero para Live debe ser un código real. Este formulario se debe rellenar por cada entorno y país cuyos ficheros se quieran consultar.

### Conectar a AppStream
Para usar el servicio *BTS Visor* es necesario hacerlo mediante **Postman** a través de [*AppStream* Work](https://secureapp-aws.live.es.platform.bbva.com/api/stack/BTSAccessWork) o [*AppStream* Live](https://secureapp-aws.live.es.platform.bbva.com/api/stack/BTSAccessLive). La URL de *AppStream* se especificará en el correo electrónico recibido anteriormente.  

![AppStream](../resources/img/AppStreamBTS.png)

### Ejecutar consultas contra el servicio

*AppStream* permite al usuario usar diferentes pestañas de *Postman* para ejecutar las peticiones disponibles. Tiene incluida una plantilla y solo será necesario cambiar el valor de las variables.  

![PostmanBTS](../resources/img/PostmanBTS.png)

## Ejecutar una consulta
**[POST]**

URL: http://localhost/bts/job/country/{COUNTRY}/environment/{ENVIRONMENT}/uuaa/{UUAA}/query

Entornos: ['dev', 'int', 'au', 'qa', 'pro']  
Paises: ['gl', 'es']

**Body schema:**
```json
{
    "fileName": ["String", "requerido"], //Nombre del fichero en el bucket BTS.
    "fileType": ["parquet/csv", "requerido"], //Formato del fichero.
    "select": ["String", "opcional"], //Columnas que se quieren obtener.
    "where": ["String", "opcional"], //Condición que se aplica a la consulta sobre el fichero.
    "count": ["Boolean", "opcional"], //Cuenta las filas que coinciden con el filtro. Si se establece a true, el campo totalElements se añade a la respuesta. Por defecto, es false.
    "header": ["Boolean", "opcional"], //Especifica si el archivo que se quiere consultar contiene encabezado. Por defecto, es true.
    "delimiter": ["String", "opcional"], //Separador entre los diferentes campos en archivos csv. Por defecto, es una coma (',').
    "page": ["integer", "opcional"] //La página que se quiere consultar. Por defecto, es la 1.
}
``` 
**IMPORTANTE:** Hay que tener cuidado con la paginación. La paginación en ficheros no es natural, y por tanto, no se recomienda. A medida que la paginación avanza a través de las páginas del fichero, las consultas se ejecutarán más lentamente debido a que debe recorrer todo el fichero. Además, puede provocar errores de timeout o de memoria.  

### Ejemplo

***Body* de ejemplo:**
```json
{
    "fileName": "{fileName}.parquet",
    "fileType": "parquet",
    "select": "column1, column2",
    "where": ""
}
```

**Respuesta de ejemplo:**
```json
{
    "fileName": "{fileName}.parquet",
    "fileType": "parquet",
    "select": "column1, column2",
    "where": "",
    "count": false,
    "page": 1,
    "requestId": "0000-0000-0000-0000",
    "userId": "userId"
}
```

**En la respuesta se devuelve el *Request ID* de la consulta lanzada, el cual será usado en otras peticiones.** Es necesario guardar este valor y cambiar la variable requestId por el valor proporcionado por la respuesta.

## Obtener estado de la consulta
**[GET]**

URL: http://localhost/bts/job/country/{COUNTRY}/environment/{ENVIRONMENT}/uuaa/{UUAA}/status/{requestId}

Environments: ['dev', 'int', 'au', 'qa', 'pro']  
Countries: ['gl', 'es']

Si el resultado es ***ERROR***, se pueden consultar en Atenea los *logs* de la ejecución accediendo al *namespace* `{country}.ether.lrba.apps.{environment}`, usando la `UUAA` como `mrId`, y buscando por nombre con el valor **BTS READER**. Lea la [documentación sobre como consultar *logs*](../developerexperience/04-ReadingJobLogs.md).  

Es necesario recibir el estado **SUCCESS** para poder leer el resultado de la consulta. Si el estado no es *SUCCESS* o *ERROR*, la consulta todavía se está ejecutando.  

**Respuestas**
```json
{"status": "INITIALIZING"}
```
```json
{"status": "SUCCESS"}
```
```json
{"status": "ERROR"}
```
```json
{"status": "RUNNING"}
```

## Obtener el resultado de la consulta
**[GET]**

URL: http://localhost/bts/job/country/{COUNTRY}/environment/{ENVIRONMENT}/uuaa/{UUAA}/result/{requestId}

Entornos: ['dev', 'int', 'au', 'qa', 'pro']  
Paises: ['gl', 'es']

El resultado de la consulta **solo estará disponible si en el paso previo se ha obtenido un *SUCCESS*.**  

El resultado de la consulta es temporal y es eliminado una vez se ha obtenido. Por esta razón, **esta petición solo se puede ejecutar una vez por cada *requestId*.**  

### Ejemplo

**Respuesta:**
```json
{
    "result": [
        {
            "COD_CCNO": "0021     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0068     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0000     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0067     ",
            "COD_SIDEBE": 1
        },
        {
            "COD_CCNO": "0000     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0066     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0055     ",
            "COD_SIDEBE": 1
        },
        {
            "COD_CCNO": "0055     ",
            "COD_SIDEBE": 0
        },
        {
            "COD_CCNO": "0067     ",
            "COD_SIDEBE": 1
        },
        {
            "COD_CCNO": "0007     ",
            "COD_SIDEBE": 0
        }
    ],
    "page": {
        "number": 1,
        "size": 50
    }
}
```

### Ejemplo con count

**Respuesta:**
```json
{
  "result": [
    {
      "COD_CCNO": "0021     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0068     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0000     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0067     ",
      "COD_SIDEBE": 1
    },
    {
      "COD_CCNO": "0000     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0066     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0055     ",
      "COD_SIDEBE": 1
    },
    {
      "COD_CCNO": "0055     ",
      "COD_SIDEBE": 0
    },
    {
      "COD_CCNO": "0067     ",
      "COD_SIDEBE": 1
    },
    {
      "COD_CCNO": "0007     ",
      "COD_SIDEBE": 0
    }
  ],
  "page": {
    "number": 1,
    "size": 50,
    "totalElements": 27173
  }
}
```

## Subir fichero (solo desarrollo)
**[POST]**

URL: http://localhost/bts/namespaces/{NAMESPACE}/files

*Namespace*: *namespace* aplicativo en el que se va a guardar el fichero.

**Body schema:**
```json
{
    "fileName": ["File", "required"]. Fichero local a subir.
}
``` 

Estos son los requisitos que debe cumplir la petición para subir el fichero:
 * Entorno del *namespace*: dev
 * Extensión del fichero: txt, csv

### Ejemplo

URL: <span>http://</span>localhost/bts/namespaces/`es.lrba.app-id-25276.dev`/files

**Body:**
```json
{
    "fileName": "result.csv"
}
```

**Respuesta:**
```json
{
    "btsFileKey": "result.csv",
    "requestId": "e14c4a7f-e8e1-4d4a-8c69-4edf01a9806d"
}
```
![PostmanBTSUploadFile](../resources/img/PostmanBTSUploadFile.png)


# developerexperience/06-BTSVisorJupyterLab.md
# Servicio *BTS Visor 2.0 (JupyterLab)*
El servicio *BTS Visor* está diseñado para lanzar consultas a ficheros almacenados en BTS.  

Es obligatorio solicitar unas credenciales para usar el servicio a través de *AppStream*.  

## Acceso a AppStream

### Gestión de credenciales
Las credenciales se deben solicitar a través del [portal de gestion de credenciales](https://bbva-credentials-vault.ew.r.appspot.com/#/personal/scality). Se debe especificar el **entorno**, **país** y la **UUAA** del *bucket* BTS al que se desea acceder. Se recibirá en el correo del usuario un correo electrónico confirmando el acceso.

![CredentialsManagement](../resources/img/CredentialsBTS.png)

**IMPORTANTE:** El código INC/CRQ se debe rellenar con un String cualquiera para los entornos de Work, pero para Live debe ser un código real. Este formulario se debe rellenar por cada entorno y país cuyos ficheros se quieran consultar.


### Ejecutar consultas contra el servicio

En el correo electronico mencionado anteriormente se indicará la url para acceder a AppStream. En ella, se abrirá una pestaña de Chrome con acceso al JupyterLab. 

![JupyterLab](../resources/img/btsVisor/jupyterLab.png)

En la parte izquierda, aparecerá una plantilla. Al abrirla, mostrará las instrucciones para la ejecución de las peticiones.

![TemplateJupyterLab](../resources/img/btsVisor/templateJupyterLab.png)


## Selección del bucket de lectura

Para consultar un fichero en BTS o Archive será necesario introducir el path completo donde se encuentra el fichero que se quiere consultar. Para ello, el bucket deberá seguir el siguiente patrón `{STORAGE_TYPE}-{REGION}-{GEOGRAPHY}-{FRESNO_SCOPE}`, donde:
 * STORAGE_TYPE: `bts` o `archive`.
 * REGION: `work-01`, `work-02`, `live-01`, `live-02`, etc.
 * GEOGRAPHY: `es`, `gl`, `mx`, `pe`, `co`, `ar`, etc.
 * FRESNO_SCOPE: código de 2 letras del ámbito Fresno al que pertenece la UUAA.

| Área | Código |
|------|--------|
| `Asset Management` | `am` |
| `Administración Productos y Servicios` | `ap` |
| `Básicos Comunes` | `bc` |
| `CIB` | `ci` |
| `Delivery` | `dy` |
| `Gestión Empresas` | `ge` |
| `Infraestructura Aplicativa y Datos` | `ia` |
| `Infraestructura` | `if` |
| `Informacional` | `in` |
| `Riesgos` | `ri` |


## Ejecución de ejemplo

Se modifica la plantilla para hacer una consulta de 20 registros de un fichero con los siguientes datos:
```
Nombre del fichero: labs/business-price.parquet (nombre real del fichero)
Bucket: bts-work-01-es-bc (obligatorio en minúsculas)
Entorno: dev (obligatorio en minúsculas)
UUAA: lrba (obligatorio en minúsculas)
```

A continuación se describen las sentencias para consultar el fichero mencionado:
```
df = spark.read.format("parquet").load("s3a://bts-work-01-es-bc/dev/lrba/labs/business-price.parquet")
```
```
df.show(20,False)
```

Una vez modificada la plantilla, por orden, se van seleccionando y ejecutando todas las instrucciones del fichero con el botón superior y se mostrará el resultado de la consulta. 

![TemplateJupyterLab](../resources/img/btsVisor/jupyterLabExec.png)

![TemplateJupyterLab](../resources/img/btsVisor/jupyterLabResult.png)

Para mas información sobre las consultas que se pueden realizar consulte la página de la [API de PySpark](https://spark.apache.org/docs/latest/api/python/reference/index.html).


## Subir ficheros

Este Visor BTS, Visor BTS 2.0 (JupyterLab), sólo se utilizará como servicio de consulta. Para la subida de ficheros, se seguirá utilizando el [Visor BTS 1.0 (Postman)](https://platform.bbva.com/lra-batch/documentation/06515c4c8f893adc1dab0bf2a14cb503/arquitectura-lrba/developer-experience/bts-visor-1-0-postman#content11).

