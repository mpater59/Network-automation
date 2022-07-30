import sys
from socket import socket

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


configurationList = []
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
            configurationList.append({})
            configurationList[counter].update(updateInterfaces(outputList))
            configurationList[counter].update(updateLoopback(outputList))
            configurationList[counter].update(updateOSPF(outputList))
            configurationList[counter].update(updateBGP(outputList))
            configurationList[counter].update(updateVLAN(outputList))
            configurationList[counter].update(updateBridge(outputList))
            configurationList[counter].update(updateVxLAN(outputList))
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}.")
        except socket.timeout:
            print(f"Timeout - {trial + 1}.")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}.")

for configuration in configurationList:
    print(configuration)
    print()
