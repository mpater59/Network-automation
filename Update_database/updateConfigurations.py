from socket import socket
import datetime
import netmiko
import paramiko
import yaml
from netmiko import ConnectHandler
import pymongo
from bson import ObjectId

from Update_database.ospf import updateOSPF
from Update_database.interfaces import updateInterfaces
from Update_database.interfaces import updateLoopback
from Update_database.bgp import updateBGP
from Update_database.vlanBridgeVxlan import updateVLAN
from Update_database.vlanBridgeVxlan import updateBridge
from Update_database.vlanBridgeVxlan import updateVxLAN
from Update_database.other_conf import updateHostname
from Update_database.other_conf import updateStaticRoute
from Update_database.interfaces import updateInterfacesAgain

from Other.other import key_exists
from Other.other import check_if_exists


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def vxlan_update(config):
    vxlan = {}
    if key_exists(config, 'vxlan', 'vnis'):
        for vni_name in config['vxlan']['vnis']:
            vni = config['vxlan']['vnis'][vni_name]
    return vxlan


def update(site, devices=None, status=None, new_documents=False):

    if devices is not None:
        split_devices = devices.split(',')
    else:
        split_devices = []

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    selected_devices = []
    for device_temp in devices_temp:
        if devices is None and device_temp["site"] == site:
            selected_devices.append(device_temp)
        elif devices is not None:
            if check_if_exists(device_temp["hostname"], split_devices) is True and device_temp["site"] == site:
                selected_devices.append(device_temp)
                split_devices.remove(device_temp["hostname"])
    stream.close()

    if split_devices != []:
        print("The following devices couldn't be found on this site:")
        for split_device in split_devices:
            print(split_device)

    config_id = ObjectId()
    config_time = datetime.datetime.now().replace(microsecond=0)

    for device in selected_devices:

        device_connection = {
            "device_type": device.get("machine type"),
            "ip": device.get("ip address"),
            "username": device.get("username"),
            "password": device.get("password"),
            "secret": device.get("secret"),
            "port": device.get("port"),
            "verbose": True
        }

        for trial in range(3):
            try:
                configuration = {}
                creation_time = datetime.datetime.now().replace(microsecond=0)
                configuration["last update datetime"] = creation_time
                configuration["archived update datetime"] = []
                configuration["config set information"] = {}
                configuration["config set information"]["last config set id"] = config_id
                configuration["config set information"]["archived config set id"] = []
                configuration["config set information"]["last config set datetime"] = config_time
                configuration["config set information"]["archived config set datetime"] = []
                configuration["device information"] = {}
                configuration["device information"]["type"] = device["device information"]["type"]
                configuration["device information"]["id"] = device["device information"]["id"]
                configuration["site"] = device.get("site")
                configuration["device hostname"] = device.get("hostname")
                if status is None:
                    configuration["status"] = "unverified"
                else:
                    configuration["status"] = status
                configuration["active"] = True
                configuration["configuration"] = {}

                connection = ConnectHandler(**device_connection)
                output = connection.send_command("net show configuration")
                print(output)
                output_list = output.splitlines()

                configuration["configuration"].update(updateHostname(output_list))
                configuration["configuration"].update(updateInterfaces(output_list))
                configuration["configuration"].update(updateLoopback(output_list))
                configuration["configuration"].update(updateStaticRoute(output_list))
                configuration["configuration"].update(updateOSPF(output_list))
                configuration["configuration"].update(updateBGP(output_list))
                configuration["configuration"].update(updateVLAN(output_list))
                configuration["configuration"].update(updateBridge(output_list))
                configuration["configuration"].update(updateVxLAN(output_list))
                configuration["configuration"] = updateInterfacesAgain(configuration["configuration"])
                connection.disconnect()

                query = {"active": True, "device hostname": device["hostname"], "site": device["site"]}
                new_values = {"$set": {"active": False}}
                modified = False
                if col_configs.count_documents(query) > 0:
                    old_config = col_configs.find(query).sort("last update datetime", -1)[0]
                    if key_exists(old_config, "configuration") and new_documents is False:
                        if old_config["configuration"] == configuration["configuration"]:

                            query = {"active": True, "device hostname": device["hostname"],
                                     "site": device["site"], "_id": {"$ne": ObjectId(old_config["_id"])}}
                            col_configs.update_many(query, new_values)

                            old_update_time = col_configs.find_one({"_id": ObjectId(old_config["_id"])})["last update datetime"]
                            old_config_set_id = col_configs.find_one({"_id": ObjectId(old_config["_id"])})\
                                ["config set information"]["last config set id"]
                            old_config_set_time = col_configs.find_one({"_id": ObjectId(old_config["_id"])})\
                                ["config set information"]["last config set datetime"]

                            new_values = {"$set": {"last update datetime": creation_time,
                                                  "config set information.last config set id": config_id,
                                                  "config set information.last config set datetime": config_time},
                                         "$push": {"archived update datetime": old_update_time,
                                                   "config set information.archived config set id": old_config_set_id,
                                                   "config set information.archived config set datetime": old_config_set_time}}
                            query = {"_id": ObjectId(old_config["_id"])}
                            col_configs.update_one(query, new_values)

                            if status is not None:
                                new_values = {"$set": {"status": status}}
                                col_configs.find_one(query, new_values)

                            modified = True
                        else:
                            col_configs.update_many(query, new_values)
                    else:
                        col_configs.update_many(query, new_values)
                if modified is False:
                    db_insert = col_configs.insert_one(configuration)
                    print(f"New update ID: " + str(db_insert.inserted_id))

                break
            except paramiko.buffered_pipe.PipeTimeout:
                print(f"Timeout - {trial + 1}.")
            except socket.timeout:
                print(f"Timeout - {trial + 1}.")
            except netmiko.ssh_exception.NetmikoTimeoutException:
                print(f"Timeout - {trial + 1}.")
