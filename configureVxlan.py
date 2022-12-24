import argparse
import pymongo
import yaml

from Update_database.updateConfigurations import update
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports
from Sites_configuration.updateVxlan import update_vxlan
from Devices_configuration.devicesConfiguration import devicesConfiguration


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def configure_vxlan(site, vxlan_file, status=None, soft_update=False, expand=False):

    vxlans = None
    if isinstance(vxlan_file, str):
        file = open(vxlan_file, 'r')
        vxlans_temp = yaml.load_all(file, Loader=yaml.Loader)

        vxlans = []
        for config_temp in vxlans_temp:
            vxlans.append(config_temp)
            print(config_temp)
        file.close()
    elif isinstance(vxlan_file, list):
        vxlans = vxlan_file
    else:
        print("Enter path to file with configurations or list of dictionaries with configurations!")
        exit()

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    file = open("sites.yaml", 'r')
    sites_file = list(yaml.load_all(file, Loader=yaml.SafeLoader))
    selected_site = None
    for site_file in sites_file:
        if site_file["name"] == site:
            selected_site = site_file
            break
    file.close()

    first_item = True
    merged_hostnames = ''
    selected_devices = []
    vxlan_results = []

    for vxlan in vxlans:

        file = open("devices.yaml", 'r')
        devices_temp = yaml.load_all(file, Loader=yaml.SafeLoader)
        selected_device = None
        for device in devices_temp:
            if device["hostname"] == vxlan["hostname"] and device["site"] == site \
                    and device['device information']['type'] == 'leaf':
                selected_device = device
                selected_devices.append(device)
                break
        file.close()

        if first_item is True:
            merged_hostnames = vxlan["hostname"]
            first_item = False
        else:
            merged_hostnames += f',{vxlan["hostname"]}'

        result = update_vxlan(selected_site['name'], selected_device['hostname'], vxlan['vxlan'], expand)
        vxlan_results.append({'hostname': selected_device['hostname'], 'vxlan': result['vxlan']})

        devicesConfiguration(site, vxlan["hostname"], result['config'], soft_update, False)

    update(site, merged_hostnames, status)

    selected_devices = []
    for vxlan in vxlans:
        stream = open("devices.yaml", 'r')
        devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
        for device in devices_temp:
            if device["hostname"] == vxlan["hostname"] and device["site"] == site:
                selected_devices.append(device)
                break
        stream.close()

    for db_device in selected_devices:
        if db_device["site"] == site:
            if db_device["device information"]["type"] == "leaf":
                ports = leaf_ports(db_device, site)
                print(f"Configured ports for device {db_device['hostname']}; site {site}")
                for port in ports:
                    print(port)

    with open(f"{site}_vxlan_configuration.yaml", "w") as stream:
        yaml.safe_dump_all(vxlan_results, stream, default_flow_style=False, sort_keys=False)


parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-vf", "--vxlan_file", dest="vxlan_file",
                    help="Path to .yaml file with new VxLAN configs")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")
parser.add_argument("-ev", "--expand_vxlan", dest="expand_vxlan", default=False, action='store_true',
                    help="Add VxLANs without deleting existing (default false)")

args = parser.parse_args()

configure_vxlan(args.site, args.vxlan_file, args.status_text, args.soft_update, args.expand_vxlan)
