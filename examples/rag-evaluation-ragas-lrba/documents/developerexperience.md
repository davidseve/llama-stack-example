# developerexperience/01-HowToWork.md
# Herramientas de desarrollo

## Herramientas necesarias.

Lo primero que necesitamos para clonar el repositorio y subir las modificaciones a Bitbucket es Git.
El desarrollo se realiza en Java, por lo que es necesario tener instalado Java 17. Además, será necesario tener un IDE ya sea Eclipse, IntelliJ, Visual Studio Code, etc.
Por último, se recomienda usar el cliente LRBA, ya que es una herramienta que permite al desarrollador construir, probar y ejecutar en local los diferentes *jobs*.

## Git

Su uso es **obligatorio** para subir el código desarrollado a Bitbucket. Para realizar la [instalación](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) es necesario acceder a la página oficial y seguir la guía en función del Sistema Operativo.

Dentro de Git, la manera recomendada de gestionar las diferentes ramas de desarrollo es siguiendo [Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)

## Java IDEs

Eclipse es un IDE de código abierto, puede ser descargado siguiendo este [enlace](https://www.eclipse.org/downloads/packages/).

IntelliJ IDEA es otro IDE que recomendamos, su versión *Comunity* es gratuita y puede ser descargada desde [aquí](https://www.jetbrains.com/es-es/idea/download/).


Visual Studio Code es otro IDE gratuito muy extendido, lo pueden encontrar en su [página oficial](https://code.visualstudio.com/download).

## LRBA CLI

Este cliente permite compilar el *job*, ejecutar sus test unitarios y realizar ejecuciones locales.


### Cómo instalar

#### Windows
Hay dos opciones, la primera opción es modificar el *PATH* para que incluya la ruta al cliente LRBA, que estará disponible desde *Power Shell* o desde *CMD*. La otra opción es, cuando se quiera usar hay que ubicarse en la carpeta que lo contiene y abrir *Power Shell* o *CMD*.

##### Descarga

* [CLI - Windows 64](https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-generic-local/lrba/arch/go/cli/LATEST/windows/x86_64/lrba.exe)

**IMPORTANTE:** No uses la *VPN* mientras usas el cliente para evitar comportamientos inesperados.

#### Mac

Hay dos opciones, la primera opción es modificar el *PATH* para que incluya la ruta al cliente LRBA, que estará disponible desde la terminal. La otra opción es, cuando se quiera usar hay que ubicarse en la carpeta que lo contiene en la terminal.

##### Descarga

* [CLI - Mac x86_64/AMD64](https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-generic-local/lrba/arch/go/cli/LATEST/mac/x86_64/lrba)

* [CLI - Mac ARM64(Apple M1, M2, M3)](https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-generic-local/lrba/arch/go/cli/LATEST/mac/arm64/lrba)

**IMPORTANTE:** 
- Si se muestra el mensaje "*'lrba' can't be opened because it is from an unidentified developer*" al ejecutar el cliente, ejecutar el siguiente comando: `xattr -d com.apple.quarantine $pathToLrbaCli`.

- No uses la *VPN* mientras usas el cliente para evitar comportamientos inesperados. 

#### Linux

Hay dos opciones, la primera opción es modificar el *PATH* para que incluya la ruta al cliente LRBA, que estará disponible desde la terminal. La otra opción es, cuando se quiera usar hay que ubicarse en la carpeta que lo contiene en la terminal.

##### Descarga

* [CLI - Linux 64](https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-generic-local/lrba/arch/go/cli/LATEST/linux/x86_64/lrba)


### Configuraciones

La primera vez que se ejecute el cliente LRBA solicitará determinadas configuraciones.

El cliente guiará al usuario para que genere las claves y credenciales necesarias para un correcto funcionamiento. Las credenciales son:
 - **Artifactory**: Solicitará el nombre de usuario y la API Key.
 - **Bitbucket**: Solicitará un token de Bitbucket para poder acceder.
 - **Entorno**: El cliente puede crear el entorno (Java + Maven) si fuera necesario. En otro caso, se puede indicar la ruta de Java (*JAVA_HOME*) al igual que la ruta de Maven.

Estas configuraciones pueden ser modificadas posteriormente utilizando el comando `lrba config`. El propio cliente ofrece más información ejecutando el comando `lrba config --help`:

```
lrba config --help
Config the LRBA CLI

Usage:
lrba config [flags]

Flags:
-h, --help   help for config

Global Flags:
-p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
--skip-config    Skip initial CLI config. The use is not recommended.
```

Por defecto la configuración del cliente se hará en la ruta del usuario. En el caso de querer especificar una ruta distinta, se deberá definir en el sistema la variable de entorno 
`LRBA_CLI_CUSTOM_PATH` con el path completo donde se quiera instalar. 

### Init

Si se quieren realizar pruebas en local sin crear componentes en la consola Ether, usando el comando `lrba init` se genera el *scaffold* de un *job* LRBA. El comando solicitará la siguiente información:
 - **Lenguaje**: Lenguaje de programación que será usado en el Job, actualmente solo está disponible en Java.
 - **Tipo**: Tipo de *job*, actualmente solo se permite Spark.
 - **UUAA**: UUAA propietaria del *job*, tiene que cumplir el patrón `^[A-Z][A-Z0-9]{3}$`.
 - **País**: País donde se genera el *job*.
 - **Nombre**: Nombre del *job*.
 - **Versión**: Versión del *job*, por defecto será `00`.

El comando `lrba init --help` muestra más información sobre su uso.

```
lrba init --help
Creates a new LRBA job

Usage:
  lrba init [flags]

Flags:
  -h, --help                 help for init
  -n, --job-name string      Scaffold project's job name
  -l, --language string      Scaffold project's language (only java available)
  -o, --output-path string   Scaffold project's directory (default "~/Documents/Projects/LRBA/lrba_cli")
  -t, --type string          Scaffold project's type (only spark available)

Global Flags:
  -p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
      --skip-config    Skip initial CLI config. The use is not recommended.
```

### Build

El comando `lrba build` inicia la compilación del proyecto. Si la tecnología es Java, ejecutará el comando `mvn clean build`. Por defecto el comando ejecuta los test unitarios, si se quiere evitar hay que ejecutar `lrba build --skip-tests`.

Para más información relativa a este comando, ejecutar `lrba build --help`:
```
lrba build --help
Build LRBA job

Usage:
  lrba build [flags]

Flags:
  -h, --help                           help for build
      --Maven-repository-path string   Maven repository directory
      --project-path string            Project directory (default "~/Documents/Projects/LRBA/lrba_cli")
      --skip-tests                     Skip tests

Global Flags:
  -p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
      --skip-config    Skip initial CLI config. The use is not recommended.
```

### Test
Para ejecutar los test unitarios, es posible ejecutar `lrba test`. Si la tecnología es Java, ejecutará `mvn clean test`.
Por defecto, el comando anterior genera un informe de Jacoco, este se puede visualizar mediante `lrba test --open-coverage-report`.
La validación de cobertura se puede saltar ejecutando `lrba test --skip-coverage`. En este caso, no es necesario abrir el reporte de cobertura.

Para más información relativa a este comando, ejecutar `lrba test --help`:
```
lrba test --help
Test LRBA job

Usage:
  lrba test [flags]

Flags:
  -h, --help                           help for test
      --Maven-repository-path string   Maven repository directory
      --open-coverage-report           Open test coverage report (only if test coverage is enabled)
      --project-path string            Project directory (default "~/Documents/Projects/LRBA/lrba_cli")
      --skip-coverage                  Skip test coverage

Global Flags:
  -p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
      --skip-config    Skip initial CLI config. The use is not recommended.
```

### Run
Ejecutando el comando `lrba run` se solicitará la versión con la que se desea ejecutar.
Existe la posibilidad de saltar esta solicitud usando el flag `--arch-version` indicando la version de arquitectura con la que se quiere ejecutar.
Una vez indicada la versión, el cliente realizará las siguientes acciones:

 - **Compilación**: Si el proyecto usa Java, ejecutará el comando `mvn clean package`. Este comando además de compilar ejecuta los test unitarios, para no ejecutar los tests hay que usar `lrba run --skip-tests`.
 - **Ejecución**: Una vez el proyecto ha terminado de compilar, se ejecutará el *job*.

**IMPORTANTE**: Si se está ejecutando una versión antigua del cliente, se mostrará el siguiente error:
`[ERROR] open [JOB_PATH]/local-execution/deploymentConfig.properties.required: no such file or directory`.
Para solucionarlo  **crear dos ficheros vacíos** en la ruta `[JOB_PATH]/local-execution`: `deploymentConfig.properties.required` y `inputParameters.properties.required`.

En las secciones [Propiedades LRBA](../utilities/01-LRBAProperties.md) y [Parámetros de entrada](../utilities/02-LRBAInputParameters.md) se amplia la información sobre cómo usar ambas clases en pruebas locales.

Se puede obtener más información usando el comando `lrba run --help`:
```
lrba run --help
Run LRBA job

Usage:
  lrba run [flags]

Flags:
  -h, --help                           help for run
      --Maven-repository-path string   Maven repository directory
      --project-path string            Project directory (default "~/Documents/Projects/LRBA/lrba_cli")
      --skip-build                     Skip build phase
      --skip-tests                     Skip tests
      --arch-version                   Architecture version 

Global Flags:
  -p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
      --skip-config    Skip initial CLI config. The use is not recommended.
```

**NOTA**: Si al ejecutar el *job* en Windows se produce el siguiente error:
`Caused by: ExitCodeException exitCode=-1073741515: at org.apache.hadoop.util.Shell.runCommand(Shell.java:575)`,
significa que falta alguna librería del sistema. Es necesario descargar el siguiente paquete eligiendo el sistema operativo del que dispone (x64 o x86) y la versión 14.x en el siguiente [enlace](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

Se requieren permisos de administrador para instalar los paquetes, puede ser necesario contactar con el administrador del sistema.

### Configure-storage
El comando `lrba configure-storage` permite configurar diferentes fuentes de datos, los sistemas permitidos son: `file`, `db2`, `oracle`, `mongodb` y `elastic`:
 - **file**: Únicamente solicitará la ruta desde la cual se leerán y escribirán ficheros.
 - **db2**: Solicitará usuario, contraseña y cadena de conexión.
 - **oracle**: Solicitará usuario, contraseña y cadena de conexión.
 - **mongodb**: Solicitará usuario, contraseña, cadena de conexión y nombre de base de datos **sin** incluir el país.
 - **elastic**: Solicitará usuario, contraseña y cadena de conexión.
 

Al finalizar el proceso, el cliente indicará el `serviceName` que se debe utilizar dentro del código para las pruebas locales. Para más información, ejecutar el comando `lrba configure-storage --help`:

```
lrba configure-storage --help
configure-storage LRBA job

Usage:
  lrba configure-storage [flags]

Flags:
  -h, --help                  help for configure-storage
      --project-path string   Project directory (default "~/Documents/Projects/LRBA/lrba_cli")

Global Flags:
  -p, --proxy string   The proxy URL with format http://username:password@proxy-host:port
      --skip-config    Skip initial CLI config. The use is not recommended.
```

### Command flags

Todos los comandos tiene flags que modifican su comportamiento. Por ejemplo, si fuera necesario podemos indicar el proxy con el flag `-p or --proxy`.

Los comandos `config` e `init` admiten los siguientes flags
- `--project-path`: Si el proyecto se encuentra en un directo diferente al que nos encontramos en el cli.
- `--maven-repository-path`: Si se quiere utilizar un repositorio local de Maven diferente al por defecto(*USER_HOME/.m2*).

## Configuración de Maven

El cliente LRBA puede ser utilizado para compilar y ejecutar desde la línea de comandos. De no querer usarlo, o querer integrar el IDE para la resolución de dependencias, siempre se puede configurar el `settings.xml` de la siguiente manera.


```xml
<?xml version="1.0" encoding="UTF-8"?>

<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">

    <offline>false</offline>
    <pluginGroups>
    </pluginGroups>

    <servers>
        <server>
            <id>artifactory-LRBA-dev</id>
            <username>{YOUR_API_USER_FROM_ARTIFACTORY_VDC}</username>
            <password>{YOUR_API_KEY_FROM_ARTIFACTORY_VDC}</password>
        </server>
        <server>
            <id>artifactory-LRBA-release</id>
            <username>{YOUR_API_USER_FROM_ARTIFACTORY_VDC}</username>
            <password>{YOUR_API_KEY_FROM_ARTIFACTORY_VDC}</password>
        </server>
        <server>
            <id>mvn-central</id>
            <username>{YOUR_API_USER_FROM_ARTIFACTORY_VDC}</username>
            <password>{YOUR_API_KEY_FROM_ARTIFACTORY_VDC}</password>
        </server>
    </servers>

    <mirrors>
    </mirrors>

    <profiles>
        <profile>
            <id>lrbadev</id>
            <repositories>
                <repository>
                    <id>artifactory-LRBA-release</id>
                    <url>https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-maven-local</url>
                </repository>
                <repository>
                    <id>artifactory-LRBA-dev</id>
                    <url>https://artifactory.globaldevtools.bbva.com/artifactory/gl-lrba-maven-dev-local</url>
                </repository>
                <repository>
                    <id>mvn-central</id>
                    <name>mvn-central</name>
                    <url>https://artifactory.globaldevtools.bbva.com/artifactory/maven.org-remote</url>
                </repository>
            </repositories>
        </profile>

    </profiles>

    <activeProfiles>
        <activeProfile>lrbadev</activeProfile>
    </activeProfiles>

</settings>
```


# developerexperience/02-LocalDevelopment.md
# Desarrollo local
Si quieres saber como desarrollar un *job* con LRBA puedes consultar nuestros [Codelabs](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/).

# developerexperience/03-EtherConsoleDevelopment.md
# Desarrollo en Consola Ether

Crear un *job*, desarrollarlo y finalmente desplegarlo es muy sencillo utilizando la Consola Ether.

## Reglas

Antes de desplegar, echa un vistazo a las siguientes reglas:
* La rama *master* no existe. La rama por defecto es *develop*. Para proyectos que aún tengan la rama *master*, esta no será borrada pero no será utilizable.
* Las ramas permitidas son: *develop*, *feature/{}*, *release/X.Y*, *hotfix/*, *bugfix/\**.
* Cualquier rama que no coincida con la nomenclatura simplemente fallará en su construcción.
* Las ramas de *develop* y *release/X.Y* están protegidas y no se puede realizar la operación *commit* sobre ellas.
* El *pipeline* es el responsable de la validación de test unitarios, test de cobertura, calidad de código y seguridad.
* La cobertura no es obligatoria para las ramas *feature/{}* en el entorno de Desarrollo. Se entiende que bajo estas ramas y entorno el desarrollador está dando forma a la aplicación.
* La gestión de las ramas se hace completamente desde *git*/*bitbucket*:
	* El *release manager* estará a cargo de la generación de ramas y su fusión (*merge*).
	* La propagación automática de parches está habilitada desde las ramas de *release/X.Y* hacia *develop*.
* Cuando se generan ramas *release/X.Y* o fusionan *hotfix*/*bugfix* en ellas, automáticamente:
	* El *pom.xml* adapta la versión a X.Y.Z, donde:
		* X.Y coincide con el nombre de la rama de despliegue.
		* Z será incremental (empezando en 0), dependiendo del *hotfix*/*bugfix* que sea fusionado en ese despliegue.
	* Se genera una *tag* de acuerdo a la versión generada en el *pom.xml*
	* Se genera una versión en la consola Ether apuntando a la etiqueta.
* Todas las ramas, *commit* y etiquetas son deplegables en entornos previos, siempre y cuando la construcción de la aplicación haya finalizado correctamente.
* Las contrucciones de versiones actuales no pueden desplegarse con versiones antiguas de *pipelines*.
* **Los despliegues en Producción quedan restrigindos a TAGs.**

## Generar el Job

Primero, ve a la [Consola Ether](https://bbva-ether-console-front.appspot.com/app), y selecciona la aplicación donde se creará el *job*. Después de introducir la aplicación, el desarrollador verá algo similar a:

![Add resource](../resources/img/AddResource.png)

A continuación, haz clic en *ADD RESOURCE*. Se mostrará una ventana modal:

![Resource type](../resources/img/CreateResourceType.png)

Luego, selecciona *LRA.BATCH* en el tipo. Si no está habilitado, el arquitecto de soluciones del *namespace* debe habilitarlo manualmente.

El último paso es indicar el nombre del *job* que debe coincidir con la expresión regular `^([A-Z][A-Z0-9]{3})-([A-Z]{2})-JSPRK-([A-Z][_A-Z0-9]{1,15})-(V[0-9]{2})$`:

![Create job scaffold](../resources/img/CreateJobScaffold.png)

## Job en la Consola Ether

Después de crear el *job*, el desarrollador debería ver algo similar a esto:

![Job info](../resources/img/JobInfoEther.png)

Se observan una serie de enlaces que darán acceso al desarrollador a Bitbucket y Jenkins al *job*.

## Job en Bitbucket

Por defecto, se crea la rama *develop* con la estructura en la que se desarrollará el *job*:

![Job in Bitbucket](../resources/img/JobDevelopScaffold.png)

Puedes encontrar más información sobre la estructura de un *job* y como probarlo en local [aquí](./02-LocalDevelopment.md).

## Job en Jenkins

Después de crear el *job*, se dispara automáticamente el *pipeline* para la rama *develop*:

![Job in Jenkins](../resources/img/JobJenkins.png)

En Jenkins, el desarrollador puede ver si el *job* está compilando y verificar si pasa el estándar de cumplimento y calidad de LRBA.

## Despligue del job

**NOTA**: Todas las ramas, *commit* y etiquetas pueden ser desplegadas en entornos previos, siempre y cuando su construcción se haya completado satifactoriamente.

### Ejemplo de ID para un commit

En la consola Ether, dirigete a *release versions*:

![Job release versions](../resources/img/JobReleaseInfo.png)

Así que, primero, el desarrollador debe hacer clic en *CREATE RELEASE VERSION*:

![Create release version source](../resources/img/CreateReleaseVersionSource.png)

Para obtener el ID, ve al repositorio de Bitbucket y haz clic en *commits*:

![Bitbucket commit button](../resources/img/BitbucketCommitButton.png)

Después, selecciona la rama apropiada y copia el código *hash* del *commit*:

![Get commit ID](../resources/img/GetCommitID.png)

Pégalo en el cuadro de texto en la consola Ether y presiona siguiente: 

![Create release version source](../resources/img/CreateReleaseVersionSourceWithCommit.png)

Indica el nombre de la versión que va a ser desplegada y haz clic en *CREATE RELEASE VERSION*:

![Create release version source](../resources/img/CreateReleaseVersionName.png)

Finalmente, espera a que termine este paso ya que le puede tomar un tiempo en completarse:

![Release version created](../resources/img/CreateReleaseVersionDone.png)

Una vez creada la versión, el *job* puede ser desplegado haciendo clic en *DEPLOY* en el entorno adecuado:

![Deploying Job](../resources/img/DeployingJob.png)

Ahora, selecciona la versión que se ha creado y haz clic en *DEPLOY*:

![Deploying Job version](../resources/img/DeployingJobModal.png)

Se mostrará un modal con el progreso:

![Deploying Job version pipeline](../resources/img/DeployingJobModalWorking.png)

Finalmente, todos los marcadores se volverán verdes, y el *job* estará listo para ser planificado.
Ver [Planificación de *Jobs*](04-JobOrchestration/01-Introduction.md) para más detalles.

## Errores

### ID de commit incorrecto

Si el ID de *commit* especificado no existe, se mostrará el siguiente error cuando se despliegue la versión con el ID de *commit* incorrecto:

![Deploying Job version pipeline](../resources/img/WrongCommitIDError.png)

Se pueden encontrar los registros y detalles de los errores en [Atenea](https://platform.bbva.com/monitoring-console-atenea/documentation/1tv5Pox5rFPYXeSM1PEIeC_LCRO01A81LXObisobiw40/introduction) bajo el *namespace* de la UUAA.


# 04-JobOrchestration/01-Introduction.md
# Planificación de Jobs

Cualquier *job* LRBA debe ejecutarse utilizando cualquiera de los siguientes planificadores:

## Cronos

Una de las capacidades del servicio de [Cronos](https://platform.bbva.com/en-us/developers/cronos/documentation/what-is) es ser un Planificador como servicio. Para más detalles sobre cómo planificar un job LRBA consulte [Cronos Tasks - LRBA](https://platform.bbva.com/en-us/developers/cronos/documentation/tasks#h.z6lho5hk3ko9).

**IMPORTANTE**: Cronos sólo puede utilizarse en el entorno de Work. Para obtener más información sobre la planificación de un *job* en el entorno Live, consulte la sección Control-M a continuación.

## Control-M

Control-M simplifica la planficación de flujos de trabajo de aplicaciones y elimina cualquier esfuerzo manual para gestionar las actividades de garantía de calidad y recuperación asociadas, ofreciendo una mayor eficiencia para mantener su mainframe preparado para el futuro.  

Control-M puede utilizarse para programar *jobs* en Work y Live.  

Para obtener más información sobre cómo programar un job LRBA con Control-M:
- [España](02-Control-M_ES.md)
- [América](03-Control-M_MX.md)


# 04-JobOrchestration/02-Control-M_ES.md
# Control-M España

La planificación en Control-M consta de dos pasos:
- Definir el *job* y la cadena del *job* en el Gestor Documental.
- Abrir Remedy para solicitar la planificación en Control-M.

## Gestor Documental
Antes de empezar con la definición, es importante leer la [documentación del Gestor Documental](https://docs.google.com/document/d/1ln7Ih-yh25Tdmb_0SKXcKf-A6aBlRU7eorlSKu53vk8). En nuestra documentación nos centraremos únicamente en las particularidades de la arquitectura LRBA.  

### Jobs
Abra el [Gestor Documental](https://e-spacio.es.igrupobbva/WebGestDoc/in) y vaya a "JOBS" -> "Alta Jobs". Vera el siguiente formulario.
![DocumentManager](../../resources/img/DocumentManager.png)

**Nombre del script:** Rellenar con:  
`/app/lrba/lrba_launcher_controlm -job-name '%%jobnameLRA' -uuaa '%%uuaa' -namespace '%%namespace' -input-parameters '%%inputparameters'`  
Para ejecutar una versión específica del *job*, rellene con:  
`/app/lrba/lrba_launcher_controlm -job-name '%%jobnameLRA' -job-version '%%jobversion' -uuaa '%%uuaa' -namespace '%%namespace' -input-parameters '%%inputparameters'`  
Si no se especifica la versión del *job*, se ejecuta la versión activa, es decir, la última versión desplegada.  

**Jobname**: El nombre deseado con la nomenclatura sugerida en el *tooltip*.

**Grupo de soporte**: El grupo de soporte al que pertenece el dueño del *job*. **NO PONER LRBA**.

**Máquina origen**: Rellenar con "N/A".  

**Librería origen**: Rellenar con "N/A".  

**Descripción**: La descripción funcional del *job* y los valores de las variables del script.  
%%namespace={{NAMESPACE}}  
%%uuaa={{UUAA}}  
%%jobnameLRA={{JOB_NAME}}  

%%inputparameters=[{"key": "{{PARAM_NAME}}", "value": "{{VALUE}}"}]  
Si el job no tiene parámetros de entrada, rellene con:  
%%inputparameters=  

%%jobversion={{JOB_VERSION}} (Sólo si se ha rellenado el nombre del script con la versión del *job*).

**Sub.Aplicación:** A definir por la aplicación según la documentación del Gestor Documental.  

**Host de ejecución:** Rellenar con la ayuda de la siguiente tabla, según el entorno donde se está planificando el *job*.

**España**

|   entorno   |       host        |
|:-----------:|:-----------------:|
|     dev     |  de_lrba_es_work  |
|     int     |  ei_lrba_es_work  |
|     aus     |  au_lrba_es_work  |
|     oct     | octa_lrba_es_work |
|     pro     |  pr_lrba_es_live  |

**Global**

|   entorno   |       host        |
|:-----------:|:-----------------:|
|     dev     |  de_lrba_gl_work  |
|     int     |  ei_lrba_gl_work  |
|     aus     |  au_lrba_gl_work  |
|     oct     | octa_lrba_gl_work |
|     pro     |  pr_lrba_gl_live  |

**Criticidad:** A definir por la aplicación.

**Descripción de pasos - Ficheros y BBDD:** Esta sección es opcional, pero se recomienda rellenar los campos con las entradas y las salidas.

### Cadenas de jobs
Una vez definidos los *jobs*, se deben crear las cadenas que contiene el flujo de ejecución de los *jobs*. Vaya a "CADENAS" -> "Alta Cadenas".  
Dado que se trata de un formulario genérico en el que no existen peculiaridades de la arquitectura LRBA, no se explicará aquí cómo rellenarlo.  
Se recomienda leer la documentación del Gestor Documental y si tiene alguna duda abrir una incidencia/solicitud como se indica en la documentación. 

## Remedy
Abrir una solicitud de "PLANIFICACION EN BBDD DE CONTROL-M - RASSDD" indicando el enlace a la cadena del *job* en el Gestor Documental.  
Al tratarse de una solicitud de remedy genérica, no es objeto de esta documentación explicarla.


# 04-JobOrchestration/03-Control-M_MX.md
# Control-M América

## Pasos para la generación de jobs en Control-M

- Conexión a [Control-M](https://docs.google.com/document/d/1fOQSqkdYgStD3YTQup4I3lwDBPykcaWYQS6KNvhLvmE/edit#)
- Creación de Workspace/malla
- Creación de un nuevo Job

### Crear un nuevo Job

1. Crear un *Workspace*: en el menú *Home*, pulse el botón *Blank Workspace*.
2. Crear un Job: En el menú del *Workspace* seleccionar el botón *OS* y arrastrarlo a la plantilla del job en el *Workspace* generado.

<p align="left"> <img src="../../resources/img/JCM_1_nuevoJob.png">

3. Al soltarlo sobre el área de trabajo se solicitará en qué Control-M se definirá:

<p align="left"> <img src="../../resources/img/JCM_2_serverSelection.png">

- En caso de crear una malla para probar en Entornos Previos seleccionar **Ctrlm_Desarrollo**.
- En caso de crear una malla que se enviará a revisión para pasar a Producción, seleccione **CTM_CTRLMCCR**.

4. Finalmente, el nuevo *job* y la malla se mostrarán con algunos valores por defecto e información para completar.

<p align="left"> <img src="../../resources/img/JCM_3_jobMalla.png">

## Configurar Job

- **Job (LRBA).**  Pulsando con el botón derecho del ratón sobre el Job se puede ver la información a configurar en el *OS* tipo Job.

<p align="left"> <img src="../../resources/img/JCM_4_ConfiguraJob.png">

- Los campos que se detallan deben rellenarse con los datos indicados según las normas y ningún campo debe contener acentos o caracteres especiales, ya que esto puede dañar la integridad de la Base de Datos Control-M.

### Datos utilizados para la generación del Job LRBA

| Propiedad        |  Valor                  |
|:----------------:|:------------------------|
| Job Type         |  OS                     |
| Job Name         |  {{jobName}}            |
| Description      |  {{Description}}        |
| What             |  `Command`              |
| Command          |  `/app/lrba/lrba_launcher_controlm --namespace '{{namespace}}' --uuaa '{{UUAA}}' --job-name '{{jobName}}'  --input-parameters '[{"key": "{{key}}", "value": "{{value}}"}]'` |
| Host/Host Group  |  `{{Host/Node Group}}`  |
| Control-M Server |  `Ctrlm_Desarrollo`     |
| Run As           |  `lrba-ctm`             |
| Parent Folder    |  {{parentFolder}}       |
| Application      |  {{application}}        |
| SubAplication    |  {{subApplication}}     |

<p align="left"> <img src="../../resources/img/JCM_5_ConfiguraJob2.png">

**NOTA:** Al seleccionar *Command*, debe describirse el comando para ejecutar el job. Por ejemplo:

```
Launcher Path: 	 /app/lrba/lrba_launcher_controlm
Namespace:		'ar.lrba.app-id-25276.dev'
UUAA:			'LRBA'
Job-name:		'LRBA-GL-JSPRK-RW_FILE-V00'
```

Para la ejecución de los *jobs* y la visualización de resultados, consulte el site de [Control-M](https://sites.google.com/a/bbva.com/controlm-distribuido/liberar-jobs-nuevos#h.p_ID_50).


## Host/Host Group por país

**Argentina**

| entorno     |     host       |
|:-----------:|:--------------:|
|     dev     |  LRBA_AR_DESA  |
|     int     |  LRBA_AR_TEST  |
|     aus     |   LRBA_AR_QA   |
|     oct     |   LRBA_AR_QA   |
|     pro     |   LRBA_AR_PROD   |

**Colombia**

| entorno     |     host       |
|:-----------:|:--------------:|
|     dev     |  LRBA_CO_DESA  |
|     int     |  LRBA_CO_TEST  |
|     aus     |   LRBA_CO_QA   |
|     oct     |   LRBA_CO_QA   |
|     pro     |   LRBA_CO_PROD   |

**México**

| entorno     |     host       |
|:-----------:|:--------------:|
|     dev     |      LRBA      |
|     int     |      LRBA      |
|     aus     |      LRBA      |
|     oct     |      LRBA      |
|     pro     |      LRBA      |

**Perú**

| entorno     |     host       |
|:-----------:|:--------------:|
|     dev     |  LRBA_PE_DESA  |
|     int     |  LRBA_PE_TEST  |
|     aus     |  LRBA_PE_QA    |
|     oct     |  LRBA_PE_QA    |
|     pro     |  LRBA_PE_PROD  |

**Venezuela**

| entorno     |     host       |
|:-----------:|:--------------:|
|     dev     |  LRBA_VE_DESA  |
|     int     |  LRBA_VE_TEST  |
|     aus     |  LRBA_VE_QA    |
|     oct     |  LRBA_VE_QA    |
|     pro     |  LRBA_VE_PRO   |

# Recursos cuantitativos

Los Recursos Cuantitativos, son recursos que se definen para limitar la cantidad de jobs en ejecución en Control-M, 
es decir estos recursos permiten limitar el número de jobs LRBA por país / ambiente.

## Configuración Recursos Cuantitativos / Ambientes Previos

La configuración de esta propiedad se realiza en el detalle de generación de Jobs en el apartado de Prerrequisitos. 
En esta se debe de asignar el nombre del recurso cuantitativo generado por país de ejecución del job.

<p align="left"> <img src="../../resources/img/ConfRecCuantitativos.png">

**Resource Name:** Se indica el nombre del recurso definido por Administración.
**Required Quantity:** Se indica la cantidad de recursos que se quieren utilizar del total definido por el Administrador

Los recursos generados para la ejecución de Jobs en Control-; para Pasarelas LRBA América de Entornos Previos son:

|   Pais    |        Recurso        | 
|:---------:|:---------------------:|
|  Global   | MAX-LRA_BATCH-WORK    |
| Argentina | MAX-LRA_BATCH-WORK-AR |
| Colombia  | MAX-LRA_BATCH-WORK-CO |   
|  México   | MAX-LRA_BATCH-WORK-MX |
|   Perú    | MAX-LRA_BATCH-WORK-PE |
| Venezuela | MAX-LRA_BATCH-WORK-VE |

## Configuración Recursos Cuantitativos / Producción

La configuración de esta propiedad se realiza en el XML (Malla a ejecutar en Producción). En esta se debe de asignar el nombre 
del recurso cuantitativo generado por país de ejecución del job.

Ejemplo de configuración en malla 'XML'

<p align="left"> <img src="../../resources/img/ConfRecCuantitativosMalla.png">

Los recursos generados para ejecución de jobs en Control-M para Pasarelas LRBA América para producción son:

|   Pais    |        Recurso        | 
|:---------:|:---------------------:|
|  Global   | MAX-LRA_BATCH-LIVE    |
| Argentina | MAX-LRA_BATCH-LIVE-AR |
| Colombia  | MAX-LRA_BATCH-LIVE-CO |   
|  México   | MAX-LRA_BATCH-LIVE-MX |
|   Perú    | MAX-LRA_BATCH-LIVE-PE |
| Venezuela | MAX-LRA_BATCH-LIVE-VE |

Para mas detalle, consultar [Recursos_Cuantitativos](https://docs.google.com/document/d/1mgiu_pug7eFdf_JXtXKSmNaHXpPJXtDrZuj4inM-OOA/edit) 



# developerexperience/05-ReadingJobLogs.md
# Job logs

## Introducción

[Atenea](https://platform.bbva.com/monitoring-console-atenea/documentation/1tv5Pox5rFPYXeSM1PEIeC_LCRO01A81LXObisobiw40/introduction) es una consola de monitorización que te permite acceder a la información de los servicios *Ether Cloud*, en este caso a los logs del *Job* de LRBA. Los logs se agrupan en *monitored resources* y trazas.

Las trazas permiten a los desarrolladores rastrear la ruta de ejecución de las diferentes operaciones que tienen lugar en el flujo del proceso.

Un *monitored resource* es una fuente de datos de monitorización.

## LRBA Job logs

Para ver los *logs* del *job*, debemos acceder a Atenea. La URL depende de la VPN que se esté utilizando y del entorno (Work/Live). Encuentre la correcta [aquí](https://platform.bbva.com/monitoring-console-atenea/documentation/1S2AMheKmpZ5zD0-Uaq2aeHCfbJvTEIQPKSmYNZxcum4/accessing-the-console).

Después de acceder, el desarrollador verá algo similar a esto:

![Atenea Home](../resources/img/AteneaHome.png)

En esa pantalla, parece que no es posible ver trazas o *logs*, pero que no cunda el pánico,
eso es porque los usuarios sólo tienen permisos para ver los *logs* de su UUAA.

Para ver los *logs*, pincha en el enlace *MONITORED RESOURCES*. Aparecerá una pantalla muy similar a esta:

![Atenea Monitored Resources](../resources/img/AteneaMonitoredResources.png)

**IMPORTANTE**: selecciona el *namespace* correcto (en función del entorno lógico y el país `{COUNTRY}.ether.lrba.apps.{ENVIRONMENT}`).
Actualmente existen los siguientes *namespaces*:

***Work***

*Global*
- gl.ether.lrba.apps.dev
- gl.ether.lrba.apps.int
- gl.ether.lrba.apps.au
- gl.ether.lrba.apps.qa

*España*
- es.ether.lrba.apps.dev
- es.ether.lrba.apps.int
- es.ether.lrba.apps.au
- es.ether.lrba.apps.qa

*América*

| ENTORNOS                   |         México         |       Argentina        |          Perú          |        Colombia        |
|:--------------------------:|:----------------------:|:----------------------:|:----------------------:|:----------------------:|
| **Desarrollo**            | mx.ether.lrba.apps.dev | ar.ether.lrba.apps.dev | pe.ether.lrba.apps.dev | co.ether.lrba.apps.dev |
| **Test**                  | mx.ether.lrba.apps.int | ar.ether.lrba.apps.int | pe.ether.lrba.apps.int | co.ether.lrba.apps.int |
| **Calidad**               | mx.ether.lrba.apps.au  | ar.ether.lrba.apps.au  | pe.ether.lrba.apps.au  | co.ether.lrba.apps.au  |
| **Certificación técnica** | mx.ether.lrba.apps.qa  |  a.ether.lrba.apps.qa  | pe.ether.lrba.apps.qa  | co.ether.lrba.apps.qa  |

***Live***

*Global*
- gl.ether.lrba.apps.pro

*España*
- es.ether.lrba.apps.pro

*América*

| ENTORNOS        |         México         |       Argentina        |          Perú          |        Colombia        |
|:---------------:|:----------------------:|:----------------------:|:----------------------:|:----------------------:|
| **Producción** | mx.ether.lrba.apps.pro | ar.ether.lrba.apps.pro | pe.ether.lrba.apps.pro | co.ether.lrba.apps.pro |


Como se puede ver en la captura de pantalla, se muestran los *monitored resources* en los que el usuario tiene permisos. Además, para cada uno de ellos se muestran los enlaces de *Traces* y *Logs*.

![Atenea MR Logs](../resources/img/AteneaMRLogsReduced.png)

### Trazas

![Atenea Traces](../resources/img/AteneaSpanList.png)

Para cada *job* se generan varias trazas. La más importante es la que tiene el mismo nombre que el *job*.
Esto se debe a que contiene cualquier otro *span* asociado al *job*:

![Atenea Full Trace Example](../resources/img/AteneaFullTraceExample.png)

A continuación, es posible hacer clic en cualquier otra traza y ver información detallada sobre ella.

En la parte inferior derecha de la traza, los desarrolladores pueden hacer clic en *LOGS* y ver todos los *logs* relacionados.
Por defecto, las vistas de los *logs* están restringidas. 

![Atenea Full Trace Permission](../resources/img/AteneaLogInTracePermission.png)

Inserte el filtro `and mrId = "{YOUR_UUAA}` en el cuadro de búsqueda para obtener permisos para ver los *logs*.  
**IMPORTANTE:** Asegúrese de que hay espacios en blanco entre el texto y "=".

![Atenea Full Trace Success](../resources/img/AteneaLogInTraceSuccess.png)


### Logs

La sección *LOGS* muestra los *logs* ordenados por fecha de creación. Todos los *logs* asociados al *monitored resource* (UUAA en este caso) se muestran aquí. Al igual que en el caso de los *spans*, es posible filtrar los *logs* por fecha y otras opciones.

![Atenea Logs](../resources/img/AteneaLogList.png)


## Crear job logs

Es posible escribir *logs* personalizados. El desarrollador sólo tiene que importar la clase *logger* apropiada utilizando *SLF4J*:

```java
private static final Logger LOGGER = LoggerFactory.getLogger({JobBuilderName}.class); // Replace JobBuilderName with the Job builder class name
```
A continuación, escriba los *logs* utilizando el nivel de *logs* adecuado: 
```java
LOGGER.debug("Working in {} mode", workingMode);
```
Es importante que, si los desarrolladores escriben *logs*, éstos sean útiles, concisos y estén escritos en el nivel de *logs* adecuado.

## Pipeline logs

Aquí se pueden encontrar los *logs* de los *pipelines*, dependiendo de la geografía:
- Global: [Jenkins](https://globaldevtools.bbva.com/je-mm-gl-apps-lrba/)
- Spain: [Jenkins](https://globaldevtools.bbva.com/je-mm-es-apps-lrba/)

Introduzca el *namespace* adecuado. A continuación, abra el *job* de Jenkins (el nombre será el mismo que el nombre del *job* LRBA).
Finalmente, abra la rama y la *build* para ver los logs en *Console Output*.

![Jenkins Logs](../resources/img/JenkinsConsoleOutputReduced.png)

## Deployer logs

Al crear una nueva *release version*, se realizan varias tareas antes de publicar realmente esa *release version*. En algunos casos, esta operación puede fallar.
Los *logs* sobre lo ocurrido y el *span* en el que se agrupan se pueden encontrar en el *namespace* de la UUAA correspondiente en Atenea.
Ejemplo: 
`es.{UUAA}.app-id-{ID}.dev`

![Atenea Deployer Logs](../resources/img/AteneaDeployerLogs.png)

## Buenas prácticas

Al buscar *logs* en Atenea, lo mejor es usar filtros de fecha. Intente averiguar cuándo se produjo el problema y filtre por esa fecha. Como resultado, sólo se mostrarán los *logs* relevantes y encontrar la causa raíz del problema será más fácil.

También, encontrar *logs* a través del *span* padre es una buena manera de ver sólo los *logs* relevantes.

Atenea soporta varios filtros que también pueden ayudar a encontrar lo que se está buscando. Algunos filtros útiles son:
- `mrId=='kbtq'` Se aplican automáticamente al acceder a *logs* o trazas a través de la sección de *monitored resources*. **IMPORTANTE** no elimines este filtro porque se mostrará un error de permisos si no está presente.
- `message=='*kbtq*'` Filtra los *logs* que contengan `kbtq` en algún lugar. `*` funciona de forma similar a `%`, en SQL el comparador *like*.
- `properties.runId=='ab1e2191-cf89-4ceb-9ad5-35a67d02a41d'` Filtra los *logs* asociados al runId `ab1e2191-cf89-4ceb-9ad5-35a67d02a41d`.
Este filtro funciona utilizando cualquiera de las propiedades asociadas al *log* o *span*.
- `level=='ERROR'` Muestra sólo los *logs* con nivel *ERROR*.

Se pueden aplicar varios filtros a la vez. Se pueden concatenar usando `AND`. Ejemplo: `mrId=='kbtq' AND message=='*kbtq*'`

## Abrir una incidencia
Al abrir una incidencia, es muy importante que los desarrolladores encuentren primero los mensajes de *logs* que indican el motivo del fallo.
Puede tratarse de un fallo del *job* y no de un problema relacionado con la arquitectura.

Si es un fallo de la arquitectura o un fallo desconocido, es **obligatorio** indicar el runId del *job*. Se puede encontrar en la Consola LRBA.
También puede extraerse de los *logs* del *job*, ya que es una propiedad:

![Atenea log runId property](../resources/img/AteneaLogRunIdProperty.png)


# developerexperience/07-SonarRules.md
# Reglas Sonar
Se han definido reglas Sonar que impiden el uso de:
* Configuraciones internas de Spark, acceso al *SparkSession* y *SparkContext*.
* Descargar la información en el *driver* en lugar de en los *executors*.
* Ejecución de acciones por fuera de los *targets* definidos.


La lista de los métodos no permitidos con la clase a la que van asociados es la siguiente:

|    Class     | Method                          |
|:------------:|:--------------------------------|
|   Dataset    | `cache`                         |
|   Dataset    | `checkpoint`                    |
|   Dataset    | `collect`                       |
|   Dataset    | `collectAsList`                 |
|   Dataset    | `createGlobalTempView`          |
|   Dataset    | `createOrReplaceGlobalTempView` |
|   Dataset    | `createOrReplaceTempView`       |
|   Dataset    | `createTempView`                |
|   Dataset    | `describe`                      |
|   Dataset    | `foreach`                       |
|   Dataset    | `foreachPartition`              |
|   Dataset    | `head`                          |
|   Dataset    | `hint`                          |
|   Dataset    | `inputFiles`                    |
|   Dataset    | `javaRDD`                       |
|   Dataset    | `localCheckpoint`               |
|   Dataset    | `observe`                       |
|   Dataset    | `ofRows`                        |
|   Dataset    | `persist`                       |
|   Dataset    | `rdd`                           |
|   Dataset    | `registerTempTable`             |
|   Dataset    | `show`                          |
|   Dataset    | `sparkSession`                  |
|   Dataset    | `sqlContext`                    |
|   Dataset    | `stat`                          |
|   Dataset    | `summary`                       |
|   Dataset    | `tail`                          |
|   Dataset    | `take`                          |
|   Dataset    | `takeAsList`                    |
|   Dataset    | `toJavaRDD`                     |
|   Dataset    | `toLocalIterator`               |
|   Dataset    | `unpersist`                     |
|   Dataset    | `write`                         |
|   Dataset    | `writeStream`                   |
|   Dataset    | `writeTo`                       |
|||
| SparkSession | `static active`                 |
| SparkSession | `static builder`                |
| SparkSession | `static clearActiveSession`     |
| SparkSession | `static clearDefaultSession`    |
| SparkSession | `static getActiveSession`       |
| SparkSession | `static getDefaultSession`      |
| SparkSession | `static setActiveSession`       |
| SparkSession | `static setDefaultSession`      |
|||
| SparkContext | `static getOrCreate`            |


Asimismo, hay otros que se pueden usar valorando su impacto en casos muy concretos y controlados si no hay otra alternativa. 
Es por ello que generan una advertencia en lugar de un error. La lista de métodos permitidos, pero no recomendados, con la clase a la que corresponden es la siguiente:


|  Class  | Method    |
|:-------:|:----------|
| Dataset | `count`   |
| Dataset | `first`   |
| Dataset | `isEmpty` |

# developerexperience/08-TestAndJacoco.md
# Cobertura de test y Jacoco

Cuando se ejecuta un *pipeline* al subir un proyecto, hay un paso llamado *Test and Coverage* que ejecuta todas las
pruebas y comprueba si cumplen con la cobertura mínima del código. Una vez hecho esto es importante saber que:
- En el *pipeline*, Sonar sólo muestra la cobertura alcanzada pero no bloquea.
- En el *pipeline* es Jacoco quien bloquea.

## Error de cobertura
Cuando se produce un error de cobertura en el paso *Test and Coverage*, la ventana del *pipeline* se vuelve naranja
indicando que hay un problema, aunque el resto de los pasos del *pipeline* se ejecutan.

![TestAndCoverageError](../resources/img/TestAndCoverageError.png)

Si queremos ver la cobertura conseguida tenemos que comprobar los *logs*. Para ello pulsamos sobre el signo de exclamación de la imagen y buscamos el *log* que contiene el error. Esta información se puede encontrar ejecutando el comando `mvn -U verify -q -s $settingsMvn` que abrirá el mensaje correspondiente. Es importante saber que sólo indica que no se ha superado la cobertura, **no el porcentaje de cobertura**.

![*Pipeline*CoverageError](../resources/img/PipelineCoverageError.png)

## Cobertura en clase de constantes
En algunos casos se utilizan clases para definir constantes y cuando se pasan los test Jacoco las marca como no testeadas
aunque se estén usando en el *Builder* o en el *Transform*. Esto ocurre porque Jacoco necesita un método al que entrar
para marcar la clase como testeada. Para solucionar este inconveniente lo más fácil es crear un constructor privado y 
que esté vacío. Con ese constructor entiende que no hay nada que hacer en esa clase de constantes y la ignora en el 
informe de cobertura. 

## Test en local
Cuando desee ver la cobertura alcanzada en las pruebas, deberá ejecutarlas localmente. Para ello, con el
[LRBA CLI](https://platform.bbva.com/lra-batch/documentation/f4ed8e8cc8c4fe2408149394b9ee9be9/lrba-architecture/developer-experience/how-to-work#content4) instalado, ejecutamos el comando `lrba test --open-coverage-report`. En caso de no alcanzar la **cobertura mínima de 0,80** al ejecutar todas las pruebas, veremos un error como el siguiente:

![CoverageError](../resources/img/CoverageError.png)

El siguiente paso sería buscar las líneas de código que faltan. Para ello tendríamos que abrir el informe Jacoco que se ha generado en la carpeta de destino de nuestro proyecto, donde la ruta es `target/site/jacoco/index.html`. Una vez abierto, podemos navegar por los diferentes ficheros de código para ver la cobertura donde encontraremos las líneas marcadas con diferentes colores:
- Verde: Se ha cubierto correctamente.
- Amarillo: Parcialmente cubierto. Por ejemplo, sólo se ha evaluado una rama de un if.
- Rojo: La línea no está cubierta.


# developerexperience/09-StaticResources.md
# Recursos Staticos del LRBA

Algunas aplicaciones pueden necesitar recursos externos como archivos HTML, XML o JSON para ejecutar la logica del proceso requerida. Hay dos tipos de recursos estáticos:
 * **Recursos gobernados**: Estos recursos comprenden diferentes archivos alojados en un repositorio de Bitbucket. Todo su ciclo de vida se gestiona por LRBA en el entorno Ether.
 * **Ungoverned resources**: El contenido de estos recursos es generado fuera de los ciclos de vida de LRBA. El contenido de los recursos no será almacenado en Bitbucket, debera ser almacenado en Artifactory.

## Crear un Proyecto

Usando el siguiente flujo de trabajo, la herramienta *stackcoder* generará un recurso básico en el repositorio de un proyecto dado.

Necesita conectarse a [Consola Ether](https://bbva-ether-console-front.appspot.com/app)

Acceda a su aplicación, `ADD RESOURCE...` y seleccione `LRA.BATCH.STATICS`

*Ejemplo de creación de un Recurso Gobernado:*

![Crear un nuevo Recurso](../resources/img/static-resources/StaticResourceCreation.png)

![Create nuevo recurso Gobernado](../resources/img/static-resources/GovernedResourceCreation.png)

![Recurso Gobernado Creado](../resources/img/static-resources/GovernedResourceRepositoryCreation.png)


*Repositorio:*

![Crear nuevo Recurso](../resources/img/static-resources/GovernedResourceNewRepo.png)


*Ejemplo de creación de recurso no gobernado:*


![Crear nuevo Recurso](../resources/img/static-resources/UngovernedResourceCreation.png)

![Crear nuevo Recurso Gobernado](../resources/img/static-resources/UngovernedResourceRepositoryCreation.png)


*Repositorio:*

![Crear nuevo Recurso](../resources/img/static-resources/UngovernedResourceNewRepo.png)


Los permisos sobre la rama de este repositorio son exactamente el mismo que de los *jobs*. Para subir nuevos recursos tendrá que abrir una nueva rama *feature*, hacer los cambios, y luego juntarlos con la rama *develop*. Finalmente, generar una rama *release/x.y*.

### Añadir recursos a los repositorios

 * **Recurso Gobernado**: Sólo se necesita añadir archivos al repositorio de Bitbucket.
 * **Recurso No Gobernado**: Modificar el descriptor de fichero .yml siguiendo este ejemplo:
    * artifactoryType: Hace referencia a los diversos Artifactorys proporcionados por GDT. Puede ser *Stock* o *VDC*.
    * repository: Complete la ruta al recurso.
    * artifact: Nombre del recurso no gobernado en Artifactory.


![Crear nuevo Recurso](../resources/img/static-resources/descriptor.png)

### Compilar Código

Una vez que los archivos han sido subidos a la rama apropiada comprueba la compilación en `jenkins`.

![Funcionalidad recurso gobernado en Jenkins](../resources/img/static-resources/GovernedResourceBuild.png)


### Crear Version de Despliegue


Después de que se haya hecho el compilado, tienes que crear una versión de despliegue. Hay tres formas de hacerlo:

![Botón Nueva Versión](../resources/img/static-resources/NewVersionButton.png)

![Botón Nueva Versión](../resources/img/static-resources/NewVersionByBranch.png)

![Botón Nueva Versión](../resources/img/static-resources/NewVersionName.png)

![Botón Nueva Versión](../resources/img/static-resources/NewVersionCreated.png)


### Versión de Despliegue

![Nueva versión Recurso Gobernado](../resources/img/static-resources/DeployButton.png)

![Nueva versión Recurso Gobernado](../resources/img/static-resources/DeployVersion.png)

![Nueva versión Recurso Gobernado](../resources/img/static-resources/Deployed.png)


## Configuración del Job

Enlace el nuevo recurso, al Job LRBA Spark que lo necesite. Tienes que crear un archivo `required_resources.yml` en tu *job*.

![carpeta de job](../resources/img/static-resources/JobFolder.png)

El archivo debe tener esta estructura. Una línea por recurso:

```yml
- name: RESOURCE_REPOSITORY_1
- name: RESOURCE_REPOSITORY_2
```

*ejemplo:*
```yml
- name: LRBA-ES-GOVRS-REPO4-V00
- name: LRBA-ES-UNGRS-REPO4-V00
```

## Uso de Recursos

En tiempo de ejecución puedes acceder a tus recursos **SÓLO** desde los ***executors* de Spark**, la ruta a los recursos es dada por `lrbaProperties.get("RESOURCES_PATH")+/$RESOURCE_REPOSITORY`. 

*Ejemplo de uso*:

```java
    @Override
    public Map<String, Dataset<Row>> transform(Map<String, Dataset<Row>> inputDatasets) {
        Dataset<Row> customers = inputDatasets.get("customers");
        Dataset<Row> response = customers.map((MapFunction<Row, Row>) row -> {
            String clientCode = row.getAs("CLIENT_CODE");
            String bankId = row.getAs("BANK_ID");
            String pdf = Singleton.getInstance()
                    .getFileContent()
                    .replace("$cclient", clientCode)
                    .replace("$bank", bankId);
            return RowFactory.create(clientCode, bankId, pdf);
        }, Encoders.row(new StructType(new StructField[]{
                new StructField("CLIENT_CODE", StringType, true, Metadata.empty()),
                new StructField("BANK_ID", StringType, true, Metadata.empty()),
                new StructField("PDF", StringType, true, Metadata.empty())
        })));
        Map<String, Dataset<Row>> datasetsToWrite = new HashMap<>();
        datasetsToWrite.put("response", response);
        return datasetsToWrite;
    }
```
*Clase Singleton:*
```java

public class Singleton implements Serializable {
    private static Singleton instance = null;

    public String getFileContent() {
        return fileContent;
    }

    private String fileContent;
    private LRBAProperties lrbaProperties = new LRBAProperties();

    private Singleton() {
        String staticResource = lrbaProperties.get("RESOURCES_PATH") + "/LRBA-ES-GOVRS-REPO4-V00";
        String pdfBlueprint = staticResource + "/blueprint.html";
        try {
            this.fileContent = new String(Files.readAllBytes(Paths.get(pdfBlueprint)), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public static Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}

```


# 10-FileWatcher/01-Introduction.md
# BTS FileWatcher

Es un servicio que permite monitorizar los ficheros del BTS haciendo de integración entre este y Control-M. La idea de
esta herramienta es ayudar en la migración de Epsilon a BTS mediante la monitorización de la creación de los ficheros.

Para hacerlo funcionar, el *filewatcher* recibe una serie de parámetros de entrada o *flags*. Estos son muy importantes 
porque contendrán los datos del fichero a monitorizar. Los parámetros y sus características son las siguientes:

- ***country:*** Geografía del fichero. Dos letras. Ejemplo: es, gl, mx...
- ***environment:*** Entorno en el que se ejecuta. Ejemplo: dev, int, oct, aus, pro.
- ***uuaa:*** UUAA del fichero en mayúscula.
- ***file-name:*** Nombre del fichero a buscar. Permite el uso de wildcards solamente en el sufijo de un path o específicamente en el nombre del archivo.
- ***partitioned:*** Indica si el fichero está particionado o no. Posibles valores: Y / N. Este parámetro es muy
importante a la hora de buscar y evitar errores.
- ***polling-ttl (OPCIONAL):*** Tiempo máximo de polling expresado en segundos. El tiempo máximo de polling son 6 horas,
el usuario puede poner menos expresándolo en segundos. Si es superior se baja a 6 horas.
- ***age-of-file:*** Indica el tiempo en segundos que el *filewatcher* utiliza para buscar cuando se creó o modificó el archivo. Valor predeterminado: 0 segundos
- ***service:*** Parámetro que indica el origen de datos donde se monitorizarán los archivos. Valor predeterminado *bts*. Valores posibles: *bts*, *bea_deadletter*.

## Lógica del servicio

El *filewatcher* de LRBA tiene la siguiente lógica de ejecución:

1. Lee el archivo de configuración para recuperar las URL y las credenciales.
2. Lee los *flags* para monitorizar el archivo.
3. Se ejecuta el job, obteniendo un código diferente para cada estado:
    - 0: Archivo encontrado.
    - 255: Se ha superado el tiempo de polling y no se ha encontrado el fichero.
    - 157: Estado desconocido.

Además, cada registro se envía a Atenea.

Cuando se quiera usar este servicio, se ha de planificar mediante Control-M. Para obtener más información sobre cómo 
programar un job LRBA FileWatcher con Control-M:

- [España](02-FileWatcher_ES.md)

- [América](03-FileWatcher_MX.md)


# 10-FileWatcher/02-FileWatcher_ES.md
# BTS FileWatcher España y Global

La planificación en Control-M consta de dos pasos:
- Definir el *job* y la cadena del *job* en el Gestor Documental.
- Abrir Remedy para solicitar la planificación en Control-M.

## Gestor Documental
Antes de empezar con la definición, es importante leer la 
[documentación del Gestor Documental](https://docs.google.com/document/d/1ln7Ih-yh25Tdmb_0SKXcKf-A6aBlRU7eorlSKu53vk8). 
En nuestra documentación nos centraremos únicamente en las particularidades de la arquitectura LRBA.

### Jobs
Abra el [Gestor Documental](https://e-spacio.es.igrupobbva/WebGestDoc/in) y vaya a "JOBS" -> "Alta Jobs". Vera el siguiente formulario.
![DocumentManager](../../resources/img/DocumentManager.png)

**Nombre del script:** Rellenar con:  
`/app/lrba/lrba_script_fw -country '%%country' -environment '%%environment' -file-name '%%filename' -uuaa '%%uuaa' -partitioned '%%partitioned'`  
Para ejecutar informando TTL::  
`/app/lrba/lrba_script_fw -country '%%country' -environment '%%environment' -file-name '%%filename' -uuaa '%%uuaa' -partitioned '%%partitioned' -polling-ttl '%%pollingttl'`

**Jobname**: El nombre deseado con la nomenclatura:
- {{UUAA}}97{{XX}}\_{{TEXTO_LIBRE}}\_FW\_{{EE}} (Entornos Previos), 
- {{UUAA}}97{{XX}}\_{{TEXTO_LIBRE}}\_FW (Producción). 

  - UUAA: La UUAA aplicativa.
  - XX: Debe ser un nuevo secuencial en función de los envíos necesarios.
  - TEXTO_LIBRE: Podrá ser una descripción personalizada.
  - EE: El entorno en el que se va a ejecutar el job (DE, EI, AU, QA).

Ejemplo: ZZZZ9701_BUSCAR_ENTRADA_FW_DE

**Grupo de soporte**: El grupo de soporte al que pertenece el dueño del *job*. **NO PONER LRBA**.

**Máquina origen**: Rellenar con "N/A".

**Librería origen**: Rellenar con "N/A".

**Descripción**: Los valores de las variables del script y los recursos cuantitativos. 
- %%country={{COUNTRY}} (*País de ejecución, formato de dos letras, ej: es, gl, etc.*)
- %%environment={{ENVIRONMENT}} (*Entorno de ejecución: dev, int, oct, aus, pro*)
- %%filename={{FILE_NAME}}(*Nombre del fichero*)
- %%uuaa={{UUAA}}(*UUAA propietaria del fichero*)
- %%partitioned={{Y|N}}(*Indica si el fichero está particionado o no, si se indica mal este parámetro **no funcionará el filewatcher***)
- %%pollingttl={{TTL}} (*Opcional. Tiempo expresado en segundos que estará activo el filewatcher, por defecto 3600(1 hora), el valor máximo es 21600(6 horas)*)
- Recursos cuantitativos:
  - Entornos previos España
    * MAX-LRBA_BTS_FW-WORK
    * MAX-LRBA_BTS_FW-WORK-ES
  - Entornos previos Global
    * MAX-LRBA_BTS_FW-WORK
    * MAX-LRBA_BTS_FW-WORK-GL
  - Producción España
    * MAX-LRBA_BTS_FW-LIVE
    * MAX-LRBA_BTS_FW-LIVE-ES
  - Producción Global
    * MAX-LRBA_BTS_FW-LIVE
    * MAX-LRBA_BTS_FW-LIVE-GL

**Sub.Aplicación:** A definir por la aplicación según la documentación del Gestor Documental.

**Host de ejecución:** Rellenar con la ayuda de la siguiente tabla, según el entorno donde se está planificando el *job*.

**España**

|   entornos   |       host        |
|:------------:|:-----------------:|
|     dev      |  de_lrba_es_work  |
|     int      |  ei_lrba_es_work  |
|     aus      |  au_lrba_es_work  |
|     oct      | octa_lrba_es_work |
|     pro      |  pr_lrba_es_live  |

**Global**

|   entornos   |       host        |
|:------------:|:-----------------:|
|     dev      |  de_lrba_gl_work  |
|     int      |  ei_lrba_gl_work  |
|     aus      |  au_lrba_gl_work  |
|     oct      | octa_lrba_gl_work |
|     pro      |  pr_lrba_gl_live  |

**Criticidad:** A definir por la aplicación.

### Cadenas de jobs
Una vez definidos los *jobs*, se deben crear las cadenas que contiene el flujo de ejecución de los *jobs*. 
Vaya a "CADENAS" -> "Alta Cadenas". Dado que se trata de un formulario genérico en el que no existen peculiaridades de 
la arquitectura LRBA, no se explicará aquí cómo rellenarlo. Se recomienda leer la documentación del Gestor Documental y 
si tiene alguna duda abrir una incidencia/solicitud como se indica en la documentación.

## Remedy
Abrir una solicitud de "PLANIFICACION EN BBDD DE CONTROL-M - RASSDD" indicando el enlace a la cadena del *job* en 
el Gestor Documental. Al tratarse de una solicitud de remedy genérica, no es objeto de esta documentación explicarla.

Adicionalmente hay que indicar que para entorno de Producción se requiere de autorización a través de cambio CRQ
relacionado y autorizado a la petición.

Para entornos previos no será necesario ningún CRQ.

# 10-FileWatcher/03-FileWatcher_MX.md
# BTS FileWatcher América

La programación de un Job LRBA Filewatcher para ambientes previos se realiza asignando el script de ejecución desde el campo "Comando" de la herramienta Control-M.
En el script se indica el fichero al que se requiere monitorizar su carga en tiempo real. 

## Nombre del script.

/app/lrba/lrba_script_fw -country '%%country' -environment '%%environment' -file-name '%%filename' -uuaa '%%uuaa' -partitioned '%%partitioned'

## Para ejecutar informando TTL.

/app/lrba/lrba_script_fw -country '%%country' -environment '%%environment' -file-name '%%filename' -uuaa '%%uuaa' -partitioned '%%partitioned' -polling-ttl '%%pollingttl'

## Descripción.

Los valores de las variables del script son:

- %%country=[{COUNTRY}]
- %%environment[{ENVIRONMENT}]
- %%filename=[{FILE_NAME}]
- %%uuaa=[{UUAA}]
- %%partitioned[{Y/N}]
- %%pollingttl=[{TTL}]

Ejemplo Fichero CSV:

<p align="left"> <img src="../../resources/img/ControlMFilewatcherCSV.png">

Ejemplo Fichero Parquet:

<p align="left"> <img src="../../resources/img/ControlMFilewatcherParquet.png">

La ejecución de los procesos LRBA Filewatcher en ambientes previos se realiza con la herramienta de Control-M.

La programación de un Job LRBA Filewatcher, en producción se realiza por medio de mallas, indicando en el apartado de comando
el script con el detalle del fichero requerido a monitorizar.

Ejemplo Malla Live

<p align="left"> <img src="../../resources/img/MallaFilewatcherLive.png">

El resultado de los procesos productivos se consultan utilizando la herramienta de Kyndryl Control-M

<p align="left"> <img src="../../resources/img/KyndrylControlM.png">



