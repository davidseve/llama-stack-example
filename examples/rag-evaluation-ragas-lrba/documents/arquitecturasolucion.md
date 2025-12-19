1. Lectura y Escritura de ficheros de tipo Excel.

En LRBA se pueden leer fichero de tipo Excel utilizando el conector de lectura de binarios y Apache POI, que es una de las dependencias externas aceptadas por la Arquitectura LRBA.
A su vez también se pueden escribir utilizando ficheros Excel utilizando el conector de escritura de binarios.

2. Limitaciones en compilación, Despliegue y Ejecución de componentes en la Arquitectura LRBA.

- Limitación en compilación
    - Las pipelines aplicativas de LRBA permiten la COMPILACIÓN de componentes siempre que se cumpla que la versión del pom.xml a implantar sea ≥ (mayor o igual que) versión mínima permitida.
    - La versión mínima permitida es la versión más antigua instalada en los entornos de Europa y América. Consulta disponible en las Release Notes.

- Limitación en despliegue
    - La Arquitectura LRBA permite el DESPLIEGUE de componentes siempre que se cumpla que la versión del pom.xml a implantar sea ≤ (menor o igual que) versión máxima permitida.
    - La versión máxima permitida es la versión de arquitectura instalada en en el entorno seleccionado de Europa y América. Consulta disponible en las Release Notes.

- Limitaciones en ejecución
    - Los jobs en LRBA se EJECUTAN siempre con la última versión de arquitectura disponible en el entorno, porque el framework de LRBA por norma es retrocompatible a excepción de posibles Breaking Changes que hagan que el código no funcione correctamente.
    - Si el código no se ve afectado por los posibles Breaking Changes NO es necesario recompilar el código en una versión actualizada.
    - Por tanto, el código aplicativo se ejecuta siempre con la versión de las dependencias de terceros desplegadas en el entorno que NO tienen por qué coincidir con las versiones anotadas en el pom.xml.

3. Como ingestar datos en BTS desde otros orígenes.

En LRBA, para ingesta de datos en BTS, se recomienda el uso de DataX. Para más información, sobre cómo configurar un adaptador, consulta la entrada en Platform de los [adaptadores BTS en DataX](https://platform.bbva.com/data-x/documentation/1glfRHhekQtSTmjIAbjGxJMRBy-0m-YrZR33wXArYHRo/systems/bts-lrba).