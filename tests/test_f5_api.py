from unittest import mock
from reboot_script.f5 import f5_api
import pytest


class TestF5ApiWrapper:

    # FIXTURES
    # =============================
    @pytest.fixture(scope="module")
    def f5_username_password(self):
        return "test@<REPLACE>.com", "dummy"

    @pytest.fixture(scope="module")
    def create_f5api_class(self):
        f5_server = "prod"
        f5_lbname = "intf5"
        username = "test@<REPLACE>.com"
        password = "dummy_password"
        f5api = f5_api.F5ApiWrapper(f5_lbname, f5_server, username, password)

        return f5api

    # UNIT TESTs
    # =============================

    # TEST get_f5_link
    # =============================

    def test_get_f5_prod_link(self, create_f5api_class):
        assert create_f5api_class.f5_link == "https://f5api.<REPLACE>.com/"

    def test_get_f5_dr_link(self, f5_username_password):
        f5_server = "dr"
        f5_lbname = "drf5"
        username, password = f5_username_password

        f5api = f5_api.F5ApiWrapper(f5_lbname, f5_server, username, password)
        assert f5api.f5_link == "https://drf5api.<REPLACE>.com/"

    def test_get_f5_qa_link(self, f5_username_password):
        f5_server = "qa"
        f5_lbname = "qaf5"
        username, password = f5_username_password

        f5api = f5_api.F5ApiWrapper(f5_lbname, f5_server, username, password)
        assert f5api.f5_link == "https://qaf5.<REPLACE>.com/"

    def test_get_f5_china_alpha_link(self, f5_username_password):
        f5_server = "china"
        f5_lbname = "alpha"
        username, password = f5_username_password

        f5api = f5_api.F5ApiWrapper(f5_lbname, f5_server, username, password)
        assert f5api.f5_link == "https://<REPLACE>.com/"
        assert f5api.f5_lbname == "<REPLACE>.com"

    def test_get_f5_china_beta_link(self, f5_username_password):
        f5_server = "china"
        f5_lbname = "beta"
        username, password = f5_username_password

        f5api = f5_api.F5ApiWrapper(f5_lbname, f5_server, username, password)
        assert f5api.f5_link == "https://<REPLACE>.com/"
        assert f5api.f5_lbname == "<REPLACE>.com"

    # TEST get_ip_from_server_name
    # =============================

    @mock.patch("socket.gethostbyname")
    def test_success_get_ip_from_server_name(self, my_mock, create_f5api_class):
        my_mock.return_value = "0.0.0.0"
        ips, failed_to_locate = create_f5api_class.get_ip_from_server_name("dummy.com")
        assert ips == ["0.0.0.0"]
        assert failed_to_locate == []
        my_mock.called_once_with("dummy.com")

    @mock.patch("socket.gethostbyname")
    def test_success_get_ip_from_server_name_ips_arg_given(self, my_mock, create_f5api_class):
        my_mock.return_value = "0.0.0.0"
        ips = ["test"]
        ip, failed_to_locate = create_f5api_class.get_ip_from_server_name("dummy.com", ips)
        assert ip == ["test", "0.0.0.0"]
        assert failed_to_locate == []
        my_mock.called_once_with("dummy.com", ["test"])

    @mock.patch("socket.gethostbyname")
    def test_failed_get_ip_from_server_name_ips_arg_given(self, my_mock, create_f5api_class):
        import socket
        my_mock.side_effect = socket.gaierror

        ips = ["test"]
        ip, failed_to_locate = create_f5api_class.get_ip_from_server_name("dummy.com", ips)
        # assert ip == []
        assert failed_to_locate == ["dummy.com"]
        my_mock.called_once_with("dummy.com", ["test"])

    # TEST authentication
    # =============================
    def test_authentication(self, create_f5api_class):
        assert create_f5api_class.authentication() == ("test@<REPLACE>.com", "dummy_password")

    # TEST find_pool_ip_is_in
    # =============================
    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_find_pool_ip_is_in_fill_pool_to_verify(self, my_mock, create_f5api_class):
        my_mock.return_value = {"poolInfo": [{"poolUsed": True, "poolName": "test_pool"}]}
        test_ip = "0.0.0.0"

        pool_to_verify, ip_in_multiple_pools, ip_not_in_any_pool, error = create_f5api_class.find_pool_ip_is_in(test_ip)
        assert pool_to_verify == {test_ip: "test_pool"}

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_find_pool_ip_is_in_fill_ip_not_in_any_pool(self, my_mock, create_f5api_class):
        my_mock.return_value = {"poolInfo": [{"poolUsed": False, "poolName": ""}]}
        test_ip = "0.0.0.0"

        pool_to_verify, ip_in_multiple_pools, ip_not_in_any_pool, error = create_f5api_class.find_pool_ip_is_in(test_ip)
        assert ip_not_in_any_pool == ["0.0.0.0"]

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_find_pool_ip_is_in_fill_ip_in_multiple_pools(self, my_mock, create_f5api_class):
        my_mock.return_value = {"poolInfo": [{"poolUsed": True, "poolName": "1st_test_pool"}, {"poolUsed": True, "poolName": "2nd_test_pool"}]}
        test_ip = "0.0.0.0"

        pool_to_verify, ip_in_multiple_pools, ip_not_in_any_pool, error = create_f5api_class.find_pool_ip_is_in(test_ip)
        assert ip_in_multiple_pools == {test_ip: ["1st_test_pool", "2nd_test_pool"]}

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_find_pool_ip_is_in_fill_error(self, my_mock, create_f5api_class):
        my_mock.return_value = {"test_error"}
        test_ip = "0.0.0.0"

        pool_to_verify, ip_in_multiple_pools, ip_not_in_any_pool, error = create_f5api_class.find_pool_ip_is_in(test_ip)
        assert error == ["0.0.0.0"]

    # TEST get_ips_of_members_in_pool
    # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_get_ips_of_members_in_pool_failed(self, my_mock, create_f5api_class):
        my_mock.return_value = {"oopla": "should return empty dict"}
        pool = "dummy_pool"
        pools_and_member_ips = create_f5api_class.get_ips_of_members_in_pool(pool)
        assert pools_and_member_ips == {}

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_get_ips_of_members_in_pool_success(self, my_mock, create_f5api_class):
        my_mock.return_value = [
            {
                'partition': 'Common',
                'ipaddress': '0.0.0.0',
                'nodename': 'dummy_server:8080'},
            {
                'partition': 'Common',
                'ipaddress': '0.0.0.1',
                'nodename': 'dummy_server2:8080'
            }
        ]

        pool = "dummy_pool"
        pools_and_member_ips = create_f5api_class.get_ips_of_members_in_pool(pool)
        assert pools_and_member_ips == {"dummy_pool": ['0.0.0.0', '0.0.0.1']}

    # TEST get_pool_members_state
    # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_get_pool_members_state_error_stack(self, my_mock, create_f5api_class):
        my_mock.return_value = {"errorStack": "", "message": "dummy_error_stack_message"}
        pool = "dummy_pool"
        pool_members_state, pool_not_found = create_f5api_class.get_pool_members_state(pool)
        assert pool_members_state == {}
        assert pool_not_found == {pool: "dummy_error_stack_message"}

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_get_pool_members_state_available_and_forced_down(self, my_mock, create_f5api_class):
        my_mock.return_value = [
            {
                "nodeName": "test_node1",
                "healthCheck":
                    {
                        "state": "available"
                    }
            },
            {
                "nodeName": "test_node2",
                "healthCheck":
                    {
                        "state": "disabled",
                        "message": "Forced down"
                    }
            }
        ]

        pool = "dummy_pool"
        pool_members_state, pool_not_found = create_f5api_class.get_pool_members_state(pool)
        assert pool_not_found == {}
        assert pool_members_state == {"test_node1": "available", "test_node2": "Forced down"}

    # TEST calculate_pool_availability
    # =============================

    def test_calculate_pool_availability(self, create_f5api_class):
        pool_members_state = {
            "test_node1": "available",
            "test_node2": "available",
            "test_node3": "available",
            "test_node4": "Forced down",
            "test_node5": "Forced down",
            "test_node6": "should go undefined"
        }
        available, forced_down, undefined = create_f5api_class.calculate_pool_availability(pool_members_state)

        assert available == 3
        assert forced_down == 2
        assert undefined == {"test_node6": "should go undefined"}

    # TEST pool_health
    # =============================

    def test_pool_health_true(self, create_f5api_class):
        available = 3
        forced_down = 2
        acceptable_health_percentage = 60

        returned_value = create_f5api_class.pool_health(available, forced_down, acceptable_health_percentage)
        assert returned_value is True

    def test_pool_health_false(self, create_f5api_class):
        available = 2
        forced_down = 3
        acceptable_health_percentage = 60

        returned_value = create_f5api_class.pool_health(available, forced_down, acceptable_health_percentage)
        assert returned_value is False

    # TEST ip_status_in_f5
    # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_ip_status_in_f5_available(self, my_mock, create_f5api_class):
        my_mock.return_value = [
            {
                'nodeName': 'dummy_node_name',
                'healthCheck': {'state': 'available', 'message': 'Pool member is available'},
                'maxConns': 8,
                'nodePort': 8000,
                'address': 'dummy_returned_IP',
                'curConns': 0,
                'serverState': 'enabled'
            }
        ]

        ip_with_pool = {"dummy_IP": "dummy_pool"}
        returned_value = create_f5api_class.ip_status_in_f5(ip_with_pool)
        assert returned_value == 'available'

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_ip_status_in_f5_forced_down(self, my_mock, create_f5api_class):
        my_mock.return_value = [
            {
                'nodeName': 'dummy_node_name',
                'healthCheck': {'state': 'offline', 'message': 'Forced down'},
                'maxConns': 0,
                'nodePort': 8080,
                'address': 'dummy_returned_IP',
                'curConns': 0,
                'serverState': 'disabled'
            }
        ]

        ip_with_pool = {"dummy_IP": "dummy_pool"}
        returned_value = create_f5api_class.ip_status_in_f5(ip_with_pool)
        assert returned_value == 'Forced down'

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_ip_status_in_f5_error_stack(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'errorStack': [],
            'message': 'dummy_error_stack_message',
            'code': 404,
            'apiError': 3
        }

        ip_with_pool = {"dummy_IP": "dummy_pool"}
        returned_value = create_f5api_class.ip_status_in_f5(ip_with_pool)
        assert returned_value == {"dummy_IP": "dummy_error_stack_message"}

    # TEST ip_active_connections_in_f5
    # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_ip_active_connections_in_f5_available(self, my_mock, create_f5api_class):
        my_mock.return_value = [
            {
                'nodeName': 'dummy_node_name',
                'healthCheck': {'state': 'available', 'message': 'Pool member is available'},
                'maxConns': 8,
                'nodePort': 8000,
                'address': 'dummy_returned_IP',
                'curConns': 0,
                'serverState': 'enabled'
            }
        ]

        ip_with_pool = {"dummy_IP": "dummy_pool"}
        returned_value = create_f5api_class.ip_active_connections_in_f5(ip_with_pool)
        assert returned_value == 0

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_ip_active_connections_in_f5_error_stack(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'errorStack': [],
            'message': 'dummy_error_stack_message',
            'code': 404,
            'apiError': 3
        }

        ip_with_pool = {"dummy_IP": "dummy_pool"}
        returned_value = create_f5api_class.ip_active_connections_in_f5(ip_with_pool)
        assert returned_value == {"dummy_IP": "dummy_error_stack_message"}

    # TEST disable_ip_on_node_level
    # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_disable_ip_on_node_level_success(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'sessionID': 'dummy_account@concurasp.com',
            'state':
                [
                    {
                        'address': 'dummy_returned_IP',
                        'nodeName': 'dummy_node_name',
                        'partition': 'Common',
                        'state': 'disabled',
                        'success': True
                    }
                ]
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.disable_ip_on_node_level(ip)
        assert returned_value is True

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_disable_ip_on_node_level_false(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'sessionID': 'dummy_account@concurasp.com',
            'state':
                [
                    {
                        'address': 'dummy_returned_IP',
                        'nodeName': 'dummy_node_name',
                        'partition': 'Common',
                        'state': 'enabled',
                        'success': False
                    }
                ]
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.disable_ip_on_node_level(ip)
        assert returned_value is False

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_disable_ip_on_node_level_failed(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'errors':
                [
                    {
                        'address': '1',
                        'message': '1 not in intf5 node list',
                        'success': False
                    }
                ],
            'sessionID': 'dummy_account@concurasp.com'
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.disable_ip_on_node_level(ip)
        assert returned_value is False

    # TEST enable_ip_on_node_level
        # =============================

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_enable_ip_on_node_level_success(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'sessionID': 'dummy_account@concurasp.com',
            'state':
                [
                    {
                        'address': 'dummy_returned_IP',
                        'nodeName': 'dummy_node_name',
                        'partition': 'Common',
                        'state': 'enabled',
                        'success': True
                    }
                ]
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.enable_ip_on_node_level(ip)
        assert returned_value is True

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_enable_ip_on_node_level_false(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'sessionID': 'dummy_account@concurasp.com',
            'state':
                [
                    {
                        'address': 'dummy_returned_IP',
                        'nodeName': 'dummy_node_name',
                        'partition': 'Common',
                        'state': 'disabled',
                        'success': False
                    }
                ]
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.enable_ip_on_node_level(ip)
        assert returned_value is False

    @mock.patch("reboot_script.f5.f5_api.F5ApiWrapper.api_call")
    def test_enable_ip_on_node_level_failed(self, my_mock, create_f5api_class):
        my_mock.return_value = {
            'errors':
                [
                    {
                        'address': '1',
                        'message': '1 not in seaintf5 node list',
                        'success': False
                    }
                ],
            'sessionID': 'dummy_account@concurasp.com'
        }

        ip = "dummy_IP"
        returned_value = create_f5api_class.enable_ip_on_node_level(ip)
        assert returned_value is False

    # TEST
        # =============================
