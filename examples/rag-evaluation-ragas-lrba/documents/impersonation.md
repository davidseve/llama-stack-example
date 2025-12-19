# commonoperations/02-SharedFilesUUAAs.md
# Compartir ficheros entre UUAAs

La Arquitectura LRBA permite compartir ficheros en el BTS entre UUAAs. Las opciones de impersonación validas son:

| MODE	  |   VISIBILITY    | WRITE SCOPE  |    
|:------:|:---------------:|:------------:|
|  `RO`  | `GROUP_SHARED`  |              |
|  `WO`  |                 |   `INBOX`    |
|  `RW`  | `GROUP_SHARED`  |   `INBOX`    |


Opción 1 - **`RO`-`GROUP_SHARED`**: Permite la lectura de ficheros compartidos entre UUAAs.

Opción 2 - **`WO`-`INBOX`**: Permite la escritura de ficheros en el BTS de la UUAA en el path inbox/{uuaa_impersonada}.

Opción 3 - **`RW`-`GROUP_SHARED`-`INBOX`**: Combinación de las primeras dos opciones.


## Ejemplos

### Ejemplo 1
`RO` - `GROUP_SHARED`

UUAA1 define su fichero con visibilidad `GROUP_SHARED` en el Target del job.

```java
@Override
public TargetsList registerTargets() {
        return TargetsList.builder()
            .add(Target.File.Parquet.builder()
                .alias("outputFile")
                .physicalName("transformedData.parquet")
                .serviceName("bts.UUAA1.BATCH")
                .fileVisibility(VisibilityType.GROUP_SHARED)
                .build())
            .build();
        }
```

UUAA1 define la siguiente impersonación:
```
Type: bts
UUAA: UUAA2
Mode: RO
Visibility: GROUP_SHARED
```

UUAA2 tiene permiso para la lectura del fichero compartido accediendo al BTS de la UUAA1:

```java
public SourcesList registerSources() {
    return SourcesList.builder()
            .add(Source.File.Parquet.builder()
                    .alias("alias")
                    .serviceName("bts.UUAA1.BATCH")
                    .physicalName("transformedData.parquet")
                    .build())
            .build();
}
```


### Ejemplo 2
`WO` - `INBOX`

UUAA1 define la siguiente impersonación:
```
Type: bts
UUAA: UUAA2
Mode: WO
WriteScope: INBOX
```

UUAA2 puede escribir ficheros en el path del BTS de la UUAA1 `inbox/{UUAA2}/...`, es estrictamente necesario que en el physicalName se especifique el path `inbox/{UUAA_que_escribe_fichero}/{fichero}`, ya que la arquitectura por si misma no puede deducir si se esta intentando escribir en el INBOX, o en cualquier otra ruta del BTS de la UUAA destino.

```java
@Override
public TargetsList registerTargets() {
    return TargetsList.builder()
            .add(Target.File.Parquet.builder()
                    .alias("outputFile")
                    .physicalName("inbox/UUAA2/transformedData.parquet")
                    .serviceName("bts.UUAA1.BATCH")
                    .build())
            .build();
}
```


### Ejemplo 3
`RW` - `GROUP_SHARED` - `INBOX`

UUAA1 define su fichero con visibilidad `GROUP_SHARED` en el job.

UUAA1 le da permisos de lectura y escritura en la consola a la UUAA2.

UUAA2 puede leer ficheros compartidos por la UUAA1 

UUAA2 puede escribir en el BTS de la UUAA1 en el path `inbox/{UUAA2}/...` siempre y cuando se especifique en el physicalName `inbox/{UUAA2}/{fichero}`



**NOTA IMPORTANTE**

- La compartición de ficheros no se puede realizar si el origen de los datos es DataX.
- Estos permisos sólo pueden ser dados de alta por los `Technical Leaders`.
- Las opciones del tipo WO/RW permiten la escritura exclusivamente en el path `/inbox/{UUAA}`


Echa un vistazo a nuestro [*Codelab* de Impersonación](https://platform.bbva.com/codelabs/lra-batch/CodelabLRBA1#/lra-batch/LRBA%20Spark%20-%20Compartir%20ficheros%20entre%20UUAAs%20%28ESP%29/Introducci%C3%B3n/) para ver como utilizarlo.

