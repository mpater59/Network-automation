import socket
import netmiko.ssh_exception
import paramiko.buffered_pipe
import pymongo
import yaml

from netmiko import ConnectHandler
import Devices_configuration.interfaces as interfaces
from Devices_configuration.ospf import ospf
from Devices_configuration.bgp import bgp
from Devices_configuration.vlanBridgeVxlan import vlan
from Devices_configuration.vlanBridgeVxlan import bridge
from Devices_configuration.vlanBridgeVxlan import vxlan
from Devices_configuration.other_conf import hostname
from Devices_configuration.other_conf import static_routes


stream = open('database_env.yaml', 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def devicesConfiguration(site, device, config, soft_config_change=False, expand=False):

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0 and soft_config_change is True:
            print("Can't find this site in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    selected_device = None
    for device_temp in devices_temp:
        if device_temp["hostname"] == device and device_temp["site"] == site:
            selected_device = device_temp
            break
    stream.close()

    commands = []
    active_config = False
    if soft_config_change is True:
        if col_configs.count_documents({"active": True, "device hostname": device, "site": site}) > 0:
            active_config = True
        else:
            print(f"Active configuration not detected in the database for {device}!")

    device_connection = {
        "device_type": selected_device.get("machine type"),
        "ip": selected_device.get("ip address"),
        "username": selected_device.get("username"),
        "password": selected_device.get("password"),
        "secret": selected_device.get("secret"),
        "port": selected_device.get("port"),
        "verbose": True
    }

    db_config = None
    if active_config is True:
        query = {"active": True, "site": site, "device hostname": device}
        if col_configs.count_documents(query) > 0:
            db_config = col_configs.find(query).sort("last update datetime", -1)[0].get("configuration")
        else:
            print(f"Couldn't find active configuration for {device} in DB!")

    apply_config = True
    # Commands for Cumulus VX virtual machines
    # hard configuration reset
    if active_config is False and expand is False:
        commands.append("net del all")
    # hostname configuration
    for command_cli in hostname(config, db_config, expand):
        commands.append(command_cli)
    # interfaces configuration
    for command_cli in interfaces.interfaces(config, db_config, expand):
        commands.append(command_cli)
    # loopback configuration
    for command_cli in interfaces.loopback(config, db_config, expand):
        commands.append(command_cli)
    # static route configuration
    for command_cli in static_routes(config, db_config, expand):
        commands.append(command_cli)
    # ospf configuration
    for command_cli in ospf(config, db_config, expand):
        commands.append(command_cli)
    # bgp configuration
    for command_cli in bgp(config, db_config, expand):
        commands.append(command_cli)
    # vlan configuration
    for command_cli in vlan(config, db_config, expand):
        commands.append(command_cli)
    # bridge configuration
    for command_cli in bridge(config, db_config, expand):
        commands.append(command_cli)
    # vxlan configuration
    for command_cli in vxlan(config, db_config, expand):
        commands.append(command_cli)
    # ending configuration
    if commands != []:
        commands.append("net commit")
    else:
        apply_config = False
        print(f"Inserted configuration is the same as active configuration for device {selected_device['hostname']}!")

    if apply_config is True:
        print(commands)

        for trial in range(5):
            try:
                break
                connection = ConnectHandler(**device_connection)
                output = connection.send_config_set(commands)
                print(output)
                connection.disconnect()
                break
            except paramiko.buffered_pipe.PipeTimeout:
                print(f"Timeout - {trial + 1}")
                break
            except socket.timeout:
                print(f"Timeout - {trial + 1}")
                break
            except netmiko.ssh_exception.NetmikoTimeoutException:
                print(f"Timeout - {trial + 1}")
                break
            except ValueError:
                print(f"Value Error - {trial + 1}")
