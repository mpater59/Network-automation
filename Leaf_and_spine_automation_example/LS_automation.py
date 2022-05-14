import yaml
from netmiko import ConnectHandler

stream = open("config.yaml", 'r')
devices = yaml.load_all(stream, Loader=yaml.SafeLoader)
"""
for counter, device in enumerate(devices):
    print(f"\nDevice {counter + 1}. - test:")
    for key, value in device.items():
        print(key + " : " + str(value))
"""
deviceConnection = []
for device in devices:
    deviceConnectionTemp = {
        "device_type": device.get("device type"),
        "ip": device.get("ip address"),
        "username": device.get("username"),
        "password": device.get("password"),
        "secret": device.get("secret"),
        "port": device.get("port"),
        "verbose": True
    }
    deviceConnection.append(deviceConnectionTemp)

for device in deviceConnection:
    connection = ConnectHandler(**device)
    output = connection.send_command(device[9])
    if len(output):
        print(output)
    connection.disconnect()
