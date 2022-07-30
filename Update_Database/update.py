import sys
from socket import socket
from datetime import datetime

import netmiko
import paramiko
import yaml
from netmiko import ConnectHandler
from ospf import updateOSPF
from interfaces import updateInterfaces
from interfaces import updateLoopback
from bgp import updateBGP
from vlanBridgeVxlan import updateVLAN
from vlanBridgeVxlan import updateBridge
from vlanBridgeVxlan import updateVxLAN
from other import updateHostname


stream = open("../known_devices.yaml", 'r')
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
"""
text_file = open("test_configuration2", "r")
output = text_file.read()
text_file.close()
print(output)
outputList = output.splitlines()
print("\nTesting!!!\n")

configurationList.append(updateInterfaces(outputList))
configurationList.append(updateLoopback(outputList))
configurationList.append(updateOSPF(outputList))
configurationList.append(updateBGP(outputList))
configurationList.append(updateVLAN(outputList))
configurationList.append(updateBridge(outputList))
configurationList.append(updateVxLAN(outputList))

for configuration in configurationList:
    print(configuration)
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

configurations = []
for counter, configuration in enumerate(configurationList):
    print(f"Device {counter + 1}.:")
    configurations.append(configuration)
    for key, value in configuration.items():
        print(key + " : " + str(value))
    print()
