from other import key_exists


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
