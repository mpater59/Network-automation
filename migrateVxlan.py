import argparse
import copy

import pymongo
import yaml

from Devices_configuration.devicesConfiguration import devicesConfiguration
from Sites_configuration.updateDevice import update_device
from Sites_configuration.updateVxlan import get_vxlan, update_vxlan
from Update_database.updateConfigurations import update
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports
from Other.other import key_exists
from Other.other import check_if_exists

stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def migrate_vni(source_site, source_device, destination_site, destination_device, ports=None, vnis=None,
                status=None, soft_update=False, extend=False, extend_ports=False):

    if source_site is None:
        print("Enter name of source site!")
        exit()
    else:
        query = {"site": source_site}
        if col_configs.count_documents(query) == 0:
            print(f"Can't find source site {source_site} in DB!")
            exit()

    if destination_site is None:
        print("Enter name of destination site!")
        exit()
    else:
        query = {"site": destination_site}
        if col_configs.count_documents(query) == 0:
            print(f"Can't find destination site {destination_site} in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    s_device = None
    d_device = None
    known_devices = []
    for device in devices_temp:
        if device["hostname"] == source_device and device["site"] == source_site \
                and device['device information']['type'] == 'leaf':
            s_device = device
        elif device["hostname"] == destination_device and device["site"] == destination_site \
                and device['device information']['type'] == 'leaf':
            d_device = device
        known_devices.append(device)
    stream.close()

    if s_device is None:
        print(f"Couldn't find source device {source_device}!")
    if d_device is None:
        print(f"Couldn't find source device {destination_device}!")

    s_vxlan = get_vxlan(source_site, source_device)
    if extend is True:
        d_vxlan = get_vxlan(destination_site, destination_device)
    else:
        d_vxlan = {}

    if vnis is not None:
        selected_vnis = list(map(int, vnis.split(',')))
        for vni in s_vxlan.copy():
            if int(vni) not in selected_vnis:
                s_vxlan.pop(vni, None)
    if ports is not None:
        selected_ports = ports.split(',')
        for vni in s_vxlan.copy():
            if 'ports' in s_vxlan[vni]:
                for port in s_vxlan[vni]['ports'][:]:
                    if port not in selected_ports:
                        s_vxlan[vni]['ports'].remove(port)

    s_vids_taken = {}
    for vni in s_vxlan:
        if 'vid' in s_vxlan[vni]:
            if int(s_vxlan[vni]['vid']) not in s_vids_taken:
                s_vids_taken[int(s_vxlan[vni]['vid'])] = []
            s_vids_taken[int(s_vxlan[vni]['vid'])].append(int(vni))

    vnis_multiple_vids = {}
    for vid in s_vids_taken:
        if len(s_vids_taken[vid]) > 1:
            for vni in s_vids_taken[vid]:
                vnis_multiple_vids[int(vni)] = int(vid)

    d_vids_taken = []
    for vni in d_vxlan:
        if 'vid' in d_vxlan[vni] and int(d_vxlan[vni]['vid']) not in d_vids_taken:
            d_vids_taken.append(int(d_vxlan[vni]['vid']))

    new_vids = {}
    for vni in s_vxlan:
        if vni in d_vxlan and 'vid' in d_vxlan[vni] and vni not in new_vids:
            new_vids[vni] = d_vxlan[vni]['vid']
            if vni in vnis_multiple_vids:
                old_vid = vnis_multiple_vids[vni]
                if old_vid in s_vids_taken:
                    for s_vni in s_vids_taken[old_vid]:
                        if s_vni not in new_vids:
                            new_vids[s_vni] = d_vxlan[vni]['vid']

    for vni in s_vxlan:
        if vni not in new_vids:
            new_vid = 10
            while True:
                if new_vid > 4096:
                    print("Couldn't find free VID")
                    break
                if new_vid not in d_vids_taken:
                    d_vids_taken.append(new_vid)
                    new_vids[vni] = new_vid
                    if vni in vnis_multiple_vids and vnis_multiple_vids[vni] in s_vids_taken:
                        for s_vni in s_vids_taken[vnis_multiple_vids[vni]]:
                            if s_vni not in new_vids:
                                new_vids[s_vni] = new_vid
                    break
                new_vid += 10

    for vni in s_vxlan:
        vni_exists = True
        if vni not in d_vxlan:
            d_vxlan[vni] = {}
            vni_exists = False
        d_vxlan[vni]['vid'] = new_vids[vni]
        if vni_exists is False and 'ports' in s_vxlan[vni]:
            d_vxlan[vni]['add ports'] = len(s_vxlan[vni]['ports'])
        elif vni_exists is True and extend_ports is True and 'ports' in s_vxlan[vni]:
            d_vxlan[vni]['add ports'] = len(s_vxlan[vni]['ports'])

    result = update_vxlan(destination_site, destination_device, d_vxlan)
    devicesConfiguration(destination_site, destination_device, result['config'], soft_update)
    update(destination_site, destination_device, status)

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    selected_device = None
    for device in devices_temp:
        if device["hostname"] == destination_device and device["site"] == destination_site:
            selected_device = device
            break
    stream.close()

    ports = leaf_ports(selected_device, destination_site)
    print(f"Configured ports for device {destination_device}; site {destination_site}")
    for port in ports:
        print(port)


parser = argparse.ArgumentParser()

parser.add_argument("-sst", "--source_site", dest="source_site", help="Name of source site")
parser.add_argument("-sd", "--source_device", dest="source_device", help="Name of source device")
parser.add_argument("-dst", "--destination_site", dest="destination_site", help="Name of destination site")
parser.add_argument("-dd", "--destination_device", dest="destination_device", help="Name of destination device")
parser.add_argument("-p", "--ports", dest="ports", default=None,
                    help="Name of switchports with VNI, separate with ',' (default parameter will migrate all known switchports with VNI from source device)")
parser.add_argument("-vx", "--vnis", dest="vnis", default=None,
                    help="Index of VNI, separate with ',' (default parameter will migrate all known VNIs from source device)")
parser.add_argument("-ex", "--extend", dest="extend", default=False, action='store_true',
                    help="Migrate new VNIs without deleting old VNIs from destination device (default false)")
parser.add_argument("-ep", "--extend_ports", dest="extend_ports", default=False, action='store_true',
                    help="Add new ports even if VNI already exists (default false)")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")

args = parser.parse_args()

migrate_vni(args.source_site, args.source_device, args.destination_site, args.destination_device, args.ports, args.vnis,
            args.status_text, args.soft_update, args.extend, args.extend_ports)
