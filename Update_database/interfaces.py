import re

from Other.other import key_exists
from Other.other import check_if_exists


def updateInterfaces(configuration):
    interfaces = {"interfaces": {}}
    for i, line in enumerate(configuration):
        if re.search("^interface swp[\d]", line):
            iter_skip = 1
            interface = line.split(" ")[1]
            interfaces["interfaces"][interface] = {}
            while True:
                if re.search("^  address [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    address = temp_split[3]
                    if interfaces.get("interfaces").get(interface).get("ip address") is None:
                        interfaces["interfaces"][interface]["ip address"] = []
                    interfaces["interfaces"][interface]["ip address"].append(address)
                elif re.search("^  link-down [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    link_down = temp_split[3]
                    if link_down == "yes":
                        shutdown = True
                    else:
                        shutdown = False
                    interfaces["interfaces"][interface]["shutdown"] = shutdown
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        break
    return interfaces


def updateLoopback(configuration):
    loopback = {"loopback": {}}
    loopback_break = False
    for i, line in enumerate(configuration):
        if re.search("^interface lo", line):
            iter_skip = 1
            while True:
                if re.search("^  address [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    address = temp_split[3]
                    if loopback.get("loopback").get("ip address") is None:
                        loopback["loopback"]["ip address"] = []
                    loopback["loopback"]["ip address"].append(address)
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        loopback_break = True
                        break
        if loopback_break is True:
            break
    return loopback


def updateInterfacesAgain(config):
    if key_exists(config, "interfaces"):
        temp_int = []
        for interface in config["interfaces"]:
            temp_int.append(interface)
        for interface in temp_int:
            int_exists = True
            if key_exists(config, "interfaces", interface, "ip address") is False:
                if key_exists(config, "bridge", "ports"):
                    if check_if_exists(interface, config["bridge"]["ports"]) is False:
                        int_exists = False
                else:
                    int_exists = False
            if int_exists is False:
                config["interfaces"].pop(interface, None)
                if key_exists(config, "ospf", "interfaces", interface):
                    config["ospf"]["interfaces"].pop(interface, None)
    return config
