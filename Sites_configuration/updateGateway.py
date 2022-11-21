import pymongo
import yaml

from other import key_exists
from other import check_if_exists


stream = open('database_env.yaml', 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def get_neighbor_ports(selected_device, devices_file, site):
    neigh_ports = []

    stream = open("sites.yaml", 'r')
    sites_file = list(yaml.load_all(stream, Loader=yaml.SafeLoader))
    selected_site = None
    for site_file in sites_file:
        if site_file["name"] == site:
            selected_site = site_file
            break
    stream.close()

    if selected_site["name"] is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": selected_site["name"]}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    db_config = None
    if selected_device["hostname"] is None:
        print("Enter name of device!")
        exit()
    else:
        query = {"site": selected_site["name"], "active": True, "device hostname": selected_device["hostname"]}
        if col_configs.count_documents(query) > 0:
            db_config = col_configs.find(query).sort("last update datetime", -1)[0].get("configuration")
        else:
            print(f"Couldn't find active configuration for device {selected_device['hostname']}!")
            exit()

    device_config_id = selected_device["device information"]["id"]
    site_id = selected_site["first octet of subnet ip address"]

    neighbors = []
    for device_file in devices_file:
        if device_file["device information"]["type"] == "spine":
            neighbors.append(device_file)

    border_as_ip_addr = []
    neigh_as = []

    for as_id in selected_device["as neighbors"]:
        for addr in selected_device["as neighbors"][as_id]["ip address"]:
            neigh_as.append(as_id)
            ip_addr_split = addr.split('/')[0].split('.')
            if ip_addr_split[-1] == '2':
                ip_addr_split[-1] = '1'
            else:
                ip_addr_split[-1] = '2'
            ip_addr = ""
            for x, char in enumerate(ip_addr_split):
                if (x + 1) < len(ip_addr_split):
                    ip_addr += f'{char}.'
                else:
                    ip_addr += f'{char}/30'
            border_as_ip_addr.append(ip_addr)

    for border, as_id in zip(border_as_ip_addr, neigh_as):
        if key_exists(db_config, "interfaces"):
            for interface in db_config["interfaces"]:
                db_int = db_config["interfaces"][interface]
                if key_exists(db_int, "ip address") and db_int["ip address"] == [border]:
                    if check_if_exists(interface, neigh_ports) is False:
                        neigh_ports.append({interface: {"as": as_id, "ip address": border}})

    for neighbor in neighbors:
        neigh_ip_addr = f'{site_id}.{neighbor["device information"]["id"]}.{200 + device_config_id}.2/30'
        if key_exists(db_config, "interfaces"):
            for interface in db_config["interfaces"]:
                db_int = db_config["interfaces"][interface]
                if key_exists(db_int, "ip address") and db_int["ip address"] == [neigh_ip_addr]:
                    if check_if_exists(interface, neigh_ports) is False:
                        neigh_ports.append({interface: {"hostname": neighbor["hostname"]}})

    return neigh_ports


def update_gateway(selected_device, devices_file, selected_site, db_config=None, active=False, expand=False):

    neighbors = []

    for device_file in devices_file:
        if device_file["device information"]["type"] == "spine":
            neighbors.append(device_file)

    device_type = selected_device["device information"]["type"]
    device_config_id = selected_device["device information"]["id"]

    border_as_ip_addr = []
    neigh_as_ip_addr = []
    neigh_as = []

    for as_id in selected_device["as neighbors"]:
        for addr in selected_device["as neighbors"][as_id]["ip address"]:
            neigh_as_ip_addr.append(addr)
            neigh_as.append(as_id)
            ip_addr_split = addr.split('/')[0].split('.')
            if ip_addr_split[-1] == '2':
                ip_addr_split[-1] = '1'
            else:
                ip_addr_split[-1] = '2'
            ip_addr = ""
            for x, char in enumerate(ip_addr_split):
                if (x + 1) < len(ip_addr_split):
                    ip_addr += f'{char}.'
                else:
                    ip_addr += f'{char}/30'
            border_as_ip_addr.append(ip_addr)

    device_swp = selected_device["number of ports"]
    site_as = selected_site["bgp as"]
    site_ospf = selected_site["ospf area"]
    site_id = selected_site["first octet of subnet ip address"]
    device_id = f'1.1.{site_id}.{200+device_config_id}'

    config = {}

    # update hostname
    if key_exists(db_config, "hostname") is False:
        if db_config is not None:
            db_config["hostname"] = f"{selected_device['hostname']}"
        config["hostname"] = f"{selected_device['hostname']}"

    # update interfaces
    taken_ports = []
    neigh_ports = []
    border_ports = []

    for neighbor in neighbors:
        neigh_ip_addr = f'{site_id}.{neighbor["device information"]["id"]}.{200 + device_config_id}.2/30'
        if active is True and key_exists(db_config, "interfaces"):
            for interface in db_config["interfaces"]:
                db_int = db_config["interfaces"][interface]
                if key_exists(db_int, "ip address") and db_int["ip address"] == [neigh_ip_addr]:
                    if check_if_exists(interface, neigh_ports) is False:
                        neigh_ports.append({interface: neighbor["device information"]})
                elif key_exists(db_int, "ip address"):
                    if check_if_exists(db_int["ip address"], border_as_ip_addr) is True:
                        if check_if_exists(interface, border_ports) is False:
                            border_ports.append({interface: neighbor["device information"]})

    # update interface (expand=False)
    if expand is False and key_exists(db_config, "interfaces"):
        neighbors_ports = []
        for neigh_port in neigh_ports:
            neighbors_ports.append(list(neigh_port.keys())[0])
        for border_port in border_ports:
            neighbors_ports.append(list(border_port.keys())[0])
        db_interfaces = []
        for interface in db_config["interfaces"]:
            db_interfaces.append(interface)
        for interface in db_interfaces:
            if check_if_exists(interface, neighbors_ports) is False:
                if key_exists(db_config, "interfaces", interface, "ip address") is True:
                    db_config["interfaces"].pop(interface, None)

    for neighbor in neighbors:
        neigh_ip_addr = f'{site_id}.{neighbor["device information"]["id"]}.{200+device_config_id}.2/30'
        if key_exists(db_config, "interfaces"):
            address_founded = False
            for interface in db_config["interfaces"]:
                db_int = db_config["interfaces"][interface]
                if key_exists(db_int, "ip address") and db_int["ip address"] == [neigh_ip_addr]:
                    db_config["interfaces"][interface].pop("shutdown", None)
                    address_founded = True
                    if check_if_exists(interface, neigh_ports) is False:
                        neigh_ports.append({interface: neighbor["device information"]})
                if check_if_exists(interface, taken_ports) is False:
                    taken_ports.append(interface)
            if address_founded is False:
                free_port = False
                for i in range(device_swp):
                    if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                        db_config["interfaces"].update({f"swp{i + 1}": {"ip address": neigh_ip_addr}})
                        free_port = True
                        if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                            taken_ports.append(f"swp{i + 1}")
                        if check_if_exists(f"swp{i + 1}", neigh_ports) is False:
                            neigh_ports.append({f"swp{i + 1}": neighbor["device information"]})
                        break
                if free_port is False:
                    print(f"Device {selected_device['hostname']} doesn't have free port for {neighbor['hostname']}!")
        elif active is True:
            free_port = False
            if key_exists(db_config, "interfaces") is False:
                db_config["interfaces"] = {}
            for i in range(device_swp):
                if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                    db_config["interfaces"].update({f"swp{i + 1}": {"ip address": neigh_ip_addr}})
                    free_port = True
                    if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                        taken_ports.append(f"swp{i + 1}")
                    if check_if_exists(f"swp{i + 1}", neigh_ports) is False:
                        neigh_ports.append({f"swp{i + 1}": neighbor["device information"]})
                    break
            if free_port is False:
                print(f"Device {selected_device['hostname']} doesn't have free port for {neighbor['hostname']}!")
        else:
            free_port = False
            if key_exists(config, "interfaces") is False:
                config["interfaces"] = {}
            for i in range(device_swp):
                if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                    config["interfaces"].update({f"swp{i + 1}": {"ip address": neigh_ip_addr}})
                    free_port = True
                    if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                        taken_ports.append(f"swp{i + 1}")
                    if check_if_exists(f"swp{i + 1}", neigh_ports) is False:
                        neigh_ports.append({f"swp{i + 1}": neighbor["device information"]})
                    break
            if free_port is False:
                print(f"Device {selected_device['hostname']} doesn't have free port for {neighbor['hostname']}!")

    # update interface gateway
    if device_type == "gateway":
        for border, as_id in zip(border_as_ip_addr, neigh_as):
            if key_exists(db_config, "interfaces"):
                address_founded = False
                for interface in db_config["interfaces"]:
                    db_int = db_config["interfaces"][interface]
                    if key_exists(db_int, "ip address") and db_int["ip address"] == [border]:
                        db_config["interfaces"][interface].pop("shutdown", None)
                        address_founded = True
                        if check_if_exists(interface, border_ports) is False:
                            border_ports.append({interface: {as_id: {"ip address": border}}})
                    if check_if_exists(interface, taken_ports) is False:
                        taken_ports.append(interface)
                if address_founded is False:
                    free_port = False
                    for i in range(device_swp):
                        if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                            db_config["interfaces"].update({f"swp{i + 1}": {"ip address": border}})
                            free_port = True
                            if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                                taken_ports.append(f"swp{i + 1}")
                            if check_if_exists(f"swp{i + 1}", border_ports) is False:
                                border_ports.append({f"swp{i + 1}": {as_id: {"ip address": border}}})
                            break
                    if free_port is False:
                        print(f"Device {selected_device['hostname']} doesn't have free port for AS {as_id} neighbor (ip address: {border})!")
            elif active is True:
                free_port = False
                if key_exists(db_config, "interfaces") is False:
                    db_config["interfaces"] = {}
                for i in range(device_swp):
                    if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                        db_config["interfaces"].update({f"swp{i + 1}": {"ip address": border}})
                        free_port = True
                        if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                            taken_ports.append(f"swp{i + 1}")
                        if check_if_exists(f"swp{i + 1}", border_ports) is False:
                            border_ports.append({f"swp{i + 1}": {as_id: {"ip address": border}}})
                        break
                if free_port is False:
                    print(f"Device {selected_device['hostname']} doesn't have free port for AS {as_id} neighbor (ip address: {border})!")
            else:
                free_port = False
                if key_exists(config, "interfaces") is False:
                    config["interfaces"] = {}
                for i in range(device_swp):
                    if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                        config["interfaces"].update({f"swp{i + 1}": {as_id: {"ip address": border}}})
                        free_port = True
                        if check_if_exists(f"swp{i + 1}", taken_ports) is False:
                            taken_ports.append(f"swp{i + 1}")
                        if check_if_exists(f"swp{i + 1}", border_ports) is False:
                            border_ports.append({f"swp{i + 1}": {as_id: {"ip address": border}}})
                        break
                if free_port is False:
                    print(
                        f"Device {selected_device['hostname']} doesn't have free port for AS {as_id} neighbor (ip address: {border})!")

    # update loopback
    if key_exists(db_config, "loopback", "ip address"):
        if db_config["loopback"]["ip address"] != device_id:
            db_config["loopback"]["ip address"] = [device_id]
    elif active is True:
        db_config["loopback"]["ip address"] = [device_id]
    else:
        config["loopback"] = {"ip address": [device_id]}

    # update ospf
    if key_exists(db_config, "ospf"):
        if key_exists(db_config, "ospf", "router-id"):
            if db_config["ospf"]["router-id"] != device_id:
                db_config["ospf"]["router-id"] = device_id
        else:
            db_config["ospf"]["router-id"] = device_id
        if key_exists(db_config, "ospf", "interfaces"):
            if key_exists(db_config, "ospf", "interfaces", "lo", "area"):
                if db_config["ospf"]["interfaces"]["lo"]["area"] != site_ospf:
                    db_config["ospf"]["interfaces"]["lo"]["area"] = site_ospf
            else:
                db_config["ospf"]["interfaces"]["lo"]["area"] = site_ospf
            for neigh_port in neigh_ports:
                neigh_port = list(neigh_port.keys())[0]
                if key_exists(db_config, "ospf", "interfaces", neigh_port):
                    port = db_config["ospf"]["interfaces"][neigh_port]
                    if key_exists(port, "area"):
                        if port["area"] != site_ospf:
                            port["area"] = site_ospf
                    else:
                        port["area"] = site_ospf
                    if key_exists(port, "network"):
                        if port["network"] != "point-to-point":
                            port["network"] = "point-to-point"
                    else:
                        port["network"] = "point-to-point"
                else:
                    db_config["ospf"]["interfaces"][neigh_port] = {}
                    db_config["ospf"]["interfaces"][neigh_port]["area"] = site_ospf
                    db_config["ospf"]["interfaces"][neigh_port]["network"] = "point-to-point"
        else:
            db_config["ospf"]["interfaces"] = {}
            db_config["ospf"]["interfaces"]["lo"] = {}
            db_config["ospf"]["interfaces"]["lo"]["area"] = site_ospf
            for neigh_port in neigh_ports:
                neigh_port = list(neigh_port.keys())[0]
                db_config["ospf"]["interfaces"].update({neigh_port: {"area": site_ospf, "network": "point-to-point"}})
    elif active is True:
        db_config["ospf"] = {"router-id": device_id}
        db_config["ospf"]["interfaces"] = {}
        db_config["ospf"]["interfaces"]["lo"] = {}
        db_config["ospf"]["interfaces"]["lo"]["area"] = site_ospf
        for neigh_port in neigh_ports:
            neigh_port = list(neigh_port.keys())[0]
            db_config["ospf"]["interfaces"].update({neigh_port: {"area": site_ospf, "network": "point-to-point"}})
    else:
        config["ospf"] = {"router-id": device_id}
        config["ospf"]["interfaces"] = {}
        config["ospf"]["interfaces"]["lo"] = {}
        config["ospf"]["interfaces"]["lo"]["area"] = site_ospf
        for neigh_port in neigh_ports:
            neigh_port = list(neigh_port.keys())[0]
            config["ospf"]["interfaces"].update({neigh_port: {"area": site_ospf, "network": "point-to-point"}})

    # update ospf (expand=False)
    if expand is False and key_exists(db_config, "ospf", "interfaces"):
        neighbors_ports = []
        for neigh_port in neigh_ports:
            neighbors_ports.append(list(neigh_port.keys())[0])
        db_ospf = []
        for interface in db_config["ospf"]["interfaces"]:
            db_ospf.append(interface)
        for interface in db_ospf:
            if check_if_exists(interface, neighbors_ports) is False:
                if key_exists(db_config, "ospf", "interfaces", interface, "area") is True:
                    db_config["ospf"]["interfaces"].pop(interface, None)

    # update bgp
    if key_exists(db_config, "bgp"):
        if key_exists(db_config, "bgp", "as"):
            if db_config["bgp"]["as"] != str(site_as):
                db_config["bgp"]["as"] = str(site_as)
        else:
            db_config["bgp"]["as"] = site_as
        if key_exists(db_config, "bgp", "router-id"):
            if db_config["bgp"]["router-id"] != device_id:
                db_config["bgp"]["router-id"] = device_id
        else:
            db_config["bgp"]["router-id"] = device_id
        for neighbor in neighbors:
            neigh_exists = False
            bgp_id_neigh = f'1.1.1.{neighbor["device information"]["id"]}'
            if key_exists(db_config, "bgp", "neighbors"):
                for neigh_id in db_config["bgp"]["neighbors"]:
                    if neigh_id == bgp_id_neigh:
                        neigh_exists = True
                        neigh = db_config["bgp"]["neighbors"][neigh_id]

                        if key_exists(neigh, "remote"):
                            if neigh["remote"] != site_as:
                                neigh["remote"] = site_as
                        else:
                            neigh["remote"] = site_as
                        if key_exists(neigh, "update"):
                            if neigh["update"] != "lo":
                                neigh["update"] = "lo"
                        else:
                            neigh["update"] = "lo"
                        break
                if neigh_exists is False:
                    db_config["bgp"]["neighbors"][bgp_id_neigh] = {}
                    db_config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = site_as
                    db_config["bgp"]["neighbors"][bgp_id_neigh]["update"] = "lo"
            else:
                db_config["bgp"]["neighbors"] = {}
                db_config["bgp"]["neighbors"][bgp_id_neigh] = {}
                db_config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = site_as
                db_config["bgp"]["neighbors"][bgp_id_neigh]["update"] = "lo"
    elif active is True:
        db_config["bgp"] = {}
        db_config["bgp"]["as"] = site_as
        db_config["bgp"]["router-id"] = device_id
        db_config["bgp"]["neighbors"] = {}
        for neighbor in neighbors:
            bgp_id_neigh = f'1.1.1.{neighbor["device information"]["id"]}'
            db_config["bgp"]["neighbors"][bgp_id_neigh] = {}
            db_config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = site_as
            db_config["bgp"]["neighbors"][bgp_id_neigh]["update"] = "lo"
    else:
        config["bgp"] = {}
        config["bgp"]["as"] = site_as
        config["bgp"]["router-id"] = device_id
        config["bgp"]["neighbors"] = {}
        for neighbor in neighbors:
            bgp_id_neigh = f'1.1.1.{neighbor["device information"]["id"]}'
            config["bgp"]["neighbors"][bgp_id_neigh] = {}
            config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = site_as
            config["bgp"]["neighbors"][bgp_id_neigh]["update"] = "lo"

    # update gateway bgp
    if db_config is not None:
        for ip_addr, as_id in zip(neigh_as_ip_addr, neigh_as):
            bgp_id_neigh = f'{ip_addr}'
            db_config["bgp"]["neighbors"][bgp_id_neigh] = {}
            db_config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = as_id
    else:
        for ip_addr, as_id in zip(neigh_as_ip_addr, neigh_as):
            bgp_id_neigh = f'{ip_addr}'
            config["bgp"]["neighbors"][bgp_id_neigh] = {}
            config["bgp"]["neighbors"][bgp_id_neigh]["remote"] = as_id

    if active is True:
        return db_config
    else:
        return config
