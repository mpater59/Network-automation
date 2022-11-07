import socket
import netmiko.ssh_exception
import paramiko.buffered_pipe
import pymongo

from netmiko import ConnectHandler
import Devices_configuration.interfaces as interfaces
from Devices_configuration.ospf import ospf as ospf
from Devices_configuration.bgp import bgp as bgp
from Devices_configuration.vlanBridgeVxlan import vlan as vlan
from Devices_configuration.vlanBridgeVxlan import bridge as bridge
from Devices_configuration.vlanBridgeVxlan import vxlan as vxlan

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


def devicesConfiguration(devices_list, config_list, soft_rollback=True):
    device_connection = []
    commands = []
    active_config = False
    if soft_rollback is True:
        if mycol.count_documents({"active": True}) > 0:
            active_config = True
        else:
            print("Active configuration not detected in the database!")
            exit()
    for (counter, device), config in zip(enumerate(devices_list), config_list):
        device_connection_temp = {
            "device_type": device.get("machine type"),
            "ip": device.get("ip address"),
            "username": device.get("username"),
            "password": device.get("password"),
            "secret": device.get("secret"),
            "port": device.get("port"),
            "verbose": True
        }
        device_connection.append(device_connection_temp)
        commands_temp = []
        db_config = None
        unknown_device = True
        if active_config is True:
            db_config_list = list(mycol.find({"active": True}).sort("date", -1)[0].get("devices").values())
            for config_list in db_config_list:
                if config.get("hostname") == config_list.get("hostname"):
                    db_config = config_list
                    unknown_device = False
                    break
            if unknown_device is True:
                print("Detected new device! Check if hostnames for all devices are correct")
                exit()

        # Commands for Cumulus VX virtual machines
        expand = False
        # hard configuration reset
        if active_config is False or config.get("hard clear config"):
            commands_temp.append("net del all")
        # hostname configuration
        if config.get("hostname"):
            commands_temp.append(f"net add hostname {config.get('hostname')}")
        # interfaces configuration
        for command_cli in interfaces.interfaces(config, db_config, expand):
            commands_temp.append(command_cli)
        # loopback configuration
        for command_cli in interfaces.loopback(config, db_config, expand):
            commands_temp.append(command_cli)
        # ospf configuration
        for command_cli in ospf(config, db_config, expand):
            commands_temp.append(command_cli)
        # bgp configuration
        for command_cli in bgp(config, db_config, expand):
            commands_temp.append(command_cli)
        # vlan configuration
        for command_cli in vlan(config, db_config, expand):
            commands_temp.append(command_cli)
        # bridge configuration
        for command_cli in bridge(config, db_config, expand):
            commands_temp.append(command_cli)
        # vxlan configuration
        for command_cli in vxlan(config, db_config, expand):
            commands_temp.append(command_cli)
        # ending configuration
        if config.get("commit"):
            commands_temp.append("net commit")
        commands.append(commands_temp)

    for deviceCommands in commands:
        print(deviceCommands)

    for counter, device in enumerate(device_connection):
        for trial in range(5):
            try:
                connection = ConnectHandler(**device)
                output = connection.send_config_set(commands[counter])
                print(output)
                connection.disconnect()
                break
            except paramiko.buffered_pipe.PipeTimeout:
                print(f"Timeout - {trial + 1}")
            except socket.timeout:
                print(f"Timeout - {trial + 1}")
            except netmiko.ssh_exception.NetmikoTimeoutException:
                print(f"Timeout - {trial + 1}")
