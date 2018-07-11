

# Counting how many nodes to reboot at a time
def count_num_nodes_to_reboot_at_a_time(pool_ips, reboot_nodes_at_a_time=None, reboot_percent_at_a_time=None):
    """Logic to calculate the number of nodes to reboot at a time.
    :param pool_ips: list of ips in pool
    :param reboot_nodes_at_a_time: number of nodes to reboot at a time
    :param reboot_percent_at_a_time: % of nodes to reboot at a time >> will calculate to actual number dependent on the number of ips in given pool
    :return: int number of nodes to reboot at a time
    """

    from math import ceil

    print("Counting number of nodes to reboot from the following list of IPs: {}.".format(pool_ips))

    if reboot_percent_at_a_time:
        # Note: For Python2x 100% must be in Float format, otherwise will not count properly
        reboot_at_a_time = int(ceil(len(pool_ips) / 100.0 * reboot_percent_at_a_time))
        print("Reboot % of nodes at a time: {}%".format(reboot_percent_at_a_time))

    elif reboot_nodes_at_a_time:
        reboot_at_a_time = reboot_nodes_at_a_time

    else:
        reboot_at_a_time = ceil(len(pool_ips) / 10)
        print("Looks like NO # of nodes to be rebooted at a time was given, the default is set to 10%!")

    print("Total # of nodes in pool: {}".format(len(pool_ips)))
    print("Reboot nodes at one time: {} (rounded up)".format(reboot_at_a_time))

    return reboot_at_a_time


def generate_nodes_to_reboot(pool_ips, reboot_at_a_time):
    """Depending on the # of nodes to reboot at a time it will yeld supplying list of IPS to operate with
    :param pool_ips: list of ips in pool
    :param reboot_at_a_time: number of nodes to reboot at a time (precalculated by `count_num_nodes_to_reboot_at_a_time`)
    :return: yield list of node names to reboot at a time
    """
    while pool_ips:
        nodes_to_reboot = []
        for each in range(reboot_at_a_time):
            try:
                nodes_to_reboot.append(pool_ips.pop(0))
            except IndexError:
                continue

        yield nodes_to_reboot
