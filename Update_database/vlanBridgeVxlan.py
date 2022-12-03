import re

from Other.other import check_if_exists
from Other.other import key_exists


def updateVLAN(configuration):
    vlan = {"vlan": {}}
    for i, line in enumerate(configuration):
        if re.search("^interface vlan[\d]", line):
            iter_skip = 1
            vlan_id = line.split("vlan")[1]
            vlan["vlan"][vlan_id] = {}
            while True:
                if re.search("^  address [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    address = temp_split[3]
                    if vlan.get("vlan").get(vlan_id).get("ip address") is None:
                        vlan["vlan"][vlan_id]["ip address"] = []
                    vlan["vlan"][vlan_id]["ip address"].append(address)
                elif re.search("^  vlan-id [\d]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    vid = temp_split[3]
                    vlan["vlan"][vlan_id]["vlan-id"] = vid
                elif re.search("^  vlan-raw-device bridge", configuration[i + iter_skip]):
                    vlan["vlan"][vlan_id]["vlan-raw-device bridge"] = True
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        break
    return vlan


def updateBridge(configuration):
    bridge = {"bridge": {}}
    bridge_break = False
    for i, line in enumerate(configuration):
        if re.search("^interface [\w]", line):
            iter_skip = 1
            interface = line.split(" ")[1]
            if interface == "bridge":
                while True:
                    if re.search("^  bridge-ports [\w]", configuration[i + iter_skip]):
                        temp_split = configuration[i + iter_skip].split("bridge-ports ")
                        ports = temp_split[1].split(" ")
                        bridge["bridge"]["ports"] = []
                        for port in ports:
                            bridge["bridge"]["ports"].append(port)
                    elif re.search("^  bridge-vids [\w]", configuration[i + iter_skip]):
                        temp_split = configuration[i + iter_skip].split("bridge-vids ")
                        vids = temp_split[1].split(" ")
                        bridge["bridge"]["vids"] = {}
                        for vid in vids:
                            bridge["bridge"]["vids"][vid] = {}
                    elif re.search("^  bridge-vlan-aware [\w]", configuration[i + iter_skip]):
                        temp_split = configuration[i + iter_skip].split(" ")
                        vlan_aware = temp_split[3]
                        if vlan_aware == "yes":
                            vlan_aware = True
                        else:
                            vlan_aware = False
                        bridge["bridge"]["bridge-vlan-aware"] = vlan_aware
                    iter_skip += 1
                    if not re.search("^  .*", configuration[i + iter_skip]):
                        if configuration[i + iter_skip] != '':
                            bridge_break = True
                            break
        if bridge_break is True:
            break
    for i, line in enumerate(configuration):
        if re.search("^interface [\w]", line):
            iter_skip = 1
            interface = line.split(" ")[1]
            if interface != "bridge":
                while True:
                    if re.search("^  bridge-access [\d]", configuration[i + iter_skip]):
                        temp_split = configuration[i + iter_skip].split("bridge-access ")
                        vid = temp_split[1]
                        if bridge.get("bridge").get("vids").get(vid).get("bridge access") is None:
                            bridge["bridge"]["vids"][vid]["bridge access"] = []
                        bridge["bridge"]["vids"][vid]["bridge access"].append(interface)
                    iter_skip += 1
                    if not re.search("^  .*", configuration[i + iter_skip]):
                        if configuration[i + iter_skip] != '':
                            break
    return bridge


def updateVxLAN(configuration):
    vxlan = {"vxlan": {}}
    vxlan["vxlan"]["vnis"] = {}
    for i, line in enumerate(configuration):
        if re.search("^interface vni[\d]", line):
            iter_skip = 1
            vni = line.split(" ")[1]
            vxlan["vxlan"]["vnis"][vni] = {}
            while True:
                if re.search("^  bridge-learning [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    learning = temp_split[3]
                    if learning == "off":
                        learning = False
                    else:
                        learning = True
                    vxlan["vxlan"]["vnis"][vni]["bridge learning"] = learning
                elif re.search("^  vxlan-id [\d]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    vxlan_id = temp_split[3]
                    vxlan["vxlan"]["vnis"][vni]["id"] = vxlan_id
                elif re.search("^  vxlan-local-tunnelip [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    local_tunnelip = temp_split[3]
                    vxlan["vxlan"]["vnis"][vni]["local-tunnelip"] = local_tunnelip
                elif re.search("^  bridge-access [\d]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    bridge_access = temp_split[3]
                    vxlan["vxlan"]["vnis"][vni]["bridge access"] = bridge_access
                elif re.search("^  vxlan-remoteip [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    remoteip = temp_split[3]
                    if key_exists(vxlan, "vxlan", "vnis", vni, "remoteip") is False:
                        vxlan["vxlan"]["vnis"][vni]["remoteip"] = []
                    if check_if_exists(remoteip, vxlan["vxlan"]["vnis"][vni]["remoteip"]) is False:
                        vxlan["vxlan"]["vnis"][vni]["remoteip"].append(remoteip)
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        break
    return vxlan
