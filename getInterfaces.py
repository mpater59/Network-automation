import argparse
import pymongo
import yaml

from Sites_configuration.updateSpine import get_neighbor_ports as spine_ports
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports
from Sites_configuration.updateGateway import get_neighbor_ports as gw_ports


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def get_interfaces(site, devices):

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    known_devices = []
    for device in devices_temp:
        known_devices.append(device)
    stream.close()

    selected_devices = []
    if devices is not None:
        split_devices = devices.split(',')
        temp_split_devices = devices.split(',')
        for split_device in temp_split_devices:
            for known_device in known_devices:
                if known_device["site"] == site and known_device["hostname"] == split_device:
                    selected_devices.append(known_device)
                    split_devices.remove(split_device)
                    break
        if split_devices != []:
            print("The following devices couldn't be found on this site:")
            for split_device in split_devices:
                print(split_device)
    else:
        for known_device in known_devices:
            if known_device["site"] == site:
                selected_devices.append(known_device)

    for device_db in selected_devices:
        if device_db["site"] == site:
            if device_db["device information"]["type"] == "spine":
                ports = spine_ports(device_db, site)
                print(f"Configured ports for device {device_db['hostname']}; site {site}")
                for port in ports:
                    print(port)
            elif device_db["device information"]["type"] == "leaf":
                ports = leaf_ports(device_db, site)
                print(f"Configured ports for device {device_db['hostname']}; site {site}")
                for port in ports:
                    print(port)
            elif device_db["device information"]["type"] == "gateway":
                ports = gw_ports(device_db, site)
                print(f"Configured ports for device {device_db['hostname']}; site {site}")
                for port in ports:
                    print(port)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--devices", dest="devices",
                    help="Name of devices, separate with ',' (default parameter will get interfaces information for all devices in selected site)")

args = parser.parse_args()

get_interfaces(args.site, args.devices)
