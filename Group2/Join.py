#!/usr/bin/env python3
import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN,json,datetime
from LoRaWAN.MHDR import MHDR
from random import randrange

BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN sender")

class LoRaWANotaa(LoRa):
    def __init__(self, verbose = False):
        super(LoRaWANotaa, self).__init__(verbose)

    def on_rx_done(self):
        print("RxDone")

        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)

        lorawan = LoRaWAN.new([], appkey)
        lorawan.read(payload)
        lorawan.get_payload()
        # ?斗?澆??臬?撇OIN_ACCEPT
        if lorawan.get_mhdr().get_mtype() == MHDR.JOIN_ACCEPT:
            print("get mic: ",lorawan.get_mic())
            print("compute mic: ",lorawan.compute_mic())
            print("valid mic: ",lorawan.valid_mic())
            
            # ?斗downlink?臭??航撌梁?
            if lorawan.valid_mic():
                devaddr = binary_array_to_hex(lorawan.get_devaddr())
                nwskey = binary_array_to_hex(lorawan.derive_nwskey(devnonce))
                appskey = binary_array_to_hex(lorawan.derive_appskey(devnonce))
                print("devaddr:",devaddr)
                print("nwskey :",nwskey)
                print("appskey:",appskey)
                
                # 撠?啁?devaddr,nwskey,appskey撖怠瑼?銝?                config = {'devaddr':devaddr,'nwskey':nwskey,'appskey':appskey,'fCnt':0}
                data = json.dumps(config, sort_keys = True, indent = 4, separators=(',', ': '))
                fp = open("config.json","w")
                fp.write(data)
                fp.close()
                print("Join Accept")
                sys.exit(0)
                
            else:
                print("Fail to join!")
                sys.exit(0)

    def on_tx_done(self):
        self.clear_irq_flags(TxDone=1)
        print("TxDone")
        # ???郢x
        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0,0,0,0,0,0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        sleep(4)
        self.set_mode(MODE.RXCONT)

    def join(self):
        # ?喲oin?澆?撠?
        lorawan = LoRaWAN.new(appkey)
        lorawan.create(MHDR.JOIN_REQUEST, {'deveui': deveui, 'appeui': appeui, 'devnonce': devnonce})
        self.write_payload(lorawan.to_raw())
        self.set_mode(MODE.TX)
        
    def start(self):
        self.join()
        while True:
            sleep(1)
            
def binary_array_to_hex(array):
    return ''.join(format(x, '02x') for x in array)            

# Init
deveui = list(bytearray.fromhex('0000000000000012'))
appeui = list(bytearray.fromhex('1234efc7104f1230'))
appkey = list(bytearray.fromhex('a346b6faef2bd33c16fe9b1d8d47a11d'))
devnonce = [randrange(256), randrange(256)]

lora = LoRaWANotaa(False)

# Setup
lora.set_mode(MODE.SLEEP)
lora.set_dio_mapping([1,0,0,0,0,0])
lora.set_freq(923.2)
lora.set_pa_config(pa_select=1)
lora.set_spreading_factor(7)
lora.set_pa_config(max_power=0x0F, output_power=0x0E)
lora.set_sync_word(0x34)
lora.set_rx_crc(True)

#print(lora)
print("deveui:",binary_array_to_hex(deveui))
print("appeui:",binary_array_to_hex(appeui))
print("appkey:",binary_array_to_hex(appkey))
assert(lora.get_agc_auto_on() == 1)

try:
    print("Sending LoRaWAN join request")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("\nKeyboardInterrupt")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
