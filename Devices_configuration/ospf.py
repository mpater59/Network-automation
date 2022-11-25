from other import compare_list
from other import key_exists
from other import check_if_exists


def del_ospf(interface, interface_type):
    commands = []
    commands.append(f"net del {interface_type} {interface} ospf area")
    commands.append(f"net del {interface_type} {interface} ospf network")
    commands.append(f"net del ospf passive-interface {interface}")
    return commands


def ospf(config, db_config=None, expand=False):
    commands = []

    # config ospf
    if key_exists(config, "ospf"):
        ospf_config = config["ospf"]

        if key_exists(db_config, "ospf") and len(db_config["ospf"]) > 0:
            db_ospf_config = db_config["ospf"]
        else:
            db_ospf_config = None

        # config router-id
        if key_exists(ospf_config, "router-id"):
            if key_exists(db_ospf_config, "router-id") and db_ospf_config["router-id"] != ospf_config["router-id"]:
                commands.append(f"net del ospf router-id")
                commands.append(f"net add ospf router-id {ospf_config['router-id']}")
            elif db_ospf_config is None:
                commands.append(f"net add ospf router-id {ospf_config['router-id']}")
        else:
            if key_exists(db_ospf_config, "router-id") and expand is False:
                commands.append("net del ospf router-id")

        # config interfaces
        if key_exists(ospf_config, "interfaces"):

            if key_exists(db_ospf_config, "interfaces") and expand is False:
                for dbInt in db_ospf_config.get("interfaces"):
                    ints = list(ospf_config.get("interfaces").keys())
                    if check_if_exists(dbInt, ints) is False:
                        if dbInt == "lo":
                            interface_type = "loopback"
                        else:
                            interface_type = "interface"
                        for commands_cli in del_ospf(dbInt, interface_type):
                            commands.append(commands_cli)

            for int in ospf_config.get("interfaces"):
                interface = ospf_config["interfaces"][int]

                if int == "lo":
                    interface_type = "loopback"
                else:
                    interface_type = "interface"

                if key_exists(db_ospf_config, "interfaces", int):
                    db_interface = db_ospf_config["interfaces"][int]
                else:
                    db_interface = None

                # config area
                if key_exists(interface, "area"):
                    if key_exists(db_interface, "area") and interface.get("area") != db_interface.get("area"):
                        commands.append(f"net del {interface_type} {int} ospf area {db_interface.get('area')}")
                        commands.append(f"net add {interface_type} {int} ospf area {interface.get('area')}")
                    elif db_interface is None:
                        commands.append(f"net add {interface_type} {int} ospf area {interface.get('area')}")
                else:
                    if key_exists(db_interface, "area") and expand is False:
                        commands.append(f"net del {interface_type} {int} ospf area {db_interface.get('area')}")

                # config passive interface
                if key_exists(interface, "passive interface"):
                    if key_exists(db_interface, "passive interface") and \
                            interface.get("passive interface") != db_interface.get("passive interface"):
                        if interface.get("passive interface") is True:
                            commands.append(f"net add ospf passive-interface {int}")
                        elif interface.get("passive interface") is False:
                            commands.append(f"net del ospf passive-interface {int}")
                    elif db_interface is None:
                        if interface.get("passive interface") is True:
                            commands.append(f"net add ospf passive-interface {int}")
                else:
                    if key_exists(db_interface, "passive interface") and expand is False:
                        if db_interface.get("passive interface") is True:
                            commands.append(f"net del ospf passive-interface {int}")

                # config network
                if key_exists(interface, "network"):
                    if key_exists(db_interface, "network") and interface.get("network") != db_interface.get("network"):
                        commands.append(f"net del {interface_type} {int} ospf network {db_interface.get('network')}")
                        commands.append(f"net add {interface_type} {int} ospf network {interface.get('network')}")
                    elif db_interface is None:
                        commands.append(f"net add {interface_type} {int} ospf network {interface.get('network')}")
                else:
                    if key_exists(db_interface, "network") and expand is False:
                        commands.append(f"net del {interface_type} {int} ospf network {db_interface.get('network')}")
        else:
            if key_exists(db_ospf_config, "interfaces") and expand is False:
                for dbInt in db_ospf_config.get("interfaces"):
                    if dbInt == "lo":
                        interface_type = "loopback"
                    else:
                        interface_type = "interface"
                    for commands_cli in del_ospf(dbInt, interface_type):
                        commands.append(commands_cli)
    else:
        if key_exists(db_config, "ospf") and expand is False:
            commands.append("net del ospf")

    return commands
