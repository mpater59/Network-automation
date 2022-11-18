import pymongo
import re
import yaml
import argparse

from datetime import datetime
from bson import ObjectId
from Devices_configuration.devicesConfiguration import devicesConfiguration

myclient = pymongo.MongoClient("mongodb://192.168.1.11:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


def configRollback(config_id=None, soft_rollback=False, status="stable", devices=None, site=None,
                   config_update_date=None):

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if mycol.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    known_devices = []
    for counter, device in enumerate(devices_temp):
        known_devices.append(device)

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
        document_id = None

        if config_id is not None:
            if re.search("^[0-9a-f]{24}$", config_id):
                query1 = {'config set information.last config set id': ObjectId(f"{config_id}"), "site": site,
                          "hostname": selected_device}
                query2 = {'config set information.archived config set id': ObjectId(f"{config_id}"), "site": site,
                          "hostname": selected_device}
                if mycol.count_documents(query1) > 0:
                    conf_id = str(mycol.find_one(query1).get("_id"))
                elif mycol.count_documents(query2) > 0:
                    conf_id = str(mycol.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set ID for {selected_device}!")
                    continue
                document_id = {'_id': ObjectId(f"{conf_id}")}
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
                if mycol.count_documents(query1) > 0:
                    conf_id = str(mycol.find_one(query1).get("_id"))
                elif mycol.count_documents(query2) > 0:
                    conf_id = str(mycol.find_one(query2).get("_id"))
                else:
                    print(f"Couldn't find entered configuration set datetime for {selected_device}!")
                    continue
                document_id = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration set datetime, enter dd/mm/YYYY HH:MM:SS!")
                exit()
        else:
            query = {"site": site, "hostname": selected_device, "status": status}
            if mycol.count_documents(query) > 0:
                conf_id = str(mycol.find(query).sort("last update datetime", -1)[0].get("_id"))
            else:
                print(f"Couldn't find entered status \"{status}\" for {selected_device}!")
                continue
            document_id = {'_id': ObjectId(f"{conf_id}")}

        config = mycol.find_one(document_id).get("configuration")

        devicesConfiguration(site, selected_device, config, soft_rollback)

        query_old = {"active": True, "site": site, "hostname": selected_device, "_id": {"$ne": document_id['_id']}}
        if mycol.count_documents(query_old) > 0:
            values_old = {"$set": {"active": False}}
            db_update_old = mycol.update_many(query_old, values_old)
            print(db_update_old.raw_result)

        values_new = {"$set": {"active": True}}
        db_update_new = mycol.update_one(document_id, values_new)
        print(db_update_new.raw_result)


parser = argparse.ArgumentParser()

parser.add_argument("-sr", "--soft_rollback", dest="soft_rollback", default=False, action='store_true',
                    help="Apply rollback without deleting existing configuration on devices (default false)")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID of configuration set in DB (optional)")
parser.add_argument("-dt", "--datetime", dest="config_update_date", default=None,
                    help="Datetime of configuration set in DB, dd/mm/YYYY HH:MM:SS format (optional)")
parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")
parser.add_argument("-t", "--status_text", dest="status_text", default="stable",
                    help='Text of configuration set status from which rollback will be applied (default "stable")')
# parser.add_argument("-pc", "--previous_config", dest="previous_config", default=False, action='store_true',
#                     help="Apply rollback from penultimate configuration set (default false)")


args = parser.parse_args()

configRollback(args.config_id, args.soft_rollback)
