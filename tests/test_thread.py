from reboot_script.get_threading.thread import my_threading
import pytest


# FIXTURES Setup
# ============================

@pytest.fixture(scope="function")
def setup_queue():
    try:
        import queue
    except ImportError:
        import Queue as queue

    successful_queue = queue.Queue()
    failed_queue = queue.Queue()

    return successful_queue, failed_queue


# INTEGRATION TESTs
# ============================

def test_my_threading(setup_queue):
    successful_queue, failed_queue = setup_queue

    server_list = ["server1", "server2", "server3", "server4", "server5"]

    def func_being_threaded(server, cmd, successful_queue, failed_queue):
        return successful_queue.put(server)

    my_threading(successful_queue, failed_queue, func_being_threaded, server_list, "no extra *args")

    get_result = []
    while not successful_queue.empty():
        get_result.append(successful_queue.get())

    assert get_result == ["server1", "server2", "server3", "server4", "server5"]
