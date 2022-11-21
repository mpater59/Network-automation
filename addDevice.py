import argparse

import pymongo
import yaml

from other import check_if_exists
from other import key_exists
from Sites_configuration.updateDevice import update_device
from Update_database.updateConfigurations import update
from Sites_configuration.updateSpine import get_neighbor_ports as spine_ports
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports
from Sites_configuration.updateGateway import get_neighbor_ports as gw_ports


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def add_device(site, devices_file, status=None, soft_update=False, expand=False):

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    devices = None
    if isinstance(devices_file, str):
        stream = open(devices_file, 'r')
        devices_temp = yaml.load_all(stream, Loader=yaml.Loader)

        devices = []
        for config_temp in devices_temp:
            devices.append(config_temp)
            print(config_temp)
        stream.close()
    elif isinstance(devices_file, list):
        devices = devices_file
    else:
        print("Enter path to file with configurations or list of dictionaries with configurations!")
        exit()

    db_devices = []
    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.Loader)
    for device_temp in devices_temp:
        db_devices.append(device_temp)
    stream.close()

    db_spines = []
    db_spines_id = []
    db_leafs = []
    db_leafs_id = []
    db_gws = []
    db_gws_id = []
    db_finals = []

    for db_device in db_devices:
        if db_device["device information"]["type"] == "spine" and db_device["site"] == site:
            db_spines.append(db_device)
            db_spines_id.append(db_device["device information"]["id"])
        elif db_device["device information"]["type"] == "leaf" and db_device["site"] == site:
            db_leafs.append(db_device)
            db_leafs_id.append(db_device["device information"]["id"])
        elif db_device["device information"]["type"] == "gateway" and db_device["site"] == site:
            db_gws.append(db_device)
            db_gws_id.append(db_device["device information"]["id"])
        else:
            db_finals.append(db_device)

    db_spines_id = sorted(db_spines_id)
    db_leafs_id = sorted(db_leafs_id)
    db_gws_id = sorted(db_gws_id)

    for device in devices:
        new_id = None
        device_type = device["device type"]

        if device_type == "spine":
            if len(db_spines_id) > 0:
                for x in range(db_spines_id[-1] + 1):
                    if check_if_exists((x+1), db_spines_id) is False:
                        db_spines_id.append(x+1)
                        db_spines_id = sorted(db_spines_id)
                        new_id = x + 1
                        break
            else:
                new_id = 1
                db_spines_id.append(new_id)
        elif device_type == "leaf":
            if len(db_leafs_id) > 0:
                for x in range(db_leafs_id[-1] + 1):
                    if check_if_exists((x+1), db_leafs_id) is False:
                        db_leafs_id.append(x+1)
                        db_leafs_id = sorted(db_leafs_id)
                        new_id = x + 1
                        break
            else:
                new_id = 1
                db_leafs_id.append(new_id)
        elif device_type == "gateway":
            if len(db_gws_id) > 0:
                for x in range(db_gws_id[-1] + 1):
                    if check_if_exists((x+1), db_gws_id) is False:
                        db_gws_id.append(x+1)
                        db_gws_id = sorted(db_gws_id)
                        new_id = x + 1
                        break
            else:
                new_id = 1
                db_gws_id.append(new_id)
        else:
            print("Entered incorrect type device!")
            exit()

        if key_exists(device, "hostname") is False:
            device["hostname"] = f"{device_type}{new_id}".capitalize()

        if key_exists(device, "site") is True:
            if device["site"] != site:
                print("Entered site name doesn't match with site parameter!")
                exit()
        else:
            device["site"] = site

        device["device information"] = {"type": device.pop('device type'), "id": new_id}

        if device_type == "spine":
            db_spines.append(device)
        elif device_type == "leaf":
            db_leafs.append(device)
        elif device_type == "gateway":
            db_gws.append(device)

    db_spines.sort(key=lambda i: (i["device information"]["id"]))
    db_leafs.sort(key=lambda i: (i["device information"]["id"]))
    db_gws.sort(key=lambda i: (i["device information"]["id"]))

    for db_spine in db_spines:
        db_finals.append(db_spine)
    for db_leaf in db_leafs:
        db_finals.append(db_leaf)
    for db_gw in db_gws:
        db_finals.append(db_gw)

    with open("devices.yaml", "w") as stream:
        yaml.safe_dump_all(db_finals, stream, default_flow_style=False, sort_keys=False)

    first_item = True
    merged_hostnames = ''
    for db_final in db_finals:
        if db_final["site"] == site:
            if first_item is True:
                merged_hostnames += db_final["hostname"]
                first_item = False
            else:
                merged_hostnames += f",{db_final['hostname']}"

            update_device(site, db_final["hostname"], soft_update, expand)

    update(site, merged_hostnames, status)

    for db_final in db_finals:
        if db_final["site"] == site:
            if db_final["device information"]["type"] == "spine":
                ports = spine_ports(db_final, db_finals, site)
                print(f"Configured ports for device {db_final['hostname']}; site {site}")
                for port in ports:
                    print(port)
            elif db_final["device information"]["type"] == "leaf":
                ports = leaf_ports(db_final, db_finals, site)
                print(f"Configured ports for device {db_final['hostname']}; site {site}")
                for port in ports:
                    print(port)
            elif db_final["device information"]["type"] == "gateway":
                ports = gw_ports(db_final, db_finals, site)
                print(f"Configured ports for device {db_final['hostname']}; site {site}")
                for port in ports:
                    print(port)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-df", "--devices_file", dest="devices_file",
                    help="Path to .yaml file with new devices")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")
parser.add_argument("-ex", "--expand", dest="expand", default=False, action='store_true',
                    help="Add changes on existing configuration (default false)")

args = parser.parse_args()

add_device(args.site, args.devices_file, args.status_text, args.soft_update, args.expand)
