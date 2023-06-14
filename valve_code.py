import time
import firebase_admin
import threading
import RPi.GPIO as GPIO
import serial
import random

from threading import Thread
from decimal import Decimal

# Ubidots MQTT credentials
UBIDOTS_TOKEN ="BBFF-h4xGqFJ8fvmHulhKLRCcA7ZESSmoLB" #"YOUR_UBIDOTS_TOKEN"
UBIDOTS_DEVICE_LABEL ="test_01" #"YOUR_DEVICE_LABEL"
UBIDOTS_VARIABLE_LABEL_PUB ="sensor" #"YOUR_VARIABLE_LABEL"
UBIDOTS_VARIABLE_LABEL_SUB ="valve" #"YOUR_VARIABLE_LABEL"
UBIDOTS_VARIABLE_ID =  "64879f00b1f4d80cd34a24ef"

# MQTT broker details
MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "BG95_MQTT_CLIENT"
MQTT_USERNAME = UBIDOTS_TOKEN
MQTT_PASSWORD = ""

# Serial port configuration
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# Create the serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Configuración del módulo BG95
ser.write('AT+CGATT=1\r\n'.encode())
time.sleep(1)
ser.write('AT+CGDCONT=1,"IP","Internet4gd.gdsp"\r\n'.encode())
time.sleep(1)
ser.write('AT+CGACT=1,1\r\n'.encode())
time.sleep(1)
ser.write('AT+QIACT=1\r\n'.encode())
time.sleep(1)

#GPIO SETUP
ESPERA = 1
PIN = 11
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.OUT)

def generar_numero_aleatorio(rango_inicial, rango_final):
    return random.randint(rango_inicial, rango_final)

# Helper function to send AT command and read response
def send_at_command(command):
	ser.write((command + "\r\n").encode())
	time.sleep(0.1)
	response = ser.read_all().decode()
	return response

dataSensor= generar_numero_aleatorio(1,100)


while True:
	

	# Connect to the MQTT broker
	send_at_command('AT+QMTCFG="keepalive",0,30')
	time.sleep(1)
	send_at_command('AT+QMTOPEN=0,"{}",{}'.format(MQTT_BROKER, MQTT_PORT))
	time.sleep(2)

	# Set MQTT connection parameters
	send_at_command('AT+QMTCONN=0,"{}","{}"'.format(MQTT_CLIENT_ID, MQTT_USERNAME))
	time.sleep(2)

	# Publish data to Ubidots
	prev = '"value": {}'.format(generar_numero_aleatorio(1,100))
	payload = '{' + prev + '}'
	topic = '/v1.6/devices/{}/{}'.format(UBIDOTS_DEVICE_LABEL,UBIDOTS_VARIABLE_LABEL_PUB)
	send_at_command('AT+QMTPUBEX=0,0,0,0,"{}","{}"'.format(topic,payload))
	time.sleep(1)
	
	# Retrieve data from Ubidots
	topic = '/v1.6/devices/{}/{}/lv'.format(UBIDOTS_DEVICE_LABEL,UBIDOTS_VARIABLE_LABEL_SUB)
	send_at_command('AT+QMTSUB=0,1,"{}",2'.format(topic))
	time.sleep(1)
	
	# Wait for the MQTT message
	response_variable = ''
	while "+QMTRECV: 0,0" not in response_variable:
		line = ser.readline()
		time.sleep(1)
		response_variable = line.decode() #send_at_command('AT+QMTRECV=0,10')
	#print(response_variable)

	# Extract the data from the MQTT message
	data = response_variable.split(',')[3].strip('"\r\n')
	int_data = int(Decimal(data))
	print("Received data:", int_data)
	
	#Open/Close the valve
	if int_data == 0:
		GPIO.output(PIN, GPIO.HIGH)
		time.sleep(ESPERA)
		print('Valvula cerrada')
		#Aquí se manda la señal para cerrar la valvula
	else:
		GPIO.output(PIN, GPIO.LOW)
		time.sleep(ESPERA)
		print('Valvula abierta')
	
	
	# Unsubscribe from the MQTT topic
	send_at_command('AT+QMTUNS=0,1,"{}"'.format(topic))
	time.sleep(1)

	# Disconnect from the MQTT broker
	send_at_command('AT+QMTDISC=0')
	time.sleep(1)

	# Close the serial connection
	#ser.close()
	time.sleep(3)


