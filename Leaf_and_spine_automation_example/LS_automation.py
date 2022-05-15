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
commands = []
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
    commandsTemp = []
    if device.get("node type") == "FRR":
        commandsTemp.append("vtysh")
        commandsTemp.append("conf t")
        for interface in device.get("interfaces"):
            commandsTemp.append(f"int {interface}")
            for ipAddr in device.get("interfaces").get(interface).get("add ip address"):
                if ipAddr:
                    commandsTemp.append(f"ip address {ipAddr}")
            for ipAddr in device.get("interfaces").get(interface).get("del ip address"):
                if ipAddr:
                    commandsTemp.append(f"no ip address {ipAddr}")
            if device.get("interfaces").get(interface).get("shutdown"):
                commandsTemp.append("shutdown")
            elif not device.get("interfaces").get(interface).get("shutdown"):
                commandsTemp.append("no shutdown")
            commandsTemp.append("exit")
    commandsTemp.append("exit")
    if device.get("copy to startup-config"):
        commandsTemp.append("copy running-config startup-config")
    commandsTemp.append("show running-config")
    commands.append(commandsTemp)

print(commands)

for counter, device in enumerate(deviceConnection):
    connection = ConnectHandler(**device)
    output = connection.send_config_set(commands[counter])
    print(output)
    connection.disconnect()
