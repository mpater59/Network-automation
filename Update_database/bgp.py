import re

from other import check_if_exists
from other import key_exists


def updateBGP(configuration):
    bgp = {"bgp": {}}
    bgp_break = False
    for i, line in enumerate(configuration):
        if re.search("^router bgp [\d]", line):
            iter_skip = 1
            as_number = line.split(" ")[2]
            bgp["bgp"]["as"] = as_number
            bgp["bgp"]["neighbors"] = {}
            while True:
                if re.search("^  bgp router-id [\w]", configuration[i + iter_skip]):
                    temp_split = configuration[i + iter_skip].split(" ")
                    router_id = temp_split[4]
                    bgp["bgp"]["router-id"] = router_id
                elif re.search("^  neighbor \S+ remote-as [\d]", configuration[i + iter_skip]):
                    neighbor = configuration[i + iter_skip].split(" ")[3]
                    remote_as = configuration[i + iter_skip].split(" ")[5]
                    if bgp.get("bgp").get("neighbors").get(neighbor) is None:
                        bgp["bgp"]["neighbors"][neighbor] = {}
                    bgp["bgp"]["neighbors"][neighbor]["remote"] = remote_as
                elif re.search("^  neighbor \S+ update-source [\w]", configuration[i + iter_skip]):
                    neighbor = configuration[i + iter_skip].split(" ")[3]
                    update_source = configuration[i + iter_skip].split(" ")[5]
                    if bgp.get("bgp").get("neighbors").get(neighbor) is None:
                        bgp["bgp"]["neighbors"][neighbor] = {}
                    bgp["bgp"]["neighbors"][neighbor]["update"] = update_source
                elif re.search("address-family l2vpn evpn", configuration[i + iter_skip]):
                    while True:
                        if re.search("^    neighbor \S+ activate", configuration[i + iter_skip]):
                            neighbor = configuration[i + iter_skip].split(" ")[5]
                            if bgp.get("bgp").get("neighbors").get(neighbor) is None:
                                bgp["bgp"]["neighbors"][neighbor] = {}
                            bgp["bgp"]["neighbors"][neighbor]["activate evpn"] = True
                        elif re.search("^    neighbor \S+ route-reflector-client", configuration[i + iter_skip]):
                            neighbor = configuration[i + iter_skip].split(" ")[5]
                            if bgp.get("bgp").get("neighbors").get(neighbor) is None:
                                bgp["bgp"]["neighbors"][neighbor] = {}
                            bgp["bgp"]["neighbors"][neighbor]["evpn rrc"] = True
                        elif re.search("^    advertise-all-vni", configuration[i + iter_skip]):
                            bgp["bgp"]["advertise-all-vni"] = True
                        iter_skip += 1
                        if not re.search("^    .+", configuration[i + iter_skip]):
                            if configuration[i + iter_skip] != '' or configuration[i + iter_skip] is None:
                                iter_skip -= 1
                                break
                elif re.search("address-family ipv4 unicast", configuration[i + iter_skip]):
                    while True:
                        if re.search("^    neighbor \S+ route-reflector-client", configuration[i + iter_skip]):
                            neighbor = configuration[i + iter_skip].split(" ")[5]
                            if bgp.get("bgp").get("neighbors").get(neighbor) is None:
                                bgp["bgp"]["neighbors"][neighbor] = {}
                            bgp["bgp"]["neighbors"][neighbor]["rrc"] = True
                        elif re.search("^    neighbor \S+ next-hop-self", configuration[i + iter_skip]):
                            neighbor = configuration[i + iter_skip].split(" ")[5]
                            if key_exists(bgp, "bgp", "neighbors", neighbor) is False:
                                bgp["bgp"]["neighbors"][neighbor] = {}
                            bgp["bgp"]["neighbors"][neighbor]["next-hop-self"] = True
                        elif re.search("^    network \S+", configuration[i + iter_skip]):
                            network = configuration[i + iter_skip].split(" ")[5]
                            if key_exists(bgp, "bgp", "networks") is False:
                                bgp["bgp"]["networks"] = []
                            if check_if_exists(network, bgp["bgp"]["networks"]):
                                bgp["bgp"]["networks"].append(network)
                        iter_skip += 1
                        if not re.search("^    .*", configuration[i + iter_skip]):
                            if configuration[i + iter_skip] != '':
                                iter_skip -= 1
                                break
                iter_skip += 1
                if not re.search("^  .*", configuration[i + iter_skip]):
                    if configuration[i + iter_skip] != '':
                        bgp_break = True
                        break
        elif bgp_break is True:
            break
    return bgp
