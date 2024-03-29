import pymongo
import yaml

from Sites_configuration.updateSpine import update_spine
from Sites_configuration.updateLeaf import update_leaf
from Sites_configuration.updateVxlan import update_vxlan
from Sites_configuration.updateGateway import update_gateway
from Devices_configuration.devicesConfiguration import devicesConfiguration
from Other.other import key_exists


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def update_device(site, device, soft_update=True, expand=False):

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0 and soft_update is True:
            print("Can't find this site in DB!")
            exit()

    devices_file = []
    stream = open("devices.yaml", 'r')
    devices_file_temp = list(yaml.load_all(stream, Loader=yaml.SafeLoader))
    for device_temp in devices_file_temp:
        if device_temp["site"] == site:
            devices_file.append(device_temp)
    selected_device = None
    device_exists = False
    for device_file in devices_file:
        if device_file["hostname"] == device and device_file["site"] == site:
            selected_device = device_file
            device_exists = True
            break
    if device_exists is False:
        print(f"Device {device} doesn't exist in DB for site {site}!")
        exit()
    stream.close()

    stream = open("sites.yaml", 'r')
    sites_file = list(yaml.load_all(stream, Loader=yaml.SafeLoader))
    selected_site = None
    for site_file in sites_file:
        if site_file["name"] == site:
            selected_site = site_file
            break
    stream.close()

    query = {"device hostname": device, "site": site, "active": True}
    if soft_update is True and col_configs.count_documents(query) > 0:
        active = True
        db_config = col_configs.find(query).sort("last update datetime", -1)[0].get("configuration")
    else:
        db_config = None
        active = False
        expand = False

    device_type = selected_device["device information"]["type"]

    # update spine
    if device_type == "spine":
        config = update_spine(selected_device, devices_file, selected_site, db_config, active, expand)

    # update leaf
    elif device_type == "leaf":
        config = update_leaf(selected_device, devices_file, selected_site, db_config, active, expand)
        # if key_exists(selected_device, "vxlan"):
        #     config = update_vxlan(selected_site, selected_device, config)

    # update gw
    elif device_type == "gateway":
        config = update_gateway(selected_device, devices_file, selected_site, db_config, active, expand)

    else:
        config = None
        print(f"Enter proper device type for {selected_device['hostname']}!")

    print(config)

    devicesConfiguration(site, device, config, soft_update, expand)

# testy
# update_device("test1", "Spine1", True, False)
