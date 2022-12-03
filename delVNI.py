import argparse
import pymongo
import yaml

from Other.other import check_if_exists
from Other.other import key_exists
from Sites_configuration.updateDevice import update_device
from Update_database.updateConfigurations import update
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def del_vni(site, devices, vnis, status=None, soft_update=False):

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
            if known_device["site"] == site and known_device['device information']['type'] == 'leaf':
                selected_devices.append(known_device)

    selected_vnis = vnis.split(',')

    for device in selected_devices:
        for db_device in known_devices:
            if db_device['site'] == device['site'] and db_device['hostname'] == device['hostname']:
                if key_exists(device, 'vxlan'):
                    temp_vnis = []
                    for vni in device['vxlan']:
                        temp_vnis.append(vni)
                    for vni in temp_vnis:
                        if key_exists(vni, 'vni') and check_if_exists(str(vni['vni']), selected_vnis):
                            device['vxlan'].remove(vni)
                break

    with open("devices.yaml", "w") as stream:
        yaml.safe_dump_all(known_devices, stream, default_flow_style=False, sort_keys=False)

    first_item = True
    merged_hostnames = ''
    for device in selected_devices:
        if device["site"] == site:
            if first_item is True:
                merged_hostnames += device["hostname"]
                first_item = False
            else:
                merged_hostnames += f",{device['hostname']}"

            update_device(site, device["hostname"], soft_update)

    update(site, merged_hostnames, status)

    for db_device in selected_devices:
        if db_device["site"] == site:
            if db_device["device information"]["type"] == "leaf":
                ports = leaf_ports(db_device, site)
                print(f"Configured ports for device {db_device['hostname']}; site {site}")
                for port in ports:
                    print(port)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")
parser.add_argument("-v", "--vni", dest="vni",
                    help="Index of VNI, separate with ','")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")

args = parser.parse_args()

del_vni(args.site, args.device, args.vni, args.status_text, args.soft_update)
