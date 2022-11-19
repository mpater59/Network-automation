import argparse
import pymongo
import yaml
from bson import objectid

from Devices_configuration.devicesConfiguration import devicesConfiguration
from other import check_if_exists
from other import key_exists
from Update_database.updateConfigurations import update


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def objectid_constructor(loader, data):
    return objectid.ObjectId(loader.construct_scalar(data))


def configuration(site, configs_list, status=None, soft_config_change=False, expand=False, new_documents=False): # devices,

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    configs = None
    if isinstance(configs_list, str):
        yaml.add_constructor("!ObjectID:", objectid_constructor)
        stream = open(configs_list, 'r')
        configs_temp = yaml.load_all(stream, Loader=yaml.Loader)

        configs = []
        for config_temp in configs_temp:
            configs.append(config_temp)
            print(config_temp)
        stream.close()
    elif isinstance(configs_list, list):
        configs = configs_list
    else:
        print("Enter path to file with configurations or list of dictionaries with configurations!")
        exit()

    selected_devices = []
    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    for config in configs:
        device_exists = False
        if key_exists(config, "device hostname") is True:
            for device_temp in devices_temp:
                if device_temp["site"] == site:
                    if device_temp["hostname"] == config["device hostname"]:
                        selected_devices.append(device_temp["hostname"])
                        device_exists = True
                        break
            if device_exists is False:
                print(f"Device {config['device hostname']} doesn't exist in DB for site {site}!")
                exit()
        else:
            print('Add hostname of device as "device hostname" field!')
    stream.close()

    for config in configs:
        devicesConfiguration(site, config["device hostname"], config, soft_config_change, expand)
        break

    merged_devices = ''
    first_iter = True
    for device in selected_devices:
        if first_iter is True:
            merged_devices = device
            first_iter = False
        else:
            merged_devices = merged_devices + ',' + device

    update(site, merged_devices, status, new_documents)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-cf", "--config_file", dest="config_file",
                    help="Path to .yaml file with saved configurations")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this configuration in DB")
parser.add_argument("-sc", "--soft_change", dest="soft_change", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")
parser.add_argument("-ex", "--expand", dest="expand", default=False, action='store_true',
                    help="Add changes on existing configuration")
parser.add_argument("-nd", "--new_documents", dest="new_documents", default=False, action='store_true',
                    help="Force creating new documents in DB")

args = parser.parse_args()

configuration(args.site, args.config_file, args.status_text, args.soft_change, args.expand, args.new_documents)
