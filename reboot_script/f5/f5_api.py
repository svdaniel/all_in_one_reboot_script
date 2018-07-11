
class F5ApiWrapper:
    """
    :param f5_lbname: choose LB from above
    :param f5_server: supported: PROD/DR/QA/China
    :param username: provide F5 login username
    :param password: provide F5 login password

    F5ApiWrapper Class provides an easy way of communicating with F5.

    """

    def __init__(self, f5_lbname, f5_server, username, password):
        self.f5_server = f5_server
        self.f5_link = self.get_f5_link()
        self.f5_lbname = f5_lbname
        self.password = password

        if "@<REPLACE>.com" not in username:
            self.username = username + "@<REPLACE>.com"
        else:
            self.username = username

        if f5_server == "china":
            self.f5_lbname = "<REPLACE>.com".format(f5_lbname)

    def get_f5_link(self):
        if self.f5_server == "prod":
            return "https://f5api.<REPLACE>.com/"
        elif self.f5_server == "dr":
            return "https://drf5api.<REPLACE>.com/"
        elif self.f5_server == "qa":
            return "https://qaf5api.<REPLACE>.com/"
        elif self.f5_server == "china":
            return "https://<REPLACE>.com/"
            # alternative >> "https://f5api.service.cnqr.io"

    @staticmethod
    def get_ip_from_server_name(server_name):
        """
        Given a server name, it will return IP

        :param server_name: provide server name to be transferred into IP
        :type server_name: str
        """

        import socket

        try:
            return socket.gethostbyname(server_name)

        except socket.gaierror:
            print("Server: {}, no DNS found.".format(server_name))
            return None

    def authentication(self):
        """
        Authentication method
        """
        auth = (self.username, self.password)
        return auth

    def api_call(self, link_extension, data):
        """
        API Call function with use of requests module
        To be called by other functions

        :param link_extension: provide link_end (e.g. '/find_pool')
        :param data: payload
        :return: answered.json()
        """

        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        from requests.exceptions import ConnectionError

        api_link = self.f5_link + link_extension
        f5_header = {'Content-Type': 'application/json'}
        try:
            answered = requests.post(api_link, verify=False, json=data, headers=f5_header, auth=self.authentication())
            return answered.json()
        except ConnectionError:
            print("ERROR: F5 API Call received ConnectionError: {}".format(ConnectionError))
            import time
            print("Trying recovery to sleep 5s and retry:")
            time.sleep(5)

            answered = requests.post(api_link, verify=False, json=data, headers=f5_header, auth=self.authentication())
            return answered.json()

    def find_pool_ip_is_in(self, ip):
        """
        Logic to obtain list of pools given IP is member of:

        :param ip: provide single IP

        :returns:
            if len(pool) == 2 or more >> {"10.205.23.51": ["pool1", "pool2"]}

            if len(pool) == 1 >> {"10.205.23.51": "pool1"}

            if len(pool) == 0 >> ["10.205.23.51"]

            if error >> ["10.205.23.51"]
        """
        # Input: "10.205.23.51"

        pool_to_verify = {}
        ip_in_multiple_pools = {}

        ip_not_in_any_pool = []
        error = []

        link_extension = 'nodefinder/v1/'
        data = {"address": ip, "lbname": self.f5_lbname}
        answered = self.api_call(link_extension=link_extension, data=data)

        if answered is None:
            return False

        try:
            pool_used = [each['poolUsed'] for each in answered["poolInfo"]]

            if len(pool_used) is 1:
                if pool_used[0] is True:
                    pool = [answered["poolInfo"][0]["poolName"]]

                    print("IP: {} found in pool: {}".format(ip, pool))

                    return pool

                elif pool_used[0] is False:
                    # with lock:
                    print("IP: {} NOT found in any pool".format(ip))

                    return []

            elif len(pool_used) >= 2:
                pools = [each['poolName'] for each in answered["poolInfo"]]

                # with lock:
                print("IP: {} found in MULTIPLE pools: {}".format(ip, pools))

                return pools

        except TypeError:
            print("IP: {}, TypeError occurred!".format(ip))
            return []

        return pool_to_verify, ip_in_multiple_pools, ip_not_in_any_pool, error

    def get_ips_of_members_in_pool(self, pool):
        """
        Returns a list of all ips in given pool

        :param pool: provide pool name
        :return: list of IPs
        """

        link_extension = 'poolmemberlist/v1/'

        data = {"poolname": pool, "lbname": self.f5_lbname}
        answered = self.api_call(link_extension=link_extension, data=data)

        pool_ips = [one["ipaddress"] for one in answered if "ipaddress" in one]

        if not pool_ips:
            print("\n\nPool: {}, ERROR: Something's gone wrong, perhaps the pool is misspelled or not in this loadbalancer: {}\n\n".format(pool, self.f5_lbname))

        return pool_ips

    def get_pool_members_state(self, pool):
        """
        Outputs state of all pool member IPs

        :param pool: pool name
        :return: pool_members_state == {"test_node1": "available", "test_node2": "Forced Down", ...}
        """

        link_extension = 'poolmemberstats/v1/'
        pool_members_state = {}

        data = {"poolname": pool, "lbname": self.f5_lbname}
        answered = self.api_call(link_extension=link_extension, data=data)
        print(answered)

        if 'errorStack' in answered:
            print("Pool NOT found! Output: {}".format(answered['message']))
            return answered['message']

        else:
            for each in answered:
                # if each['healthCheck']['state'] == 'available':
                pool_members_state[each['nodeName']] = str(each['serverState']).lower()
                # else:
                #     pool_members_state[each['nodeName']] = str(each['healthCheck']['message']).lower()

            print("Pool: {}, members state: {}\n".format(pool, pool_members_state))
            return pool_members_state

    @staticmethod
    def calculate_pool_availability(pool_members_state):
        """
        .. note::
            Not used on its own, rather called by full_pool_health_calculation_logic()

        :param pool_members_state: list obtained from `get_pool_members_state`
        :return: available (int), forced_down (int), undefined (dict)
        """

        available = 0
        forced_down = 0
        undefined = {}

        for key, value in pool_members_state.items():
            if value == 'enabled':
                available += 1
            elif value == 'disabled':
                forced_down += 1
            # elif value == 'Forced down':
            #     forced_down += 1
            elif value == 'Parent down':
                print("Parent Down >> Looks like 0 nodes are available in the pool!")
                forced_down += 1
            else:
                undefined[key] = value

        print("Available: {}".format(available))
        print("Forced Down: {}".format(forced_down))
        print("Undefined: {}\n".format(undefined))

        return available, forced_down, undefined

    @staticmethod
    def pool_health(available, forced_down, acceptable_health_percentage):
        """
        .. note::
            Not used on its own, rather called by full_pool_health_calculation_logic()

        :param available: int - obtained from calculate_pool_availability()
        :param forced_down: int - obtained from calculate_pool_availability()
        :param acceptable_health_percentage: int - % ratio of how pool health
        :return: bool
        """

        entire_pool = available + forced_down
        try:
            pool_health = int(available / entire_pool * 100)

            if pool_health >= acceptable_health_percentage:
                print("Pool health state: {} % healthy, minimum health acceptable is: {} %\n".format(pool_health, acceptable_health_percentage))
                return True

            else:
                print("Pool is NOT healthy: only {} % healthy, minimum health acceptable is: {} %\n".format(pool_health, acceptable_health_percentage))
                return False

        except ZeroDivisionError:
            print("ZeroDivisionError: Seems incorrect or 0 pool length returned: returned: {}\n".format(entire_pool))
            return False

    def full_pool_health_calculation_logic(self, pool, acceptable_health_percentage):
        """
        Full logic, calling several functions:
            I. get_pool_members_state()
            II. calculate_pool_availability()
            III. pool_health()

        :param pool: pool name
        :param acceptable_health_percentage: int - % ratio of how pool health
        :return: bool
        """

        healthy = False
        max_retry = 2
        current_loop = 0

        while healthy is False and current_loop <= max_retry:
            #   I. get_pool_members_state()
            pool_members_state = self.get_pool_members_state(pool)

            #   II. calculate_pool_availability()
            available, forced_down, undefined = self.calculate_pool_availability(pool_members_state)

            #   III. pool_health()
            healthy = self.pool_health(available, forced_down, acceptable_health_percentage)

            if healthy is False:
                import time
                print("Sleeping 60s before checking again to allow pool to recover.")
                time.sleep(60)

            current_loop += 1

        print("Pool: {}, is healthy: {}".format(pool, healthy))
        return healthy

    def full_multiple_pools_health_calculation_logic(self, *args):
        """
        Full logic, calling several functions >> only used when IP is member of 2 or more pools
            I. get_pool_members_state()
            II. calculate_pool_availability()
            III. pool_health()

        :param args: (pool, acceptable_health_percentage)
        :return: saves returning data to queue
        """
        print("THEADING LEVEL III. >> Multiple Pools Health Calculations level Threading")

        pool, raw_args = args
        acceptable_health_percentage, queue = raw_args

        healthy = False
        max_retry = 2
        current_loop = 0

        while healthy is False and current_loop <= max_retry:
            #   I. get_pool_members_state()
            pool_members_state = self.get_pool_members_state(pool)

            #   II. calculate_pool_availability()
            available, forced_down, undefined = self.calculate_pool_availability(pool_members_state)

            #   III. pool_health()
            healthy = self.pool_health(available, forced_down, acceptable_health_percentage)

            # if healthy is False:
            #     import time
            #     time.sleep(60)

            current_loop += 1

        print("Pool: {}, is healthy: {}".format(pool, healthy))
        queue.enter_single_data(healthy)

    def ip_status_in_f5(self, ip, pool):
        """
        Returns IP's availability status in given pool

        :param ip: ip
        :param pool: pool name
        :return: bool
        """

        link_extension = 'poolmemberstats/v1/'
        data = {"poolname": pool, "address": ip, "lbname": self.f5_lbname}

        answered = self.api_call(link_extension=link_extension, data=data)

        if answered is None:
            return False, {ip: "False, F5 API IP Status collection received error"}

        elif 'errorStack' in answered:
            return {ip: answered['message']}

        else:
            if answered[0]['serverState'] == 'enabled':
                # IP Is enabled and good to go
                print("IP: {}: is Enabled in Pool: {}".format(ip, pool))
                return True, answered[0]['healthCheck']['message']

            elif answered[0]['serverState'] == 'disabled':
                if answered[0]['healthCheck']['state'] == 'available':
                    # IP Is disabled on Pool level
                    print("IP: {}: is Disabled on Pool Level. Skipping run for this node!".format(ip))
                    return False, answered[0]['healthCheck']['message']
                elif answered[0]['healthCheck']['state'] == 'offline':
                    # IP Is Forced Down on Pool level
                    print("IP: {}: is Forced offlne on Pool Level. Skipping run for this node!".format(ip))
                    return False, answered[0]['healthCheck']['message']
                else:
                    # IP Is disabled with unknown output
                    print("IP: {}: is Disabled with unrecognized output. Skipping run for this node!".format(ip))
                    return False, answered[0]['healthCheck']['message']

            elif answered[0]['serverState'] == 'disabled-by-parent':
                # IP Is Forced Down on Node level
                print("IP: {}: is Disabled on Node Level. Skipping run for this node!".format(ip))
                return False, answered[0]['healthCheck']['message']

            else:
                print("IP: {}: IP F5 status returned unrecognized output: {}. Skipping run for this node!".format(ip, answered))
                return False, answered

    def ip_active_connections_in_f5(self, ip, pool):
        """
        Lists # of active connections within given pool and IP

        :param ip: ip
        :param pool: pool name
        :return: int - active_connections
        """

        link_extension = 'poolmemberstats/v1/'
        data = {"poolname": pool, "address": ip, "lbname": self.f5_lbname}

        answered = self.api_call(link_extension=link_extension, data=data)

        if 'errorStack' in answered:
            return answered['message']

        else:
            for each in answered:
                active_connections = each['curConns']
                return active_connections

    def disable_ip_on_node_level(self, ip):
        """
        Disables IP on node level in F5

        :param ip: ip
        :return: bool
        """

        link_extension = 'nodestate/v1/'
        data = {"state": "disabled", "lbname": self.f5_lbname, "address": [ip]}
        print(data)

        answered = self.api_call(link_extension=link_extension, data=data)
        if 'errors' in answered:
            print("Error while disabling IP: {}! Reason: {}".format(ip, answered['errors'][0]))
            return False

        else:
            state = answered['state'][0]['state']
            success = answered['state'][0]['success']

            if state == "disabled" and success is True:
                print("Successfully Disabled IP: {} in F5".format(ip))
                return True
            else:
                print("Failed to Disable IP: {} in F5! Full return message: {}".format(ip, answered))
                return False

    def enable_ip_on_node_level(self, ip):
        """
        Enables IP on node level in F5

        :param ip: ip
        :return: bool
        """

        link_extension = 'nodestate/v1/'
        data = {"state": "enabled", "lbname": self.f5_lbname, "address": [ip]}

        answered = self.api_call(link_extension=link_extension, data=data)
        if 'errors' in answered:
            print("Error while Enabling IP: {}! Reason: {}".format(ip, answered['errors'][0]))
            return False

        else:
            state = answered['state'][0]['state']
            success = answered['state'][0]['success']

            if state == "enabled" and success is True:
                print("Successfully Enabled IP: {} in F5".format(ip))
                return True
            else:
                print("Failed to Enable IP: {} in F5! Full return message: {}".format(ip, answered))
                return False

    def disable_and_bleed(self, ip, pool, time_out, bleed_until_num_of_connections, force=False):
        """
        Logic for disabling and awaiting active connections for the IP to bleed in given pool

        :param ip: ip
        :param pool: pool name
        :param time_out: seconds to wait
        :param bleed_until_num_of_connections: int - max. allowed connections
        :param force: bool
        :return: bool - success
        """
        import time
        from datetime import datetime, timedelta

        disable_success = self.disable_ip_on_node_level(ip=ip)

        print("IP: {}, Disable success: {}".format(ip, disable_success))

        if force is True:
            print("Force is True, no need to wait to bleed.")
            return disable_success

        else:
            if disable_success is True:
                active_connections = int(self.ip_active_connections_in_f5(ip, pool))
                print("Server: {}, current number of active connections: {}. Allowing {}s to bleed.".format(ip, active_connections, time_out))
                if active_connections > bleed_until_num_of_connections:

                    bleed_time_out = datetime.now() + timedelta(seconds=time_out)
                    while active_connections > bleed_until_num_of_connections or bleed_time_out >= datetime.now():
                        print("Server: {}, current number of active connections: {}. Allowing {}s to bleed.".format(ip, active_connections, time_out))
                        time.sleep(10)
                        active_connections = int(self.ip_active_connections_in_f5(ip, pool))

                print("Server: {} has been disabled: {} & serves less than max. number of active connections or timeout clocked out. Current active connections: {}".format(ip, disable_success, active_connections))

        return disable_success
