from other import key_exists
from other import check_if_exists


def hostname(config, db_config=None, expand=False):
    commands = []

    # config hostname
    if key_exists(config, "hostname"):

        if key_exists(db_config, "hostname"):
            if config["hostname"] != db_config["hostname"]:
                commands.append('net del hostname')
                commands.append(f'net add hostname {config["hostname"]}')
        elif db_config is None:
            commands.append(f'net add hostname {config["hostname"]}')
    else:
        if key_exists(db_config, "hostname") and expand is False:
            commands.append("net del hostname")

    return commands


def static_routes(config, db_config=None, expand=False):
    commands = []

    # config static routes
    if key_exists(config, "static routes"):

        if key_exists(db_config, "static routes") and expand is False:
            for route in db_config["static routes"]:
                if check_if_exists(route, config["static routes"]) is False:
                    commands.append(f"net del routing route {route['subnet']} {route['via']}")

        for route in config["static routes"]:

            if key_exists(db_config, "static routes") and db_config["static routes"] != []:
                if check_if_exists(route, db_config["static routes"]) is False:
                    commands.append(f"net add routing route {route['subnet']} {route['via']}")
            else:
                commands.append(f"net add routing route {route['subnet']} {route['via']}")
    else:
        if key_exists(db_config, "static routes") and expand is False:
            for route in db_config["static routes"]:
                if key_exists(route, "subnet") and key_exists(route, "via"):
                    commands.append(f"net del routing route {route['subnet']} {route['via']}")

    return commands
