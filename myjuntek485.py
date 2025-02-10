##############################################################
#                                                            #
# thanks to https://github.com/AnalogThinker/junctek_monitor #
#                                                            #
##############################################################


'''

#python3
#async-timeout==4.0.2
#bleak==0.20.2
#dbus-fast==1.86.0
#paho-mqtt==1.6.1
#PyYAML==6.0
#pyserial

# per usare anche il monitor collegato, cambiargli indirizzo P01->P02
# premere SET 5 secondi
# P01 diventa rosso
# usare le frecce  P01->P02
# premere OK


# la risposta puo' cambiare, controllare il manuale  
 
:r50=1,229,1342,20,16022,52,71,43,123,0,99,1,1193,13392,
0 1=indirizzo juntek
1 229=chesum
2 1342/100 = 13.42 volt
3 20/100=0.2 amp
4 16022/1000=16.022 ah remaining
5 52/1000=0.052 total use kwh
6 71/1000=0.071 total charge kwh
7 43 record of operation
8 123-100=23 temp
9 0 represents a function to be determined;
10 99 represents the output status as ON; (0-ON, 1-OVP, 2-OCP, 3-LVP, 4-NCP,5-OPP,6-OTP,99-OFF)
11 1 represents the current direction, currently charging current; (0-discharge,1-charging)
12 1193 minuti per scaricare batteria
13 13392 resistenza interna = 13392/100 133.92 mOhm

### USE python3 myjuntek485.py ACM0

'''



import asyncio
import signal
import time
import serial
import math
import random
from paho.mqtt import client as mqtt_client
import random
import json
import re
import os
import sys

#################### change this
version="myjuntek485 v1.0"
config_BATT_CAP=2
broker = "192.168.2.11"
usethisname = "user"
usethispassword = "pass"
port = 1883

###################

if (len(sys.argv)>1):
   arg1= str(sys.argv[1])
   arg1=arg1.strip()
else:
   arg1=""
   
if (arg1 == ""):
   print(version)
   print("USE python3 myjuntek485.py ACM0")
   print("if junktek is /dev/ttyACM0")
   print("exit")
   sys.exit(1)
   
config_DEV="/dev/tty"+arg1

esiste=os.system("ls "+ config_DEV)

if esiste==0:
    print(config_DEV+" OK")
else:
   print(version)
   print("USE python3 myjuntek485.py ACM0")
   print("if junktek is /dev/ttyACM0")
   print(" ")
   print("your choice "+config_DEV+" is invalid")
   print("exit")
   sys.exit(1)



#sleeptime serve per mqtt
sleeptime = 1
client_id = f'python-mqtt-{random.randint(0, 1000)}'
client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)

#client.username_pw_set(username=usethisname, password=usethispassword)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker with result: {rc}")
        client.publish(topic, msg)
        print (topic)
        print (msg)
        client.disconnect()
        print()
        print("========================================")
        print(f"Gracefully disconnected from MQTT Broker")
        time.sleep(sleeptime)
    else:
        print("Failed to connect to Broker, return code = ", rc)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT Broker disconnection!")
        time.sleep(1)





#config_BATT_CAP=2
#config_DEV="/dev/ttyACM0"
        
#        self.data = JTData()
        #global discovery_info_sent
#        self.name = "Juntek Monitor"
        #Capture data from RS485

        '''
        set amp=2
        with serial.Serial(config_DEV, baudrate=115200, timeout=1) as serialHandle:
            get_values_str = b':W28=1,0,20,\n'
            serialHandle.write(get_values_str)
            byte_string = serialHandle.readline()
        string = byte_string.decode()
        string = string.strip()
        print (string)
        print (" ")
        time.sleep(2)
        '''
read=0
try:
  with serial.Serial(config_DEV, baudrate=115200, timeout=1) as serialHandle:
     get_values_str = b':R00=1,2,1,\n'
     serialHandle.write(get_values_str)
     byte_string = serialHandle.readline()
     #print(byte_string)
     #split CSV
    
     string = byte_string.decode()
     string = string.strip()
     print (string)
     values = string.split(',')
     calc_ser=values[4]
     calc_sof=values[3]
     calc_mod=values[2]
     read=1   
     #print (calc_ser)
     #print (" ")
except Exception as er:
    print("The error is: ",er) 
    sys.exit(1)


time.sleep(2)
try:
  with serial.Serial(config_DEV, baudrate=115200, timeout=1) as serialHandle:
        get_values_str = b':R50=1,2,1,\n'
        serialHandle.write(get_values_str)
        byte_string = serialHandle.readline()
        #print(byte_string)
        #split CSV
        string = byte_string.decode()
        string = string.strip()
        print (string)
        values = string.split(',')
        #Calculations
        calc_watts = int(values[2])*int(values[3])/10000

        #Formatting the data
        data_jt_batt_v = int(values[2])/100
        data_jt_current = int(values[3])/100
        data_jt_watts = math.ceil(calc_watts*100)/100
        #self.data.jt_batt_charging = int(values[11])
        data_jt_soc = math.ceil(int(values[4]) / config_BATT_CAP) /10
        data_jt_ah_remaining = int(values[4])/1000
        data_jt_tot_charge = int(values[6])/100000
        data_jt_min_remaining = int(values[12])
        data_jt_temp = int(values[8])-100
        data_jt_resi = int(values[13])/100
     
        #Negative values if Discharging (0)
        if int(values[11]) == 0:
            data_jt_watts = -data_jt_watts
            data_jt_current =-data_jt_current 
        read=read+1
except Exception as er:
    print("The error is: ",er)
       

if (read==2):
   timestamp=int(time.time())
   mystr='{"timestamp": "'+str(timestamp)+'", '
   mystr=mystr+'"jt_model": "'+str(calc_mod)+'", '
   mystr=mystr+'"jt_soft": "'+str(calc_sof)+'", '
   mystr=mystr+'"jt_serial": "'+str(calc_ser)+'", '
   mystr=mystr+'"jt_volt": "'+str(data_jt_batt_v)+'", '
   mystr=mystr+'"jt_amp": "'+str(data_jt_current)+'", '
   mystr=mystr+'"jt_watt": "'+str(data_jt_watts)+'", '
   mystr=mystr+'"jt_soc": "'+str(data_jt_soc)+'", '
   mystr=mystr+'"jt_ar": "'+str(data_jt_ah_remaining)+'", '
   mystr=mystr+'"jt_cum_charge_kwh": "'+str(data_jt_tot_charge)+'", '
   mystr=mystr+'"jt_mir": "'+str(data_jt_min_remaining)+'", '
   mystr=mystr+'"jt_resi": "'+str(data_jt_resi)+'", '
   mystr=mystr+'"jt_temp": "'+str(data_jt_temp)+'"}'
   ident1=str(calc_mod)
   ident1=ident1.strip()
   ident2=str(calc_sof)
   ident2=ident2.strip()
   ident3=str(calc_ser)
   ident3=ident3.strip()
   topic="J_"+ident1+"_"+ident2+"_"+ident3+"/status"
   msg=mystr
   #print (topic,msg)

else:
   sys.exit(1)



client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect(broker, port, 60)


if __name__ == "__main__":
    client.loop_forever()


