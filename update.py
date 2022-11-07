from socket import socket
import datetime

import netmiko
import paramiko
import yaml
from netmiko import ConnectHandler
import pymongo
from bson import ObjectId

from Update_database.ospf import updateOSPF
from Update_database.interfaces import updateInterfaces
from Update_database.interfaces import updateLoopback
from Update_database.bgp import updateBGP
from Update_database.vlanBridgeVxlan import updateVLAN
from Update_database.vlanBridgeVxlan import updateBridge
from Update_database.vlanBridgeVxlan import updateVxLAN
from Update_database.other import updateHostname

from other import key_exists

myclient = pymongo.MongoClient("mongodb://192.168.1.11:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]

stream = open("devices.yaml", 'r')
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
        "device_type": device.get("machine type"),
        "ip": device.get("ip address"),
        "username": device.get("username"),
        "password": device.get("password"),
        "secret": device.get("secret"),
        "port": device.get("port"),
        "verbose": True
    })

"""
configurationList = {}
configurationList["date"] = datetime.datetime.now().replace(microsecond=0)
configurationList["status"] = "unverified"
configurationList["active"] = True
configurationList["devices"] = {}

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

config_id = ObjectId()
config_time = datetime.datetime.now().replace(microsecond=0)

for counter, device in enumerate(deviceConnection):
    for trial in range(3):
        try:
            configurationList = {}
            creation_time = datetime.datetime.now().replace(microsecond=0)
            configurationList["creation date"] = creation_time
            configurationList["update date"] = None
            configurationList["config id"] = config_id
            configurationList["config update time"] = config_time
            configurationList["device type"] = devices[counter].get("device type")
            configurationList["site"] = devices[counter].get("site")
            configurationList["status"] = "unverified"
            configurationList["active"] = True
            configurationList["configuration"] = {}

            connection = ConnectHandler(**device)
            output = connection.send_command("net show configuration")
            print(output)
            outputList = output.splitlines()

            configurationList["configuration"].update(updateHostname(outputList))
            configurationList["configuration"].update(updateInterfaces(outputList))
            configurationList["configuration"].update(updateLoopback(outputList))
            configurationList["configuration"].update(updateOSPF(outputList))
            configurationList["configuration"].update(updateBGP(outputList))
            configurationList["configuration"].update(updateVLAN(outputList))
            configurationList["configuration"].update(updateBridge(outputList))
            configurationList["configuration"].update(updateVxLAN(outputList))
            configurationList["configuration"]["commit"] = True
            connection.disconnect()

            query = {"active": True, "configuration.hostname": devices[counter].get("hostname"),
                     "site": devices[counter].get("site")}
            newValues = {"$set": {"active": False}}
            modified = False
            if mycol.count_documents(query) > 0:
                old_config = mycol.find(query).sort([("config update time", -1), ("creation date", -1)])[0]
                if key_exists(old_config, "configuration"):
                    if old_config["configuration"] == configurationList["configuration"]:
                        query = {"active": True, "configuration.hostname": devices[counter].get("hostname"),
                                 "site": devices[counter].get("site"), "_id": {"$ne": ObjectId(old_config["_id"])}}
                        dbUpdate1 = mycol.update_many(query, newValues)
                        newValues = {"$set": {"update date": creation_time, "config id": config_id}}
                        query = {"active": True, "configuration.hostname": devices[counter].get("hostname"),
                                 "site": devices[counter].get("site")}
                        dbUpdate2 = mycol.update_many(query, newValues)
                        newValues = {"$set": {"config update time": config_time}}
                        dbUpdate3 = mycol.update_many(query, newValues)
                        modified = True
                    else:
                        dbUpdate = mycol.update_many(query, newValues)
                else:
                    dbUpdate = mycol.update_many(query, newValues)
            if modified is False:
                dbInsert = mycol.insert_one(configurationList)
                print(f"New ID: " + str(dbInsert.inserted_id))

            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}.")
        except socket.timeout:
            print(f"Timeout - {trial + 1}.")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}.")
