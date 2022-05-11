from netmiko import ConnectHandler

staticRoutes = open("cumulusConfig.txt", "r")
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
    addLoopback = []
    delLoopback = []
    addStaticAddress = []
    delStaticAddress = []
    ospf = []
    maxLength = len(routerKeys[x])
    for i, key in enumerate(routerKeys[x]):
        if "hostname" in key:
            routers[x].append(routerVals[x][i])
        elif ("swp" or "eth") in key:
            interfacesName.append(key)
            interfacesAddress.append(routerVals[x][i])
        elif "loopback" in key:
            if "add" in key:
                addLoopback.append(routerVals[x][i])
            elif "del" in key:
                delLoopback.append(routerVals[x][i])
        elif "static" in key:
            addStaticAddressTemp = []
            delStaticAddressTemp = []
            addStaticAddressTemp.append(routerVals[x][i])
            delStaticAddressTemp.append(routerVals[x][i])
            for n in range(i + 1, maxLength):
                if "int" not in routerKeys[x][n]:
                    break
                elif "add" in routerKeys[x][n]:
                    addStaticAddressTemp.append(routerVals[x][n])
                elif "del" in routerKeys[x][n]:
                    delStaticAddressTemp.append(routerVals[x][n])
            addStaticAddress.append(addStaticAddressTemp)
            delStaticAddress.append(delStaticAddressTemp)
        elif "ospf" in key:
            networks = []
            passiveInts = []
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
        i += 1
    routers[x].append(interfacesName)
    routers[x].append(interfacesAddress)
    routers[x].append(addLoopback)
    routers[x].append(delLoopback)
    routers[x].append(addStaticAddress)
    routers[x].append(delStaticAddress)
    routers[x].append(ospf)

devices = []
cli = []
output = []

for device in routerVals:
    deviceTemp = {
        "device_type": "linux",
        "ip": device[1],
        "username": device[2],
        "password": device[3],
        "secret": device[4],
        "port": device[5],
        "verbose": True
    }
    devices.append(deviceTemp)

for x, router in enumerate(routers):
    cliTemp = []
    if len(router[0]):
        cliTemp.append("net del hostname")
        cliTemp.append(f"net add hostname {router[0]}")
    if len(router[1]):
        for counter, swp in enumerate(router[1]):
            cliTemp.append(f"net del interface {swp}")
            cliTemp.append(f"net add interface {swp} ip address {router[2][counter]}")
    if len(router[3]):
        for lo in router[3]:
            cliTemp.append(f"net add loopback lo ip address {lo}")
    if len(router[4]):
        for lo in router[4]:
            cliTemp.append(f"net del loopback lo ip address {lo}")
    if len(router[5]):
        for staticRoute in router[5]:
            if len(staticRoute) > 1:
                for addressRoute in staticRoute[1:len(staticRoute)]:
                    cliTemp.append(f"net add routing route {staticRoute[0]} {addressRoute}")
    if len(router[6]):
        for staticRoute in router[6]:
            if len(staticRoute) > 1:
                for addressRoute in staticRoute[1:len(staticRoute)]:
                    cliTemp.append(f"net del routing route {staticRoute[0]} {addressRoute}")
    if len(router[7]):
        cliTemp.append("net del ospf")
        cliTemp.append(f"net add ospf router-id {router[7][0]}")
        for network in router[7][1]:
            cliTemp.append(f"net add ospf network {network}")
        for interface in router[7][2]:
            cliTemp.append(f"net add ospf passive-interface {interface}")
    cliTemp.append(f"net commit")

    cli.append(cliTemp)

for counter, device in enumerate(devices):
    connection = ConnectHandler(**device)
    for command in cli[counter]:
        output = connection.send_command(command)
        if len(output):
            print(output)
    connection.disconnect()
