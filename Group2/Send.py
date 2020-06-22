#!/usr/bin/env python3
import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN
from LoRaWAN.MHDR import MHDR
import json,datetime
import Adafruit_DHT
from gps import *
import requests
import time
from firebase import firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import RPi.GPIO as GPIO

BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN sender")
def Music():
    print("Music")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(16, GPIO.OUT) 
    p = GPIO.PWM(16, 1)
    p.start(100)
    
    print("Do")
    p.ChangeFrequency(523)
    sleep(1)
    
    print("Re")
    p.ChangeFrequency(587)
    sleep(1)
   
    print("Mi")
    p.ChangeFrequency(659)
    sleep(1)
   
    p.stop()
    
    GPIO.cleanup()

def GPS():
    #Listen on port 2947 of gpsd
    session = gps("localhost","2947")
    #session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
    m = ""
    flag = False
    for i in str(session):
       if i == "A":
          break
       if i == "L" and (not flag):
          flag = True
       if flag:
          m = m + i
    
    url = "https://gpsfinalproject-7afcb.firebaseio.com/"
    fb = firebase.FirebaseApplication(url, None)
    newGpsData = m
    lat = float(m.split(" ")[2])
    lon = float(m.split(" ")[3].split("\n")[0])
    fb.put("/gpsData", "lat", lat)
    fb.put("/gpsData", "lon", lon)
    print(lat, lon)
    dist = fb.get('https://gpsfinalproject-7afcb.firebaseio.com/', 'distance')
    print(dist)
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    while(dist < 0.01):
        #break
        Music()
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        if(humidity>70):
            print("humidity>70")
            break
    return m

def DHT22():
    sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
    sensor = Adafruit_DHT.DHT22
    pin = 4
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    print(humidity, temperature)
    if(humidity > 70):
        print(">70")
    return str(int(humidity)) +   " " + str(int(temperature))


class LoRaWANsend(LoRa):
    def __init__(self, devaddr = [], nwkey = [], appkey = [], verbose = False):
        super(LoRaWANsend, self).__init__(verbose)
        
    def on_tx_done(self):
        print("TxDone\n")
        # ???郢x
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0,0,0,0,0,0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        sleep(1)
        self.set_mode(MODE.RXSINGLE)
        
    def on_rx_done(self):
        global RxDone
        RxDone = any([self.get_irq_flags()[s] for s in ['rx_done']])
        print("RxDone")
        self.clear_irq_flags(RxDone=1)
        
        # 霈??payload
        payload = self.read_payload(nocheck=True)
        lorawan = LoRaWAN.new(nwskey, appskey)
        lorawan.read(payload)
        print("get mic: ",lorawan.get_mic())
        print("compute mic: ",lorawan.compute_mic())
        print("valid mic: ",lorawan.valid_mic())
        # 瑼Ｘmic
        if lorawan.valid_mic():
            print("ACK: ",lorawan.get_mac_payload().get_fhdr().get_fctrl()>>5&0x01)
            print("direction: ",lorawan.get_direction())
            print("devaddr: ",''.join(format(x, '02x') for x in lorawan.get_devaddr()))
            write_config()
        else:
            print("Wrong MIC")
    
    def send(self):
        global fCnt
        lorawan = LoRaWAN.new(nwskey, appskey)
        message = GPS()
        # 鞈???,fCnt+1
        lorawan.create(MHDR.CONF_DATA_UP, {'devaddr': devaddr, 'fcnt': fCnt, 'data': list(map(ord, message)) })
        print("fCnt: ",fCnt)
        print("Send Message: ",message)
        fCnt = fCnt+1
        self.write_payload(lorawan.to_raw())
        self.set_mode(MODE.TX)
    
    def time_checking(self):
        global RxDone
        # 瑼Ｘ?臬頞?
        TIMEOUT = any([self.get_irq_flags()[s] for s in ['rx_timeout']])
        if TIMEOUT:
            print("TIMEOUT!!")
            write_config()
            sys.exit(0)
        elif RxDone:
            print("SUCCESS!!")
            sys.exit(0)
    
    def start(self):
        self.send()
        while True:
            self.time_checking()
            sleep(1)

def binary_array_to_hex(array):
    return ''.join(format(x, '02x') for x in array)

def write_config():
    global devaddr,nwskey,appskey,fCnt
    config = {'devaddr':binary_array_to_hex(devaddr),'nwskey':binary_array_to_hex(nwskey),'appskey':binary_array_to_hex(appskey),'fCnt':fCnt}
    data = json.dumps(config, sort_keys = True, indent = 4, separators=(',', ': '))
    fp = open("config.json","w")
    fp.write(data)
    fp.close()

def read_config():
    global devaddr,nwskey,appskey,fCnt
    config_file = open('config.json')
    parsed_json = json.load(config_file)
    devaddr = list(bytearray.fromhex(parsed_json['devaddr']))
    nwskey = list(bytearray.fromhex(parsed_json['nwskey']))
    appskey = list(bytearray.fromhex(parsed_json['appskey']))
    fCnt = parsed_json['fCnt']
    print("devaddr: ",parsed_json['devaddr'])
    print("nwskey : ",parsed_json['nwskey'])
    print("appskey: ",parsed_json['appskey'],"\n")

# Init
RxDone = False
fCnt = 0
devaddr = []
nwskey = []
appskey = []
read_config()
lora = LoRaWANsend(False)

# Setup
lora.set_mode(MODE.SLEEP)
lora.set_dio_mapping([1,0,0,0,0,0])
lora.set_freq(AS923.FREQ1)
lora.set_spreading_factor(SF.SF7)
lora.set_bw(BW.BW125)
lora.set_pa_config(pa_select=1)
lora.set_pa_config(max_power=0x0F, output_power=0x0E)
lora.set_sync_word(0x34)
lora.set_rx_crc(True)

#print(lora)
assert(lora.get_agc_auto_on() == 1)

try:
    print("Sending LoRaWAN message")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("\nKeyboardInterrupt")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
    write_config()
