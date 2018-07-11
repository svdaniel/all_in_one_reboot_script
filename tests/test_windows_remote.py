from reboot_script.windows.windows_remote import CommandWindows
from unittest import mock
import pytest


class TestCommandWindows:

    # MOCK Subprocess.Popen class
    # =============================

    # FIXTURES
    # =============================
    @pytest.fixture("function")
    def tested_class(self):
        return CommandWindows()

    @pytest.fixture(scope='function')
    def queue_fixture(self):
        try:
            # python 3x
            import queue
        except ImportError:
            # python 2x
            import Queue as queue

        successful_queue = queue.Queue()
        failed_queue = queue.Queue()

        return successful_queue, failed_queue

    # TEST kinit_krb_tkt
    # =============================
    def test_kinit_krb_tkt_only_homepath_path_to_keytab_arg_provided(self, tested_class):
        home_path = '/test/home/path'
        path_to_keytab = "/dummy/path/to/keytab"

        returned_value = tested_class.kinit_krb_tkt(home_path=home_path, path_to_keytab=path_to_keytab)
        expected_value = "kinit default_sa_jenkins@<REPLACE>.COM -k -t /dummy/path/to/keytab"
        assert returned_value == expected_value

    def test_kinit_krb_tkt_only_home_path_user_realm_args_provided(self, tested_class):
        user = 'user'
        realm = 'REALM.COM'
        home_path = '/test/home/path'

        returned_value = tested_class.kinit_krb_tkt(user, realm, home_path)
        expected_value = "kinit user@REALM.COM -k -t /test/home/path/.keytab/user.keytab"
        assert returned_value == expected_value

    # TEST decide_winrm_link
    # =============================
    def test_decide_winrm_link_ip(self, tested_class):
        ip = '10.10.10.10'

        returned_value = tested_class.decide_winrm_link(ip)
        expected_value = "http://{}:5985/wsman".format(ip)

        assert returned_value == expected_value

    def test_decide_winrm_link_server(self, tested_class):
        server = "seapr1smweb001"

        returned_value = tested_class.decide_winrm_link(server)
        expected_value = "http://{}.<REPLACE>.com:5985/wsman".format(server)

        assert returned_value == expected_value

    # TEST fill_queue
    # =============================

    def test_fill_queue_fill_successful(self, tested_class, queue_fixture):

        data = {"test": "success"}
        successful_queue, failed_queue = queue_fixture

        tested_class.fill_queue(data, successful_queue=successful_queue)
        assert successful_queue.get() == {"test": "success"}

    def test_fill_queue_fill_failed(self, tested_class, queue_fixture):

        data = {"test": "failed"}
        successful_queue, failed_queue = queue_fixture

        tested_class.fill_queue(data, failed_queue=failed_queue)
        assert failed_queue.get() == {"test": "failed"}

    def test_fill_queue_else_clause(self, tested_class):
        data = {"test else": "should return false"}
        success = tested_class.fill_queue(data)
        assert success is False

    # TEST get_all_from_queue_one_at_time
    # =============================

    def test_get_all_from_queue_one_at_time(self, tested_class, queue_fixture):
        successful_queue, failed_queue = queue_fixture

        # Fill queue with test data
        data = {"first": "success", "second": "failure"}
        for k, v in data.items():
            successful_queue.put({k: v})

        returned_generator = tested_class.get_all_from_queue_one_at_time(successful_queue)
        assert next(returned_generator) == {"first": "success"}
        assert next(returned_generator) == {"second": "failure"}
        with pytest.raises(StopIteration):
            next(returned_generator)

    # TEST verify_single_rebooted
    # =============================
    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.call_winrm_powershell")
    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.get_all_from_queue_one_at_time")
    def test_verify_rebooted_true(self, mock_queue, mock_winrm_call, tested_class, queue_fixture):
        mock_winrm_call.return_value = True
        mock_queue.return_value = [{'dummy_server': '0 Days 0 Hours 5 Minutes \r\n'}]

        server = 'dummy_server'
        successful_queue, failed_queue = queue_fixture
        win_verify_rebooted_cmd = """\
        Function Get-Uptime {
        $os = Get-WmiObject win32_operatingsystem -ErrorAction SilentlyContinue
        $uptime = (Get-Date) - $os.ConvertToDateTime($os.LastBootUpTime)
        Write-Output ("" + $uptime.Days + " Days " + $uptime.Hours + " Hours " + $uptime.Minutes + " Minutes " )
        }
        Get-Uptime"""

        success = tested_class.verify_rebooted(server, successful_queue, failed_queue)
        assert success is True

        mock_winrm_call.assert_called_once_with(server, win_verify_rebooted_cmd, successful_queue, failed_queue)

    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.call_winrm_powershell")
    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.get_all_from_queue_one_at_time")
    def test_verify_rebooted_false(self, mock_queue, mock_winrm_call, tested_class, queue_fixture):
        mock_winrm_call.return_value = True
        mock_queue.return_value = [{'dummy_server': '169 Days 2 Hours 37 Minutes \r\n'}]

        server = 'dummy_server'
        successful_queue, failed_queue = queue_fixture
        win_verify_rebooted_cmd = """\
        Function Get-Uptime {
        $os = Get-WmiObject win32_operatingsystem -ErrorAction SilentlyContinue
        $uptime = (Get-Date) - $os.ConvertToDateTime($os.LastBootUpTime)
        Write-Output ("" + $uptime.Days + " Days " + $uptime.Hours + " Hours " + $uptime.Minutes + " Minutes " )
        }
        Get-Uptime"""

        success = tested_class.verify_rebooted(server, successful_queue, failed_queue)
        assert success is False

        mock_winrm_call.assert_called_once_with(server, win_verify_rebooted_cmd, successful_queue, failed_queue)

    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.call_winrm_powershell")
    def test_verify_rebooted_test_else_clause(self, mock_winrm_call, tested_class, queue_fixture):
        mock_winrm_call.return_value = False
        server = 'dummy_server'
        successful_queue, failed_queue = queue_fixture

        success = tested_class.verify_rebooted(server, successful_queue, failed_queue)
        assert success is False

    # TEST stop_start_restart_service
    # =============================
    @mock.patch("reboot_script.windows.windows_remote.CommandWindows.call_winrm_powershell")
    def test_stop_start_restart_service(self, my_mock, tested_class):
        successful_queue, failed_queue = [], []
        server = 'dummy server'
        service = "dummy_service"

        # Test that correct service_cmd is being used
        # STOP
        tested_class.stop_start_restart_service(successful_queue=successful_queue, failed_queue=failed_queue, server=server, service=service, action="stop")
        my_mock.assert_called_with('dummy server', "Stop-Service dummy_service", successful_queue, failed_queue)

        # START
        tested_class.stop_start_restart_service(successful_queue=successful_queue, failed_queue=failed_queue, server=server, service=service, action="start")
        my_mock.assert_called_with('dummy server', "Start-Service dummy_service", successful_queue, failed_queue)

        # RESTART
        tested_class.stop_start_restart_service(successful_queue=successful_queue, failed_queue=failed_queue, server=server, service=service, action="should-autodefault-to-restart")
        my_mock.assert_called_with('dummy server', "Restart-Service dummy_service", successful_queue, failed_queue)

        # RESTART (no action argument given => should fall back to restart)
        tested_class.stop_start_restart_service(successful_queue=successful_queue, failed_queue=failed_queue, server=server, service=service)
        my_mock.assert_called_with('dummy server', "Restart-Service dummy_service", successful_queue, failed_queue)

    # TEST
    # =============================
