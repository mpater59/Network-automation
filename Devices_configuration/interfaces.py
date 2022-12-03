from Other.other import key_exists
from Other.other import check_if_exists


def interfaces(config, db_config=None, expand=False):
    commands = []

    # config interfaces
    if key_exists(config, "interfaces"):

        if key_exists(db_config, "interfaces") and expand is False:
            for dbInt in db_config.get("interfaces"):
                ints = list(config.get("interfaces").keys())
                if check_if_exists(dbInt, ints) is False:
                    commands.append(f"net del interface {dbInt}")

        for int in config.get("interfaces"):
            interface = config["interfaces"][int]

            if key_exists(db_config, "interfaces", int) and len(db_config["interfaces"][int]) > 0:
                db_interface = db_config["interfaces"][int]
            else:
                db_interface = None

            # config ip address
            if key_exists(interface, "ip address"):
                if isinstance(interface["ip address"], str) is True:
                    ip_address = [interface["ip address"]]
                else:
                    ip_address = interface["ip address"]

                if key_exists(db_interface, "ip address"):
                    db_ip_address = db_interface["ip address"]
                    for dbIpAddr in db_ip_address:
                        if check_if_exists(dbIpAddr, ip_address) is False:
                            commands.append(f"net del interface {int} ip address {dbIpAddr}")
                else:
                    db_ip_address = None

                for ipAddr in ip_address:
                    if check_if_exists(ipAddr, db_ip_address) is False:
                        commands.append(f"net add interface {int} ip address {ipAddr}")
            else:
                if key_exists(db_interface, "ip address") and expand is False:
                    commands.append(f"net del interface {int} ip address")

            # config shutdown
            if key_exists(interface, "shutdown"):
                if key_exists(db_interface, "shutdown") and db_interface["shutdown"] != interface["shutdown"]:
                    if interface.get("shutdown") is True:
                        commands.append(f"net add interface {int} link down")
                    elif interface.get("shutdown") is False:
                        commands.append(f"net del interface {int} link down")
                elif db_interface is None:
                    if interface.get("shutdown") is True:
                        commands.append(f"net add interface {int} link down")
                    elif interface.get("shutdown") is False:
                        commands.append(f"net del interface {int} link down")
            else:
                if key_exists(db_interface, "shutdown") and expand is False:
                    if db_interface["shutdown"] is True:
                        commands.append(f"net del interface {int} link down")
    else:
        if key_exists(db_config, "interfaces") and expand is False:
            for dbInt in db_config.get("interfaces"):
                commands.append(f"net del interface {dbInt}")
    return commands


def loopback(config, db_config=None, expand=False):
    commands = []

    # config loopback ip address
    if key_exists(config, "loopback", "ip address"):
        if isinstance(config["loopback"]["ip address"], str) is True:
            ip_address = [config["loopback"]["ip address"]]
        else:
            ip_address = config["loopback"]["ip address"]
        db_ip_address = None
        if key_exists(db_config, "loopback", "ip address"):
            if isinstance(db_config["loopback"]["ip address"], str) is True:
                db_ip_address = [db_config["loopback"]["ip address"]]
            else:
                db_ip_address = db_config["loopback"]["ip address"]
            for dbIpAddr in db_ip_address:
                if check_if_exists(dbIpAddr, ip_address) is False:
                    commands.append(f"net del loopback lo ip address {dbIpAddr}")
        for ipAddr in ip_address:
            if check_if_exists(ipAddr, db_ip_address) is False:
                commands.append(f"net add loopback lo ip address {ipAddr}")
    else:
        if expand is False:
            commands.append(f"net del loopback lo ip address")
    return commands
