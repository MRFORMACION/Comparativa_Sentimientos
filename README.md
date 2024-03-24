# (Re)Análisis de Sentimientos

El objetivo de este proyecto es refinar el análisis de sentimientos que se realiza sobre mensajes de la Red Social TWITTER.

Partiendo de un fichero con mensajes de TWITTER (ante la imposibilidad de poder leer comentarios ON-LINE desde la API de Twitter), se implementa un sistema que lo lee y calcula los sentimientos de esos mensajes.

Los mensajes tweets de este fichero YA VIENEN etiquetados con ciertos sentimientos, calculados en otro proceso externo.

Se desean reprocesar estos comentarios en tiempo real (a medida que se leen los datos) y aplicarles otro modelo de análisis para reetiquetarlos y comparar la calificación automática de ambos modelos.

Este es el diagrama de arquitectura de componentes que comforman el proyecto:

![image](https://github.com/MRFORMACION/Comparativa_Sentimientos/blob/main/Arquitectura.png)

> ENTRADA AL SISTEMA: Fichero con tweets preetiquetados (1).

> PROCESO LECTURA DE TWEETS: Ejecutable en Python (2) que extrae los tweets y los encola para su procesameinto en el TOPIC  "twitter" realizando la función de PRODUCER. Este TOPIC tendrá 2 CONSUMER (KSQL y otro proceso Pyhthon). 

> MOTOR KAFKA: Para la gestión de las colas de mensajes.

> PROCESO ANÁLISIS SENTIMIENTOS: Ejecutable en Python (3) que recibe el TOPIC "twitter", calcula el análisis de sentimientos y encola los mensajes con sus nuevos valores de sentimientos en el TOPIC "Sentimientos". Realiza la función de PRODUCER, teniendo como único CONSUMER (KSQL).

> MOTOR KSQL: Que recibe ambos TOPICs y compara las etiquetas originales y las generadas en el presente análisis.

En este proyecto usamos la versión 7.2.2 de los diferentes componentes KAFKA y KSQL que están configurados en contenedores DOCKER y la versión 3.x.x. de Python para los ejecutables. Además tendremos el fichero con los mensajes twitter "tweets.csv"



## Parte 1: Ingesta de datos con Python y Kafka.
  
 (1)  Fichero "tweets.csv" que contiene los mensajes con una etiqueta de sentimientos inicial calculada en otro proceso externo que es el que se desea comparar al final del proceso.

  El formato de los registros de este fichero es:

          IDENTIFICADOR_NUMERICO_DEL_MENSAJE , "TEXTO DE MENSAJE SIN SANITIZAR", SENTIMIENTO_ORIGEN

  Revisar fichero: https://github.com/MRFORMACION/Comparativa_Sentimientos/blob/main/tweets.csv

  (2) Fichero Python "extraer_de_twitter_a_kafka.py" que lee estos mensajes (en una pretensión inicial que fueran ON-LINE, pero para este proyecto se hace desde el fichero citado), y los encola en el TOPIC "twitter".
      Esta carga de mensajes se hace CADA 2 SEGUNDO para simular la recepción continua de datos.

  Revisar fichero: https://github.com/MRFORMACION/Comparativa_Sentimientos/blob/main/extraer_de_twitter_a_kafka.py



## Parte 2: MOTOR KAFKA.

Con la tecnologia que nos proporcionan los componentes de KAFKA, se utilizan 2 TOPIC. El primero ya citado "tweets" para la ingesta de datos y transmisión de eventos, y el segundo "Sentimientos" que se utilizará para procesar flujo de datos entre servicios (PROCESO DE ANÁLISIS DE SENTIMIENTOS -> PROCESO COMPARATIVA DE SENTIMIENTOS (KSQL))

 El PRODUCER de TOPIC "tweets" es el proceso de lecturas de mensajes, y los CONSUMER el proceso de análisis de sentimientos, y KSQL donde se realizará las comparaciones.

 El PRODUCER de TOPIC "Sentimientos" es el proceso de análisis de sentimientos, y el único CONSUMER será de nuevo KSQL donde se realizará las comparaciones.

 Estos TOPIC tendrán una única partición y el factor de replicación será también 1.

 El despliegue de los componentes KAFKA se realizará con la tecnología DOCKER, y esta conformado de los siguientes elementos:

       * Broker: Son los nodos o puntos de intersección del clúster. Almacenan los flujos de datos entrantes, clasificándolos en TOPICs. 
         En este caso solo habra un único nodo BROKER, y como se ha citado 1 partición y no habrá replica (factor de replicación 1).
       * Zookeeper: Gestiona los brokers de kafka y les envía notificaciones en caso de cambio como creación de topics, caída de broker, recuperación de broker, borrado de topics, ...
       * Control Center: Para monitorizar el NODO/BROKER  de Kafka, gestionar topics, monitorizar data streams, etc.
       * Servidor KSQL: Base de datos para manejar Streams y tablas y hacer las comparaciones.
       * Cliente de KSQL: Entorno desde donde se harán las consultas al Serivor KSQL. 


## Parte 3: PROCESO ANÁLISIS DE SENTIMIENTOS.

 (3) Fichero Python "consumer.py" que realiza las tareas de CONSUMER y PRODUCER. 
 Recibe los mensajes del TOPIC "twitter" y los sanitiza (hace limpieza de caracteres que no son útiles para el análisis).
 
 Posteriormente utiliza la función "TextBlob" para calcular el sentimiento del mensaje.
 
 Y por último realiza la tarea de PRODUCER con el registro enriquecido con los nuevos valores.

 Con el Método "TextBlob" se calculan 3 campos de sentimientos que ayudarán en la comparativa posterior en KSQL, ya que intentan determinar la actitud del usuario con respecto al tema del mensaje, y la polaridad 
 contextual general del mismo.

 Estos campos son:
 
      > Sentimiento: Con valores "Positivo", "Negativo" o "Neutro".
 
      > Subjetividad: Valor entre 0 (muy objetivo) y 1 (muy subjetivo).
      
      > Polaridad: Entendido comoestado de ánimo, con valor entre -1 (ánimo muy negativo) y 1 (ánimo muy positivo).

 Mas información:  https://es.wikipedia.org/wiki/An%C3%A1lisis_de_sentimiento

 Revisar fichero:  https://github.com/MRFORMACION/Comparativa_Sentimientos/blob/main/consumer.py


 
## Parte 4: MONITOR COMPARATIVA DE SENTIMIENTOS.

 El preanálisis de sentimientos (externo a este proyecto) que se realiza a los mensajes del fichero de entrada "tweets.csv" los etiqueta con los siguientes valores:

        |angry             |
        |disgust           |
        |disgust|angry     |
        |happy             |
        |happy|sad         |
        |happy|surprise    |
        |nocode            |
        |not-relevant      |
        |sad               |
        |sad|angry         |
        |sad|disgust       |
        |sad|disgust|angry |
        |surprise          |

 Mientras que el análisis que se realiza en este proceso aporta las etiquetas:

        |Negativo   |
        |Neutro     |
        |Positivo   |

 En la comparativa, lo que se desea detectar, son los mensajes que NO concuerden entre los tipos de etiquetados. Es decir, que si por ejemplo en el etiquetado de este proceso, el mensaje se marca como "Positivo", nos lo muestre en el monitor de consulta si la preetiqueta es diferente a "happy".

 Estos son los valores que se han considerado equivalentes:

 ![image](https://github.com/MRFORMACION/Comparativa_Sentimientos/blob/main/DIAGRAMA%20de%20ETIQUETAS.drawio.png)

 Todo mensaje que no cumpla con estas equivalencias, se mostrará en el Monitor de Comparativa de Sentimiento en el KSQL, lo que permitirá optimizar los modelos de cálculo (Proceso fuera de este proyecto).


--------------------------------------------------------------------------
--------------------------------------------------------------------------


# Configuración y explotación del Proyecto.

 En primer lugar, pondremos en marcha los componentes de KAFKA (docker compose up), prepararemos el entorno y las consultas en KSQL para recibir automáticamente los mensajes que tengan discrepancias entre  ambos etiquetados.

 Posteriormente copiaremos los ficheros ejecutables y el fichero csv de entrada, y pondremos en marcha los PRODUCERs, CONSUMERs y ANÁLISIS DE SENTIMIENTOS.

 Vamos allá.



## PASO 1: Puesta en marcha componentes KAFKA.

 > Arrancar la aplicación DOCKER DESKTOP 
 > Descargar el fichero docker-compose.yml
 > Situados en el directorio de descarga del fichero docker-compose.yml ejecutar:

     docker compose up -d

 Cuando acabe de ejecutarse este comando y haya creado los contenedores de los componentes KAFKA, accedemos al del KSQL.


## PASO 2: Arrancar el MONITOR DE COMPARATIVAS DE SENTIMIENTOS (KSQL)

 Que recibe ambos TOPICs y compara las etiquetas originales y las generadas en el presente análisis.
 Acceder al Cliente de KSQK:

    docker exec -it ksqldb-cli ksql http://ksqldb-server:8088

 Ahora crearemos una serie de streams y tablas para las consultas:

    create stream tweets (id VARCHAR, msg VARCHAR, preanotacion VARCHAR) with (kafka_topic='twitter', value_format='JSON', partitions=1);

    create stream Sentimientos (id VARCHAR, msg VARCHAR, Sentimiento VARCHAR, Subjetividad VARCHAR, Polaridad VARCHAR) with (kafka_topic='Sentimientos', value_format='JSON', partitions=1);

    create table tabla_sentimientos (id VARCHAR PRIMARY KEY, msg VARCHAR, Sentimiento VARCHAR, Subjetividad VARCHAR, Polaridad VARCHAR) with (kafka_topic='Sentimientos', value_format='JSON', partitions=1);

    create table tabla_tweets as select preanotacion, count(*) as contador from  tweets group by preanotacion emit changes;

    create table tabla_recuento_sentimientos as select Sentimiento, count(*) as contador from Sentimientos group by Sentimiento emit changes;

    create stream Stream_join_sentimientos as select  t.id id_twitter, t.msg msg_twitter, t.preanotacion, S.Sentimiento, S.Subjetividad, S.Polaridad from tweets t LEFT JOIN tabla_sentimientos S ON t.id = S.id EMIT CHANGES;
 
 En esta consola, ahora vamos a lanzar una consulta que recibirá las discrepancias entre ambos etiquetados. 
 
 LA SIGUIENTE CONSULTA MANTIENE LA CONSOLA EN ESPERA DE DATOS Y A PARTIR DE AHORA SOLO SE UTILIZARÁ PARA ESTA FUNCIÓN (RECEPCIÓN DE DATOS DE DISCREPANCIAS).

    select * from Stream_join_sentimientos where ((preanotacion = 'nocode' or preanotacion = 'not-relevant' or preanotacion = 'surprise')  and Sentimiento != 'Neutro') or (preanotacion = 'happy' and Sentimiento != 'Positivo') or ((preanotacion = 'sad' or preanotacion = 'angry' or preanotacion = 'disgust') and Sentimiento != 'Negativo') emit changes;

 EN OTRA CONSOLA, deberemos ejecutar estos comandos para obtener el conteo de los mensajes que van llegando al KSQL:

    docker exec -it ksqldb-cli ksql http://ksqldb-server:8088

 Dentro de KSQL se podrán ejecutar estos comandos a demanda, cuando se necesite saber cuantos registros se han recibido de cada sentimiento:
  
    select * from tabla_tweets;

    select * from tabla_recuento_sentimientos;

 Estas acciones dejaran 2 consolas abiertas para ir verificando que los datos de los TOPIC van llegando y se van comparando


## Paso 3: Copia de ficheros e instalación de bibliotecas Python.
 
  Descargar los ficheros ejecutables Python y copiarlos al contenedor BROKER.

    docker cp consumer.py broker:/home/appuser
    docker cp extraer_de_twitter_a_kafka.py broker:/home/appuser
  
  También copiar el fichero con los mensajes iniciales de twitter.

    docker cp tweets.csv broker:/home/appuser

  Accedemos al contenedor BROKER

    docker exec -it broker /bin/bash

  E instalamos la bibliotecas Python

    pip3 install kafka-python
    pip3 install textblob

## Paso 4: (OPCIONAL) Suscribirnos a los TOPIC (uno en cada consola) para ir verificando que los TOPIC reciben mensajes.
 
  En otras 2 consolas diferentes (o en uno de los casos, reutilizando la anterior de copias de ficheros e instalación de bibliotecas) deberemos abrir sesión en el BROKER:

    docker exec -it broker /bin/bash
 
 Y en cada uno suscribirnos a los TOPIC:

    kafka-console-consumer --bootstrap-server broker:9092 --topic twitter --from-beginning  (en una de las consolas)
    kafka-console-consumer --bootstrap-server broker:9092 --topic Sentimientos --from-beginning (en otra de las consolas)

 
## Paso 5: Ejecución de los procesos de Extracción de mensajes (desde fichero "tweets.csv") y Análisis de Sentimientos.

  Este paso lo que hace es ejecutar ambos ficheros Python para las acciones de PRODUCER y CONSUMER de los procesos.

  En otras 2 consolas diferentes deberemos abrir sesión en el BROKER:

    docker exec -it broker /bin/bash
 
 Y en cada uno ejecutamos un fichero Python:

    python3 extraer_de_twitter_a_kafka.py   (en una de las consolas)
    python3 consumer.py                     (en otra de las consolas)




En el Monitor que se crea en el Paso 2, se deberían de estar recibiendo mensajes con discrepancia en ambos etiquetados.


