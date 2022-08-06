import re


def updateOSPF(configuration):
    ospf = {"ospf": {}}
    for i, line in enumerate(configuration):
        if line == "router ospf":
            iter_skip = 1
            while True:
                if "ospf router-id" in configuration[i + iter_skip]:
                    temp_split = configuration[i + iter_skip].split(" ")
                    ospf["ospf"]["router-id"] = temp_split[4]
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] == '':
                        break
        elif re.search("^interface swp[\d]", line) or re.search("^interface lo", line):
            iter_skip = 1
            interface = line.split(" ")[1]
            if ospf.get("ospf").get("interfaces") is None:
                ospf["ospf"]["interfaces"] = {}
            ospf["ospf"]["interfaces"][interface] = {}
            while True:
                if "ip ospf area" in configuration[i + iter_skip]:
                    temp_split = configuration[i + iter_skip].split(" ")
                    area = temp_split[5]
                    ospf["ospf"]["interfaces"][interface]["area"] = area
                elif "ip ospf passive" in configuration[i + iter_skip]:
                    ospf["ospf"]["interfaces"][interface]["passive interface"] = True
                elif "ipv6 ospf6 passive" in configuration[i + iter_skip]:
                    ospf["ospf"]["interfaces"][interface]["passive interface ipv6"] = True
                elif "ip ospf network" in configuration[i + iter_skip]:
                    temp_split = configuration[i + iter_skip].split(" ")
                    network = temp_split[5]
                    ospf["ospf"]["interfaces"][interface]["network"] = network
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        break
    return ospf
