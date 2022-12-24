import argparse
import re
import pymongo
import yaml

from datetime import datetime
from bson import ObjectId
from Sites_configuration.updateLeaf import get_neighbor_ports
from Sites_configuration.updateVxlan import get_vxlan
from Other.other import key_exists


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def get_configuration(site, file=None, devices=None, status=None, config_id=None, config_update_date=None):

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
    for device_temp in devices_temp:
        known_devices.append(device_temp)
    stream.close()

    selected_devices = []
    if devices is not None:
        split_devices = devices.split(',')
        split_devices_temp = devices.split(',')
        for split_device in split_devices:
            for known_device in known_devices:
                if known_device["site"] == site and known_device["hostname"] == split_device and \
                        known_device['device information']['type'] == 'leaf':
                    selected_devices.append(known_device)
                    split_devices_temp.remove(split_device)
                    break
        if split_devices_temp != []:
            print("The following devices couldn't be found on this site:")
            for split_device in split_devices_temp:
                print(split_device["hostname"])
    else:
        for known_device in known_devices:
            if known_device["site"] == site and known_device['device information']['type'] == 'leaf':
                selected_devices.append(known_device)

    vxlans = []

    for device in selected_devices:
        get_condition = None

        if config_id is not None:
            if re.search("^[0-9a-f]{24}$", config_id):
                query1 = {'config set information.last config set id': ObjectId(f"{config_id}"), "site": site,
                          "device hostname": device}
                query2 = {'config set information.archived config set id': ObjectId(f"{config_id}"), "site": site,
                          "device hostname": device}
                if col_configs.count_documents(query1) > 0:
                    conf_id = str(col_configs.find_one(query1).get("_id"))
                elif col_configs.count_documents(query2) > 0:
                    conf_id = str(col_configs.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set ID for {device}!")
                    continue
                get_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration set ID!")
                exit()
        elif config_update_date is not None:
            if re.search("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", config_update_date):
                date = datetime.strptime(config_update_date, "%d/%m/%Y %H:%M:%S")
                query1 = {"site": site, "device hostname": device,
                          "config set information.last config set datetime": date}
                query2 = {"site": site, "device hostname": device,
                          "config set information.archived config set datetime": date}
                if col_configs.count_documents(query1) > 0:
                    conf_id = str(col_configs.find_one(query1).get("_id"))
                elif col_configs.count_documents(query2) > 0:
                    conf_id = str(col_configs.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set datetime for {device}!")
                    continue
                get_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration update datetime, enter dd/mm/YYYY HH:MM:SS!")
                exit()
        elif status is not None:
            query = {"site": site, "device hostname": device, "status": status}
            if col_configs.count_documents(query) > 0:
                conf_id = str(col_configs.find(query).sort("last update datetime", -1)[0].get("_id"))
                get_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                continue
        else:
            query = {"site": site, "device hostname": device['hostname'], "active": True}
            if col_configs.count_documents(query) > 0:
                conf_id = str(col_configs.find(query).sort("last update datetime", -1)[0].get("_id"))
                get_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                continue

        config_db = col_configs.find_one(get_condition)

        vxlan = {}
        vxlan['hostname'] = device['hostname']
        vxlan['vxlan'] = get_vxlan(site, device['hostname'], config_db)
        print(vxlan)

        vxlans.append(vxlan)

    if file is not None:
        name_file = file
        new_file = open(name_file, "w")
    else:
        name_file = f'{site}_'
        if devices is None:
            name_file += 'vxlan'
        else:
            for device in selected_devices:
                name_file = name_file + device
        name_file = name_file + '.yaml'
        new_file = open(name_file, "w")
    new_file.close()

    with open(name_file, "a") as stream:
        yaml.safe_dump_all(vxlans, stream, default_flow_style=False, sort_keys=False)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-f", "--file_name", dest="file_name", default=None,
                    help="File name where you want save configurations from DB (optional)")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will get all devices in selected site)")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status of configuration set in DB (optional)")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID of configuration set in DB (optional)")
parser.add_argument("-dt", "--datetime", dest="config_update_date", default=None,
                    help="Datetime of configuration set in DB, dd/mm/YYYY HH:MM:SS format (optional)")

args = parser.parse_args()

get_configuration(args.site, args.file_name, args.device, args.status_text, args.config_id, args.config_update_date)
