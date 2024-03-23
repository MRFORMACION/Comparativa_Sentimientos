#import tweepy
#import os
import time
import json
from kafka import KafkaProducer
import logging
import csv

"""API ACCESS KEYS"""   #Si tuvieramos cuenta de desarrollador de TWITTER para descargar 

consumerKey = "XXXX"
consumerSecret = "XXXX"
accessToken = "XXX-XXX"
accessTokenSecret = "XXXX"


log = logging.getLogger(__name__)
# Creamos el Productor
producer = KafkaProducer(bootstrap_servers=['localhost:9092'], 
value_serializer=lambda x: json.dumps(x).encode('utf-8'))

# Funcion para el caso de exito en la produccion del metodo
def on_send_success(record_metadata):
  print(record_metadata.topic)
  print(record_metadata.partition)
  print(record_metadata.offset)

# que haremos en caso de error
def on_send_error(ex):
  log.error('I am an Error', exc_info=ex)
  # handle exception



#Creamos el Topic
topic_name = 'twitter'

#Generamos mensajes en el Topic

with open ('tweets.csv', 'r') as fichero:
    reader = csv.reader(fichero)
    for linea in reader:
        clave = linea[0]
        valor = {'Id': linea[0], 'msg':linea[1], 'preanotacion': linea[2]}
        producer.send(topic_name, key=clave.encode('utf-8'), 
        value=valor).add_callback(on_send_success).add_errback(on_send_error)
        time.sleep(2)

producer.flush()
