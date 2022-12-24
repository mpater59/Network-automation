import argparse
import pymongo
import yaml

from Devices_configuration.devicesConfiguration import devicesConfiguration
from Sites_configuration.updateVxlan import get_vxlan, update_vxlan
from Update_database.updateConfigurations import update
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports

stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def del_vxlan(site, devices=None, vnis=None, ports=None, status=None, soft_update=False):
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

    if vnis is not None:
        selected_vnis = vnis.split(',')
    else:
        selected_vnis = None
    if ports is not None:
        selected_ports = ports.split(',')
    else:
        selected_ports = None

    merged_hostnames = ''
    first_item = True
    for device in selected_devices:
        if device["site"] == site:
            if first_item is True:
                merged_hostnames += device["hostname"]
                first_item = False
            else:
                merged_hostnames += f",{device['hostname']}"

        vxlan = get_vxlan(site, device['hostname'])

        if selected_vnis is not None:
            for vni_del in selected_vnis:
                for vni in vxlan.copy():
                    if int(vni) == int(vni_del):
                        vxlan.pop(vni, None)
        elif selected_ports is not None:
            for port_del in selected_ports:
                for vni in vxlan.copy():
                    if 'ports' in vxlan[int(vni)] and port_del in vxlan[int(vni)]['ports']:
                        vxlan[int(vni)]['ports'].remove(port_del)
            for vni in vxlan.copy():
                if 'ports' in vxlan[int(vni)] and len(vxlan[int(vni)]['ports']) == 0:
                    vxlan.pop(vni, None)
        else:
            for vni in vxlan.copy():
                vxlan.pop(vni, None)

        result = update_vxlan(site, device['hostname'], vxlan)

        devicesConfiguration(site, device["hostname"], result['config'], soft_update)

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
parser.add_argument("-p", "--ports", dest="ports", default=None,
                    help="Name of switchports with VNI, separate with ',' (default parameter will delete all known switchports with VNI from source device)")
parser.add_argument("-v", "--vnis", dest="vnis", default=None,
                    help="Index of VNI, separate with ',' (default parameter will delete all known VNIs from source device)")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")

args = parser.parse_args()

del_vxlan(args.site, args.device, args.vnis, args.ports, args.status_text, args.soft_update)
