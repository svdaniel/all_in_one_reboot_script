
def project_import():
    import sys
    import os

    path = os.getcwd()
    print(sys.path)

    if path not in sys.path:
        print("Appending path: '{}' to sys.path".format(path))
        sys.path.append(path)


def main():
    from .get_queue.my_queue import MyQueue
    from .prepare_arguments.preparing_args import gathering_arguments
    from .full_logic import logic_for_individual_servers, pool_logic
    from .get_threading.thread import my_threading

    # I. Gather Arguments
    pools, servers, action, service, service_action, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time, \
        force, f5_server, f5_lbname, f5_username, f5_password, f5_acceptable_pool_health, bleed_until_num_of_connections, \
        bleed_timeout, compute_username, compute_password, lin_username, lin_password, win_reboot_message = gathering_arguments()

    queue = MyQueue()

    arguments = (action, queue, f5_lbname, f5_server, f5_username, f5_password, compute_username, compute_password, force,
                 f5_acceptable_pool_health, bleed_timeout, bleed_until_num_of_connections, lin_username, lin_password,
                 win_reboot_message, reboot_nodes_at_a_time, reboot_percent_of_nodes_at_a_time, service, service_action, None, None)

    if pools:
        my_threading(pool_logic, pools, arguments)

    if servers:
        my_threading(logic_for_individual_servers, servers, arguments)

    while not queue.empty():
        overall_output = queue.get_single_data()
        print(overall_output)


if __name__ == '__main__':
    project_import()
    main()
