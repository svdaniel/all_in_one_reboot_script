from reboot_script.linux.linux_remote import CommandLinux
from unittest import mock
import pytest


# MOCK Subprocess.Popen class
# =============================

def mocked_subprocess(*args, **kwargs):
    class MockSubprocess:
        def __init__(self, communicate, returncode):
            self.communicate = communicate
            self.returncode = returncode

        def communicate(self):
            return self.communicate

        def returncode(self):
            return self.returncode

    if args[0] == "sshpass -p dummy_password ssh -o StrictHostKeyChecking=no dummy_user@dummy_server return good uptime":
        communicate_back = ('3 min,\n', '')
        returncode = 0
        return MockSubprocess(communicate=communicate_back, returncode=returncode)
    elif args[0] == "sshpass -p dummy_password ssh -o StrictHostKeyChecking=no dummy_user@dummy_server return bad uptime":
        communicate_back = ('14 days,\n', '')
        returncode = 0
        return MockSubprocess(communicate=communicate_back, returncode=returncode)
    else:
        communicate_back = ('', '/bin/sh: sshpass: command not found\n')
        returncode = 1
        return MockSubprocess(communicate=communicate_back, returncode=returncode)


class TestCommandLinux:

    # FIXTURES
    # =============================

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

    @pytest.fixture(scope='function')
    def commandlinux(self):
        return CommandLinux()

    @pytest.fixture(scope='module')
    def linux_args(self):
        server = "dummy_server"
        user = "dummy_user"
        password = "dummy_password"

        return server, user, password

    # TEST fill_queue
    # =============================

    def test_fill_queue_fill_successful(self, commandlinux, queue_fixture):
        tested_class = commandlinux

        data = {"test": "success"}
        successful_queue, failed_queue = queue_fixture

        tested_class.fill_queue(data, successful_queue=successful_queue)
        assert successful_queue.get() == {"test": "success"}

    def test_fill_queue_fill_failed(self, commandlinux, queue_fixture):
        tested_class = commandlinux

        data = {"test": "failed"}
        successful_queue, failed_queue = queue_fixture

        tested_class.fill_queue(data, failed_queue=failed_queue)
        assert failed_queue.get() == {"test": "failed"}

    def test_fill_queue_else_clause(self, commandlinux):
        tested_class = commandlinux
        data = {"test else": "should return false"}
        success = tested_class.fill_queue(data)
        assert success is False

    # TEST get_all_from_queue_one_at_time
    # =============================

    def test_get_all_from_queue_one_at_time(self, commandlinux, queue_fixture):
        tested_class = commandlinux
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

    # TEST remote_call_linux
    # =============================

    @mock.patch("subprocess.Popen", side_effect=mocked_subprocess)
    def test_remote_call_linux_success_queues_provided(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        command = 'return good uptime'

        success, stdout = tested_class.remote_call_linux(server, password, user, command, successful_queue, failed_queue)
        assert success is True
        assert successful_queue.get() == {"dummy_server": '3 min,\n'}
        assert stdout == '3 min,\n'

    @mock.patch("subprocess.Popen", side_effect=mocked_subprocess)
    def test_remote_call_linux_failed_queues_provided(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        command = 'this is not going to end well...'

        success, stdout = tested_class.remote_call_linux(server, password, user, command, successful_queue, failed_queue)
        assert success is False
        assert failed_queue.get() == {"dummy_server": '/bin/sh: sshpass: command not found\n'}
        assert stdout == '/bin/sh: sshpass: command not found\n'

    # TEST linux_verify_rebooted
    # =============================

    @mock.patch("reboot_script.linux.linux_remote.CommandLinux.remote_call_linux")
    def test_linux_verify_rebooted_true(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        my_mock.return_value = (True, '3 min,\n')

        success = tested_class.linux_verify_rebooted(server, password, user, successful_queue, failed_queue)
        assert success is True

    @mock.patch("reboot_script.linux.linux_remote.CommandLinux.remote_call_linux")
    def test_linux_verify_rebooted_false(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        my_mock.return_value = (True, '14 days,\n')

        success = tested_class.linux_verify_rebooted(server, password, user, successful_queue, failed_queue)
        assert success is False

    @mock.patch("reboot_script.linux.linux_remote.CommandLinux.remote_call_linux")
    def test_linux_verify_rebooted_test_valuerror(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        my_mock.return_value = (True, 'well this will fail')

        success = tested_class.linux_verify_rebooted(server, password, user, successful_queue, failed_queue)
        assert success is False

    @mock.patch("reboot_script.linux.linux_remote.CommandLinux.remote_call_linux")
    def test_linux_verify_rebooted_test_else_clause(self, my_mock, commandlinux, queue_fixture, linux_args):
        server, user, password = linux_args
        tested_class = commandlinux
        successful_queue, failed_queue = queue_fixture

        my_mock.return_value = (False, 'well this will fail')

        success = tested_class.linux_verify_rebooted(server, password, user, successful_queue, failed_queue)
        assert success is False


# TEST
# =============================
