

# VALIDATING ALL ARGUMENTS
# ------------------------------------
def correcting_arguments(to_validate):
    import re

    raw_validated = re.sub("([ ,:;])", ',', str(to_validate)).split(",")

    # Turn List into Set and back to get rid of multiple same values,
    validated_set = set(raw_validated)
    if '' in validated_set:
        validated_set.remove('')
    validated = list(validated_set)

    return validated


def verify_input(var):
    if var is None or var == "" or var.lower() == "none" or var.lower() == "false":
        return None
    else:
        return var


# GATHERING && PREPARING ARGUMENTS
# ------------------------------------
def gathering_arguments():
    import os

    # If arg is not filled => "arg == None"

    # I. GENERAL ARGs
    # ============================
    pools = os.getenv('RD_OPTION_POOLS')
    if pools is None or pools == "" or pools == "None".lower():
        pools = None
    else:
        pools = correcting_arguments(pools)

    servers_ips = os.getenv('RD_OPTION_SERVERS_IPS')
    if servers_ips is None or servers_ips == "" or servers_ips == "None".lower():
        servers_ips = None
    else:
        servers_ips = correcting_arguments(servers_ips)

    iis_recycle = str(os.getenv('RD_OPTION_ACTION')).lower()
    service = verify_input(os.getenv('RD_OPTION_SERVICE'))
    service_action = verify_input(os.getenv('RD_OPTION_SERVICE_ACTION'))

    # II. REBOOT ARGs
    # ============================
    temp_reboot_nodes_at_a_time = verify_input(os.getenv('RD_OPTION_TAKE_NODES_AT_A_TIME'))                           # Default: 10
    print(temp_reboot_nodes_at_a_time)

    if temp_reboot_nodes_at_a_time is not None:
        reboot_nodes_at_a_time = int(temp_reboot_nodes_at_a_time)
    else:
        reboot_nodes_at_a_time = temp_reboot_nodes_at_a_time

    temp_reboot_percent_of_nodes_at_a_time = verify_input(os.getenv('RD_OPTION_TAKE_PERCENT_OF_NODES_AT_A_TIME'))     # Default: 20 %
    if temp_reboot_percent_of_nodes_at_a_time is not None:
        reboot_percent_of_nodes_at_a_time = int(temp_reboot_percent_of_nodes_at_a_time)
    else:
        reboot_percent_of_nodes_at_a_time = temp_reboot_percent_of_nodes_at_a_time

    force = str(os.getenv('RD_OPTION_FORCE')).lower()                                                    # Default: False
    if force == "true":
        force = True
    else:
        force = False

    # III. F5 ARGs
    # ============================
    f5_server = os.getenv('RD_OPTION_F5_SERVER')
    f5_lbname = os.getenv('RD_OPTION_F5_LBNAME')
    f5_username = os.getenv('RD_OPTION_F5_USERNAME')
    f5_password = os.getenv('RD_OPTION_F5_PASSWORD')

    temp_f5_acceptable_pool_health = verify_input(os.getenv('RD_OPTION_ACCEPTABLE_POOL_HEALTH'))                    # Default: 60 %
    if temp_f5_acceptable_pool_health is not None:
        f5_acceptable_pool_health = int(temp_f5_acceptable_pool_health)
    else:
        f5_acceptable_pool_health = temp_f5_acceptable_pool_health

    temp_bleed_until_num_of_connections = verify_input(os.getenv('RD_OPTION_BLEED_UNTIL_CONNECTIONS'))              # Default: 10
    if temp_bleed_until_num_of_connections is not None:
        bleed_until_num_of_connections = int(temp_bleed_until_num_of_connections)
    else:
        bleed_until_num_of_connections = temp_bleed_until_num_of_connections

    temp_bleed_timeout = verify_input(os.getenv('RD_OPTION_BLEED_TIMEOUT'))                                         # Default: 300 (seconds)
    if temp_bleed_timeout is not None:
        bleed_timeout = int(temp_bleed_timeout)
    else:
        bleed_timeout = temp_bleed_timeout

    # IV. COMPUTE ARGs
    # ============================
    compute_username = os.getenv('RD_OPTION_COMPUTE_USERNAME')
    compute_password = os.getenv('RD_OPTION_COMPUTE_PASSWORD')

    # V. Linux + Windows ARGs
    # ============================
    lin_username = verify_input(os.getenv('RD_OPTION_LIN_USERNAME'))
    lin_password = verify_input(os.getenv('RD_OPTION_LIN_PASSWORD'))

    # PREPARATION: in case specific/custom realm, home path or path to keytab is required:
    #   raw_win_realm = os.getenv('win_realm')
    #   win_realm = verify_input(raw_win_realm)
    #
    #   raw_win_home_path = os.getenv('win_home_path')
    #   win_home_path = verify_input(raw_win_home_path)
    #
    #   raw_win_path_to_keytab = os.getenv('win_path_to_keytab')
    #   win_path_to_keytab = verify_input(raw_win_path_to_keytab)

    win_reboot_message = verify_input(os.getenv('RD_OPTION_WIN_REBOOT_MESSAGE'))

    print("\n\nArguments Gathered:")
    print("\tpools: \t\t\t\t\t\t\t{}".format(pools))
    print("\tservers_ips: \t\t\t\t\t\t{}".format(servers_ips))
    print("\tiis_recycle: \t\t\t\t\t\t{}".format(iis_recycle))
    print("\tservice: \t\t\t\t\t\t{}".format(service))
    print("\tservice_action: \t\t\t\t\t{}".format(service_action))
    print("\treboot_nodes_at_a_time: \t\t\t\t{}".format(reboot_nodes_at_a_time))
    print("\treboot_percent_of_nodes_at_a_time: \t\t\t{}".format(reboot_percent_of_nodes_at_a_time))
    print("\tforce: \t\t\t\t\t\t\t{}".format(force))
    print("\tf5_server: \t\t\t\t\t\t{}".format(f5_server))
    print("\tf5_lbname: \t\t\t\t\t\t{}".format(f5_lbname))
    print("\tf5_username: \t\t\t\t\t\t{}".format(f5_username))
    print("\tf5_password: \t\t\t\t\t\t{}".format(f5_password))
    print("\tf5_acceptable_pool_health: \t\t\t\t{}".format(f5_acceptable_pool_health))
    print("\tbleed_until_num_of_connections: \t\t\t{}".format(bleed_until_num_of_connections))
    print("\tbleed_timeout: \t\t\t\t\t\t{}".format(bleed_timeout))
    print("\tcompute_username: \t\t\t\t\t{}".format(compute_username))
    print("\tcompute_password: \t\t\t\t\t{}".format(compute_password))
    print("\tlin_username: \t\t\t\t\t\t{}".format(lin_username))
    print("\tlin_password: \t\t\t\t\t\t{}".format(lin_password))
    print("\twin_reboot_message: \t\t\t\t\t{}".format(win_reboot_message))

    return pools, servers_ips, iis_recycle, service, service_action, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time, \
        force, f5_server, f5_lbname, f5_username, f5_password, f5_acceptable_pool_health, bleed_until_num_of_connections,\
        bleed_timeout, compute_username, compute_password, lin_username, lin_password, win_reboot_message
