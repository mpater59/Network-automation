import re
import yaml
import pymongo

from Other.other import key_exists
from Other.other import check_if_exists
from Sites_configuration.updateLeaf import get_neighbor_ports


def update_vxlan(selected_site, selected_device, config):

    cp_device_vxlan = []
    site = selected_site['name']

    stream = open("database_env.yaml", 'r')
    db_env = yaml.load(stream, Loader=yaml.SafeLoader)

    myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
    mydb = myclient[f"{db_env['DB name']}"]
    col_configs = mydb[f"{db_env['DB collection configuration']}"]
    stream.close()

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    if key_exists(selected_device, "vxlan") is False:
        return config

    swp_taken = []
    vids_taken = []
    vnis_taken = []

    ports = get_neighbor_ports(selected_device, site, config)
    for port in ports:
        if check_if_exists(list(port.keys())[0], swp_taken) is False:
            swp_taken.append(list(port.keys())[0])
        else:
            print(f'Found multiple usage of switchport {list(port.keys())[0]} for device {selected_device["hostname"]}!')
            exit()
        if key_exists(port, list(port.keys())[0], "vid"):
            if check_if_exists(port[list(port.keys())[0]]["vid"], vids_taken) is False:
                vids_taken.append(port[list(port.keys())[0]]["vid"])
        if key_exists(port, list(port.keys())[0], 'vni'):
            if check_if_exists(port[list(port.keys())[0]]["vni"], vnis_taken) is False:
                vnis_taken.append(port[list(port.keys())[0]]["vni"])

    vids = []
    vnis = []
    vnis_names = []
    swps = []
    multiple_vnis = []

    for vxlan in selected_device['vxlan']:
        if key_exists(vxlan, "vni"):
            if check_if_exists(vxlan["vni"], vnis_taken) is True:
                if check_if_exists(vxlan["vni"], multiple_vnis) is True:
                    print(f"VNI {vxlan['vni']} already exists!")
                    continue
                else:
                    multiple_vnis.append(vxlan["vni"])
            vnis.append(vxlan["vni"])
            if len(vnis_names) > 0:
                if check_if_exists(f'vni{vxlan["vni"]}', vnis_names) is True:
                    x = 2
                    while True:
                        if check_if_exists(f'vni{vxlan["vni"]}-{x}', vnis_names) is False:
                            vnis_names.append(f'vni{vxlan["vni"]}-{x}')
                            break
                        else:
                            x += 1
                else:
                    vnis_names.append(f'vni{vxlan["vni"]}')
            else:
                vnis_names.append(f'vni{vxlan["vni"]}')
        else:
            print("Enter VNI for every VxLAN!")
            exit()

        if key_exists(vxlan, "vid"):
            vids.append(vxlan["vid"])
        else:
            new_vid = 10
            while True:
                if new_vid > 4096:
                    print("Couldn't find free VID")
                    break
                if check_if_exists(new_vid, vids_taken) is False:
                    vids_taken.append(new_vid)
                    vids.append(new_vid)
                    break
                new_vid += 10

        if key_exists(vxlan, "port"):
            swps.append(vxlan["port"])
        else:
            free_port = False
            for new_swp in range(selected_device["number of ports"]):
                if check_if_exists(f'swp{new_swp+1}', swp_taken) is False:
                    swp_taken.append(f'swp{new_swp+1}')
                    swps.append(f'swp{new_swp+1}')
                    free_port = True
                    break
            if free_port is False:
                print(f"Couldn't find free port for new VNI for device {selected_device['hostname']}!")

    if key_exists(config, "vxlan") is False:
        config["vxlan"] = {}
    if key_exists(config, "vxlan", "vnis") is False:
        config["vxlan"]["vnis"] = {}
    if key_exists(config, "bridge") is False:
        config["bridge"] = {}
    if key_exists(config, "bridge", "vids") is False:
        config["bridge"]["vids"] = {}
    if key_exists(config, "bridge", "ports") is False:
        config["bridge"]["ports"] = []

    swp_del = []
    for port in config["bridge"]["ports"]:
        if re.search("^swp\d+", port):
            swp_del.append(port)
    config["bridge"]["ports"] = []

    temp_vids = []
    for temp_vid in config["bridge"]["vids"]:
        temp_vids.append(temp_vid)
    for vid in temp_vids:
        config["bridge"]["vids"].pop(vid, None)

    temp_vnis = []
    for temp_vni in config["vxlan"]["vnis"]:
        temp_vnis.append(temp_vni)
    for vni in temp_vnis:
        config["vxlan"]["vnis"].pop(vni, None)

    temp_interfaces = []
    for temp_interface in config["interfaces"]:
        temp_interfaces.append(temp_interface)
    for interface in temp_interfaces:
        if check_if_exists(interface, swp_del):
            config["interfaces"].pop(interface, None)

    temp_ospf = []
    for temp_ospf_int in config["ospf"]["interfaces"]:
        temp_ospf.append(temp_ospf_int)
    for interface in temp_ospf:
        if check_if_exists(interface, swp_del):
            config["ospf"]["interfaces"].pop(interface, None)

    for vni, vni_name, vid, swp in zip(vnis, vnis_names, vids, swps):
        if key_exists(config, "bridge", "ports") is False:
            config["bridge"]["ports"] = []
        config["bridge"]["ports"].append(swp)
        config["bridge"]["ports"].append(vni_name)
        if key_exists(config, "bridge", "vids", vid) is False:
            config["bridge"]["vids"][vid] = {}
        if key_exists(config, "bridge", "vids", vid, "bridge access") is False:
            config["bridge"]["vids"][vid]["bridge access"] = []
        config["bridge"]["vids"][vid]["bridge access"].append(swp)
        config["bridge"]["vids"][vid]["bridge access"].append(vni_name)

        if key_exists(config, "vxlan", "vnis", vni_name) is False:
            config["vxlan"]["vnis"][vni_name] = {}
        config["vxlan"]["vnis"][vni_name]["bridge access"] = vid
        config["vxlan"]["vnis"][vni_name]["id"] = vni
        config["vxlan"]["vnis"][vni_name]["local-tunnelip"] = \
            f'1.1.{selected_site["site id"]}.{100+selected_device["device information"]["id"]}'

        if key_exists(config, 'interfaces') is False:
            config['interfaces'] = {}
        config['interfaces'][swp] = {}
        if key_exists(config, 'ospf', 'interfaces') is False:
            config['ospf']['interfaces'] = {}
        config['ospf']['interfaces'][swp] = {}

        cp_device_vxlan.append({'vni': vni, 'vid': vid, 'port': swp})

    if selected_device['vxlan'] != cp_device_vxlan:
        db_devices = []
        stream = open("devices.yaml", 'r')
        devices_temp = yaml.load_all(stream, Loader=yaml.Loader)
        for device_temp in devices_temp:
            db_devices.append(device_temp)
        stream.close()

        for device in db_devices:
            if device["hostname"] == selected_device["hostname"] and device["site"] == site:
                device['vxlan'] = []
                for vxlan in cp_device_vxlan:
                    device['vxlan'].append(vxlan)
                break

        with open("devices.yaml", "w") as stream:
            yaml.safe_dump_all(db_devices, stream, default_flow_style=False, sort_keys=False)

    return config
