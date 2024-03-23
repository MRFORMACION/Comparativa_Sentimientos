import json
import re
from textblob import TextBlob
from kafka import KafkaConsumer
from kafka import KafkaProducer


topic_name_entrada = 'twitter'
topic_name_salida = 'Sentimientos'

#Sanitizar campo texto
def sanitizar(tweet: str) -> str:
    # Elimina link
    tweet = re.sub(r'http\S+', '', str(tweet))
    tweet = re.sub(r'bit.ly/\S+', '', str(tweet))
    tweet = tweet.strip('[link]')

    # elimina nick usuarios
    tweet = re.sub('(RT\s@[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))
    tweet = re.sub('(@[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))

    # elimina signos puntuacion
    my_punctuation = '!"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@â'
    tweet = re.sub('[' + my_punctuation + ']+', ' ', str(tweet))

    # elimina numero 
    tweet = re.sub('([0-9]+)', '', str(tweet))

    # elimina el hashtag
    tweet = re.sub('(#[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))

    return tweet

# Definimos el Consumer que lee del Topic de entrada
consumer = KafkaConsumer(
    topic_name_entrada,
     bootstrap_servers=['localhost:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     auto_commit_interval_ms=5000,
     fetch_max_bytes=128,
     max_poll_records=100,
     value_deserializer=lambda x: json.loads(x.decode('utf-8')))

#Definimos ek Producer que escribe un nuevo Topis Salida
producer = KafkaProducer(
    bootstrap_servers=['broker:9092'],
    value_serializer=lambda m: json.dumps(m).encode('utf-8'))

# Funcion para el caso de exito en la produccion del metodo
def on_send_success(record_metadata):
  print(record_metadata.topic)
  print(record_metadata.partition)
  print(record_metadata.offset)

# que haremos en caso de error
def on_send_error(ex):
  log.error('I am an Error', exc_info=ex)
  # handle exception


for message in consumer:
   #print(message.value["msg"])
   decoded = message.value["msg"]
   #decoded= message["msg"].value.decode('utf-8')
   texto_sanitizado = sanitizar(decoded)
   
   Analisis = TextBlob(decoded)
   Sentimiento = 'Neutro'
   if Analisis.sentiment.polarity > 0:
      Sentimiento = 'Positivo'
   elif Analisis.sentiment.polarity < 0:
      Sentimiento = 'Negativo'

   Subjetividad = Analisis.sentiment.subjectivity
   Polaridad = Analisis.sentiment.polarity

   clave = message.value["Id"]
   valor = {'Id': message.value["Id"], 'msg': texto_sanitizado, 'Sentimiento': Sentimiento, 'Subjetividad': Subjetividad, 'Polaridad': Polaridad}
   producer.send(topic_name_salida, key=clave.encode('utf-8'), 
   value=valor).add_callback(on_send_success).add_errback(on_send_error)
producer.flush()
