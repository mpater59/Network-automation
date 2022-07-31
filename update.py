import sys
from socket import socket
from datetime import datetime

import netmiko
import paramiko
import yaml
from netmiko import ConnectHandler
import pymongo

from Update_Database.ospf import updateOSPF
from Update_Database.interfaces import updateInterfaces
from Update_Database.interfaces import updateLoopback
from Update_Database.bgp import updateBGP
from Update_Database.vlanBridgeVxlan import updateVLAN
from Update_Database.vlanBridgeVxlan import updateBridge
from Update_Database.vlanBridgeVxlan import updateVxLAN
from Update_Database.other import updateHostname

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]

stream = open("known_devices.yaml", 'r')
devicesTemp = yaml.load_all(stream, Loader=yaml.SafeLoader)
devices = []

for counter, device in enumerate(devicesTemp):
    print(f"Device {counter + 1}.:")
    devices.append(device)
    for key, value in device.items():
        print(key + " : " + str(value))
    print()

deviceConnection = []

for counter, device in enumerate(devices):
    deviceConnection.append({
        "device_type": device.get("device type"),
        "ip": device.get("ip address"),
        "username": device.get("username"),
        "password": device.get("password"),
        "secret": device.get("secret"),
        "port": device.get("port"),
        "verbose": True
    })


configurationList = {}
now = datetime.now()
configurationList["time"] = now.strftime("%Y/%m/%d %H:%M:%S")
configurationList["status"] = "unverified"
configurationList["active"] = True
"""
text_file = open("test_configuration2", "r")
output = text_file.read()
text_file.close()
print(output)
outputList = output.splitlines()
print("\nTesting!!!\n")

configurationList.update(updateHostname(outputList))
configurationList.update(updateInterfaces(outputList))
configurationList.update(updateLoopback(outputList))
configurationList.update(updateOSPF(outputList))
configurationList.update(updateBGP(outputList))
configurationList.update(updateVLAN(outputList))
configurationList.update(updateBridge(outputList))
configurationList.update(updateVxLAN(outputList))

for configuration in configurationList:
    print(configuration)

dbPush = mycol.insert_one(configurationList)
print(dbPush.inserted_id)
"""

for counter, device in enumerate(deviceConnection):
    for trial in range(3):
        try:
            connection = ConnectHandler(**device)
            output = connection.send_command("net show configuration")
            print(output)
            outputList = output.splitlines()
            configurationList[f"device {counter + 1}"] = {}
            configurationList[f"device {counter + 1}"].update(updateHostname(outputList))
            configurationList[f"device {counter + 1}"].update(updateInterfaces(outputList))
            configurationList[f"device {counter + 1}"].update(updateLoopback(outputList))
            configurationList[f"device {counter + 1}"].update(updateOSPF(outputList))
            configurationList[f"device {counter + 1}"].update(updateBGP(outputList))
            configurationList[f"device {counter + 1}"].update(updateVLAN(outputList))
            configurationList[f"device {counter + 1}"].update(updateBridge(outputList))
            configurationList[f"device {counter + 1}"].update(updateVxLAN(outputList))
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}.")
        except socket.timeout:
            print(f"Timeout - {trial + 1}.")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}.")

for key, value in configurationList.items():
    print(key + " : " + str(value))

dbPush = mycol.insert_one(configurationList)
print(dbPush.inserted_id)
