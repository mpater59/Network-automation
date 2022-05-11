import socket

import netmiko.ssh_exception
import paramiko.buffered_pipe
from netmiko import ConnectHandler

staticRoutes = open("aristaConfig.txt", "r")
routerKeys = []
routerVals = []
routerCounter = 0
for line in staticRoutes:
    if "hostname:" in line:
        routerKeysTemp = []
        routerValsTemp = []
        routerKeys.append(routerKeysTemp)
        routerVals.append(routerValsTemp)
        routerCounter += 1
    if ":" in line and "#" not in line:
        key, val = map(str.strip, line.split(":"))
        routerKeys[routerCounter - 1].append(key)
        routerVals[routerCounter - 1].append(val)

routers = []
for x in range(routerCounter):
    routersTemp = []
    routers.append(routersTemp)
    interfacesName = []
    interfacesAddress = []
    loopbackName = []
    loopbackAddress = []
    staticAddress = []
    ospf = []
    maxLength = len(routerKeys[x])
    for i, key in enumerate(routerKeys[x]):
        if "hostname" in key:
            routers[x].append(routerVals[x][i])
        elif "eth" in key:
            interfacesName.append(key)
            interfacesAddress.append(routerVals[x][i])
        elif "loopback" in key:
            loopbackName.append(key)
            loopbackAddress.append(routerVals[x][i])
        elif "static" in key:
            staticAddressTemp = [routerVals[x][i]]
            for n in range(i + 1, maxLength):
                if "int" in routerKeys[x][n]:
                    staticAddressTemp.append(routerVals[x][n])
                else:
                    break
            staticAddress.append(staticAddressTemp)
        elif "ospf" in key:
            networks = []
            passiveInts = []
            ospf.append(routerVals[x][i])
            for n in range(i + 1, maxLength):
                if "router-id" in routerKeys[x][n]:
                    ospf.append(routerVals[x][n])
                elif "network" in routerKeys[x][n]:
                    networks.append(routerVals[x][n])
                elif "passive int" in routerKeys[x][n]:
                    passiveInts.append(routerVals[x][n])
                else:
                    break
            ospf.append(networks)
            ospf.append(passiveInts)
    routers[x].append(interfacesName)
    routers[x].append(interfacesAddress)
    routers[x].append(loopbackName)
    routers[x].append(loopbackAddress)
    routers[x].append(staticAddress)
    routers[x].append(ospf)

devices = []
cli = []
output = []

for device in routerVals:
    deviceTemp = {
        "device_type": "arista_eos",
        "ip": device[1],
        "username": device[2],
        "password": device[3],
        "secret": device[4],
        "port": device[5],
        "verbose": True,
        "session_log": "log.txt"
    }
    devices.append(deviceTemp)

for x, router in enumerate(routers):
    cliTemp = []
#    if len(router[0]):
#        cliTemp.append(f"hostname {router[0]}")
    if len(router[1]):
        for counter, interface in enumerate(router[1]):
            cliTemp.append(f"interface {interface}")
            cliTemp.append("no ip address")
            if "delete" not in router[2][counter]:
                cliTemp.append("no switchport")
                cliTemp.append(f"ip address {router[2][counter]}")
                cliTemp.append("no shutdown")
            cliTemp.append("exit")
    if len(router[3]):
        for counter, lo in enumerate(router[3]):
            cliTemp.append(f"no interface {lo}")
            if "delete" not in router[4][counter]:
                cliTemp.append(f"interface {lo}")
                cliTemp.append(f"ip address {router[4][counter]}")
                cliTemp.append("no shutdown")
                cliTemp.append("exit")
    if len(router[5]):
        for staticRoute in router[5]:
            if len(staticRoute) > 1:
                cliTemp.append(f"no ip route {staticRoute[0]}")
                for addressRoute in staticRoute[1:len(staticRoute)]:
                    cliTemp.append(f"ip route {staticRoute[0]} {addressRoute}")
    if len(router[6]):
        cliTemp.append("ip routing")
        cliTemp.append(f"no router ospf {router[6][0]}")
        cliTemp.append(f"router ospf {router[6][0]}")
        if len(router[6][1]):
            cliTemp.append(f"router-id {router[6][1]}")
        if len(router[6][2]):
            for network in router[6][2]:
                cliTemp.append(f"network {network}")
        if len(router[6][3]):
            for interface in router[6][3]:
                cliTemp.append(f"passive-interface {interface}")
        cliTemp.append("exit")
    cliTemp.append("copy running-config startup-config")

    cli.append(cliTemp)

for counter, device in enumerate(devices):
    for trial in range(5):
        try:
            connection = ConnectHandler(**device)
            connection.enable()
            connection.config_mode()
            if len(routers[counter][0]):
                connection.send_command(f"hostname {routers[counter][0]}")
                connection.set_base_prompt()
            output = connection.send_config_set(cli[counter])
            print(output)
            print(connection.send_command("sh run"))
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"{trial + 1}. timeout")
        except socket.timeout:
            print(f"{trial + 1}. timeout")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"{trial + 1}. timeout")
