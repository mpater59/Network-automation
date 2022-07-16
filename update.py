import sys
from socket import socket

import netmiko
import paramiko
import yaml
from netmiko import ConnectHandler


def updateOSPF(configuration_list):
    for line in configuration_list:
        if line is "router osp":
            print("OSPF detect")


stream = open("known_devices.yaml", 'r')
devicesTemp = yaml.load_all(stream, Loader=yaml.SafeLoader)
devices = []
for counter, device in enumerate(devicesTemp):
    print(f"Device {counter + 1}.:")
    devices.append(device)
    for key, value in device.items():
        print(key + " : " + str(value))
    print()

commands = ["net show configuration"]
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

for counter, device in enumerate(deviceConnection):
    for trial in range(3):
        try:
            connection = ConnectHandler(**device)
            output = connection.send_config_set(commands)
            # print(output)
            outputList = output.splitlines()
            updateOSPF(outputList)
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}.")
        except socket.timeout:
            print(f"Timeout - {trial + 1}.")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}.")
