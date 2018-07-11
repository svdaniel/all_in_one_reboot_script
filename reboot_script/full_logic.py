from .f5.f5_api import F5ApiWrapper
from .get_os.verify_os import get_os_type
from .linux.linux_remote import CommandLinux
from .get_threading.thread import my_threading, choose_max_threads
from .windows.windows_remote import CommandWindows, verify_ui_web_healthcheck
from .calc_nodes_to_work_with.number_of_nodes_to_reboot import count_num_nodes_to_reboot_at_a_time


def prepare_server(server, f5_lbname, f5_server, f5_username, f5_password, compute_username, compute_password, search_pool=True):
    f5 = F5ApiWrapper(f5_lbname, f5_server, f5_username, f5_password)

    # I. Get IP from servername if not already provided
    if server[:2].isdigit():
        print("It already is IP")
        ip = server
    else:
        ip = f5.get_ip_from_server_name(server_name=server)
    print("Server: {}, IP: {}".format(server, ip))

    # II. Get Operating System type
    os = get_os_type(compute_username, compute_password, ip=ip)

    if search_pool is True:
        # III. List IP Pool(s) the server is part of
        pools = f5.find_pool_ip_is_in(ip=ip)
        return ip, os, pools

    return ip, os


def f5_disable_logic(queue, ip, pools, f5_lbname, f5_server, f5_username, f5_password, force,
                     acceptable_health_percentage, time_out, bleed_until_num_of_connections):

    f5 = F5ApiWrapper(f5_lbname, f5_server, f5_username, f5_password)

    # Note: Normally POOLs should be in list format, split to list if string is obtained
    if type(pools) == str:
        pools = str(pools).split(',')

    # Bypass F5 logic if IP is not part of any pool
    if not pools:
        print("IP: {}, no pool used. Skipping F5 Logic.".format(ip))
        return True

    else:
        # Verify if IP is not disabled/forced offline in F5, if yes, skip and do NOT reboot
        for each in pools:
            enabled, output = f5.ip_status_in_f5(ip, each)
            if enabled is False:
                print("IP: {}: Only enabled nodes in F5 will be rebooted. Skipping this IP, it returned: {}". format(ip, output))
                output = {ip: {'reboot_success': "False, Node original state in F5: Disabled/Forced offline. Skipped this IP"}}
                queue.enter_single_data(output)
                return False

        # If Force is Enabled, skip F5 bleeding logic and directly disable in F5
        if force is True:
            print("IP: {}, Force is SET: Bypassing bleed out and directly disabling of Node on F5.".format(ip))
            disable_success = f5.disable_and_bleed(ip, pools[0], time_out, bleed_until_num_of_connections, force=True)
            return disable_success

        else:
            # IP is member of a more than 1 pool use threading to verify that all used pools are healthy
            if len(pools) > 1:
                print("IP: {}, more than 1 pool used. Verifying healtcheck of all pools: {}".format(ip, pools))
                my_threading(f5.full_multiple_pools_health_calculation_logic, pools, acceptable_health_percentage, queue)

                # Get health of pools from queue and ensure all of them return healthy: True, else exit
                while not queue.empty():
                    pool_health = queue.get_single_data()
                    if pool_health is True:
                        print("IP: {}, All Pools are healthy, ready to continue on!".format(ip))
                        pass
                    else:
                        print("IP: {}, ERROR: At least one of the pools is NOT Healthy despite several attempts!! Skipping run for this IP!".format(ip, pool_health))
                        queue.enter_single_data({ip: "False, One or more pools are NOT healthy despite several attempts!"})
                        return pool_health

            # IP is member of a single pool
            else:
                print("IP: {}, single pool used. Verifying healtcheck of pool: {}".format(ip, pools))
                healthy = f5.full_pool_health_calculation_logic(pools[0], acceptable_health_percentage)

                # Ensure Pool is Healthy
                if healthy is True:
                    print("IP: {}, All Pools are healthy, ready to continue on!".format(ip))
                    pass
                else:
                    print("IP: {}, ERROR: The Pool is NOT Healthy despite several attempts!! Skipping run for this IP!".format(ip))
                    queue.enter_single_data({ip: "False, the pool is NOT healthy despite several attempts!!"})
                    return healthy

            # Disable and bleed until desired number of connections or time out clocks out
            print("IP: {}, Disabling and allowing to bleed.".format(ip))
            disable_success = f5.disable_and_bleed(ip, pools[0], time_out, bleed_until_num_of_connections, force=False)

            return disable_success


def f5_enable_logic(ip, f5_lbname, f5_server, f5_username, f5_password):
    f5 = F5ApiWrapper(f5_lbname, f5_server, f5_username, f5_password)

    # Re-Enable server in F5
    success = f5.enable_ip_on_node_level(ip=ip)

    if success is True:
        print("IP {}: Successfully Enabled in F5.".format(ip))
    else:
        print("IP {}: FAILED Enabling in F5!".format(ip))

    return success


def reboot_logic(server, action, queue, os, service, service_action, linux_username=None, linux_password=None, win_reboot_message=None):

    if os == "windows":
        windows = CommandWindows(server=server)

        # Obtain Kerberos Ticket to Authenticate
        kinit_command = windows.get_kinit_command()
        windows.kinit_krb_tkt(kinit_command)

        if action == 'reboot':
            # Initiate Reboot
            reboot_success, reboot_output = windows.reboot_windows(reboot_message=win_reboot_message)

            print("IP: {}, rebooted: {}, with output: {}".format(server, reboot_success, reboot_output))

            if reboot_success is True:
                print("IP: {}, now awaiting server to come up".format(server))
                windows.sleep_after_reboot(100)

                rebooted_success = windows.verify_rebooted()
                windows.sleep_after_reboot(5)

                output = {server: {'rebooted_success': rebooted_success}}
            else:
                output = {server: {'reboot_success': reboot_success}}

        elif action == 'iis_recycle':
            # Initiate Reboot
            iis_recycle_success, iis_recycle_output = windows.recycle_iis()

            print("IP: {}: IIS Recycle success: {}, with output: {}".format(server, iis_recycle_success,
                                                                            iis_recycle_output))
            output = {server: {'iis_recycle_success': iis_recycle_success}}

        else:
            # Initiate Stop/Start/Restart of Service
            service_success, service_output = windows.stop_start_restart_service(service=service, action=service_action)
            print("IP: {}: service: {}, action: {}, success: {}, with output: {}".format(server, service, service_action, service_success, service_output))
            output = {server: {'{}, {}'.format(service, service_action): service_success}}

        if "ui" in server:
            healthcheck_success = verify_ui_web_healthcheck(server)
            output[server]['healthcheck_success'] = healthcheck_success

        queue.enter_single_data(output)

    elif os == "linux":
        linux = CommandLinux(server=server, username=linux_username, password=linux_password)

        if action == 'reboot':
            reboot_success = linux.reboot_linux()

            print("IP: {}, rebooted: {}.".format(server, reboot_success))

            if reboot_success is True:
                print("IP: {}, now awaiting server to come up".format(server))
                linux.sleep_after_reboot(100)

                rebooted_success = linux.verify_rebooted()
                linux.sleep_after_reboot(5)

                output = {server: {'rebooted_success': rebooted_success}}
            else:
                output = {server: {'reboot_success': reboot_success}}

        else:
            service_success, service_output = linux.stop_start_restart_service(service=service, action=service_action)
            print("IP: {}: service: {}, action: {}, success: {}, with output: {}".format(server, service, service_action, service_success, service_output))

            output = {server: {'{}, {}'.format(service, service_action): service_success}}

        queue.enter_single_data(output)


def logic_for_individual_servers(*args):

    print("THEADING LEVEL II. >> Servers level Threading")

    # Gather arguments provided from threading function
    server, other_args = args

    action, queue, f5_lbname, f5_server, f5_username, f5_password, compute_username, compute_password, force, \
        acceptable_health_percentage, time_out, bleed_until_num_of_connections, linux_username, linux_password, \
        win_reboot_message, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time, service, service_action, os, pool = other_args

    # If OS/Pools are None, that means that the script is ran for separate server, not from pool level logic, get IP/OS/Pool info
    if os is None or pool is None:
        ip, os, pool = prepare_server(server, f5_lbname, f5_server, f5_username, f5_password, compute_username, compute_password)
    else:
        ip = server

    if action == 'iis_recycle':
        print("IIS Recycle chosen, skipping entire F5 logic")
    else:
        # Go through F5 logic Verify/Disable/Bleed...
        f5_success = f5_disable_logic(queue, ip, pool, f5_lbname, f5_server, f5_username, f5_password, force,
                                      acceptable_health_percentage, time_out, bleed_until_num_of_connections)

        if f5_success is True:
            print("IP: {}: F5 logic passed, good to continue to next step".format(ip))
            pass
        else:
            print("IP: {}: F5 logic did NOT PASS. Exiting for this IP!".format(ip))
            return

    # Run reboot itself including verification of successful reboot
    reboot_logic(server, action, queue, os, service, linux_username, linux_password, win_reboot_message)

    # Re-enable IP in F5 if server is member of any pool
    if pool and action != 'iis_recycle':
        f5_enable_logic(ip, f5_lbname, f5_server, f5_username, f5_password)


def get_pool_info(f5_lbname, f5_server, f5_username, f5_password, pool, reboot_nodes_at_a_time,
                  reboot_percent_of_nodes_at_a_time, compute_username, compute_password):

    f5 = F5ApiWrapper(f5_lbname, f5_server, f5_username, f5_password)

    # Get list of IPs in a pool
    ips = f5.get_ips_of_members_in_pool(pool)

    # Count how many servers/ips to reboot at a time
    reboot_at_a_time = count_num_nodes_to_reboot_at_a_time(ips, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time)

    # II. Get Operating System type
    os = get_os_type(compute_username, compute_password, ip=ips[0])

    return ips, reboot_at_a_time, os


def pool_logic(*args):

    print("THEADING LEVEL I. >> Pool level Threading")

    # Gather arguments provided from threading function
    pool, other_args = args
    action, queue, f5_lbname, f5_server, f5_username, f5_password, compute_username, compute_password, force, \
        acceptable_health_percentage, time_out, bleed_until_num_of_connections, linux_username, linux_password, \
        win_reboot_message, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time, service, service_action, os, pool = other_args[0]

    ips, reboot_at_a_time, os = get_pool_info(f5_lbname, f5_server, f5_username, f5_password, pool, reboot_nodes_at_a_time,
                                              reboot_percent_of_nodes_at_a_time, compute_username, compute_password)

    choose_max_threads(logic_for_individual_servers, ips, reboot_at_a_time, action, queue, f5_lbname, f5_server, f5_username,
                       f5_password, compute_username, compute_password, force, acceptable_health_percentage, time_out,
                       bleed_until_num_of_connections, linux_username, linux_password, win_reboot_message, os, pool)
