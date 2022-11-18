import re
import pymongo
import argparse
import yaml
from bson import ObjectId
from datetime import datetime


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]


def changeStatus(site, devices=None, status="stable", config_id=None, config_update_date=None, active=False):

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

    config_datetime = None
    if active is False:
        config_datetime = col_configs.find({"site": site}).sort("config set information.last config set datetime", -1)[0]\
            .get("config set information").get("last config set datetime")

    selected_devices = []
    if devices is not None:
        split_devices = devices.split(',')
        for split_device in split_devices:
            for known_device in known_devices:
                if known_device["site"] == site and known_device["hostname"] == split_device:
                    selected_devices.append(known_device["hostname"])
                    split_devices.remove(split_device)
                    break
        if split_devices != []:
            print("The following devices couldn't be found on this site:")
            for split_device in split_devices:
                print(split_device)
    else:
        for known_device in known_devices:
            if known_device["site"] == site:
                selected_devices.append(known_device["hostname"])

    for selected_device in selected_devices:
        update_condition = None

        if config_id is not None:
            if re.search("^[0-9a-f]{24}$", config_id):
                query1 = {'config set information.last config set id': ObjectId(f"{config_id}"), "site": site,
                          "hostname": selected_device}
                query2 = {'config set information.archived config set id': ObjectId(f"{config_id}"), "site": site,
                          "hostname": selected_device}
                if col_configs.count_documents(query1) > 0:
                    conf_id = str(col_configs.find_one(query1).get("_id"))
                elif col_configs.count_documents(query2) > 0:
                    conf_id = str(col_configs.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set ID for {selected_device}!")
                    continue
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration set ID!")
                exit()
        elif config_update_date is not None:
            if re.search("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", config_update_date):
                date = datetime.strptime(config_update_date, "%d/%m/%Y %H:%M:%S")
                query1 = {"site": site, "hostname": selected_device,
                          "config set information.last config set datetime": date}
                query2 = {"site": site, "hostname": selected_device,
                          "config set information.archived config set datetime": date}
                if col_configs.count_documents(query1) > 0:
                    conf_id = str(col_configs.find_one(query1).get("_id"))
                elif col_configs.count_documents(query2) > 0:
                    conf_id = str(col_configs.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set datetime for {selected_device}!")
                    continue
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration update datetime, enter dd/mm/YYYY HH:MM:SS!")
                exit()
        elif active is True:
            query = {"active": True, "site": site, "hostname": selected_device}
            conf_id = str(col_configs.find(query).sort("config set information.last config set datetime", -1)[0].get("_id"))
            update_condition = {'_id': ObjectId(f"{conf_id}")}
        else:
            query = {"site": site, "hostname": selected_device,
                     "config set information.last config set datetime": config_datetime}
            if col_configs.count_documents(query) > 0:
                conf_id = str(col_configs.find(query).sort("config set information.last config set datetime", -1)[0].get("_id"))
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                continue

        new_values = {"$set": {"status": status}}
        db_update = col_configs.update_one(update_condition, new_values)
        print(db_update.raw_result)


parser = argparse.ArgumentParser()

parser.add_argument("-t", "--status_text", dest="status_text", default="stable",
                    help="Text status that will be inserted to DB for selected configuration")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID of configuration set in DB (optional)")
parser.add_argument("-dt", "--datetime", dest="config_update_date", default=None,
                    help="Datetime of configuration set in DB, dd/mm/YYYY HH:MM:SS format (optional)")
parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")
parser.add_argument("-oa", "--only_active", dest="active", default=False, action='store_true',
                    help="Change status only on active configuration (cannot be used with -id and -st flags)")

args = parser.parse_args()

changeStatus(args.site, args.device, args.status_text, args.config_id, args.config_update_date, args.active)
