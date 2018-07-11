from reboot_script.calc_nodes_to_work_with import number_of_nodes_to_reboot
import pytest


# FIXTURES
# =============================
@pytest.fixture(scope="module")
def data():
    pool_ips = ["0.0.0.0", "0.0.0.1", "0.0.0.2", "0.0.0.3",
                "0.0.0.4", "0.0.0.5", "0.0.0.6", "0.0.0.7",
                "0.0.0.8", "0.0.0.9", "0.0.0.10", "0.0.0.11",
                "0.0.0.12", "0.0.0.13", "0.0.0.14", "0.0.0.15"]

    return pool_ips


# TEST count_num_nodes_to_reboot_at_a_time
# =============================

def test_count_num_nodes_to_reboot_at_a_time_test_percent_round_down(data):
    pool_ips = data
    reboot_percent_at_a_time = 20

    reboot_at_a_time = number_of_nodes_to_reboot.count_num_nodes_to_reboot_at_a_time(pool_ips=pool_ips, reboot_percent_at_a_time=reboot_percent_at_a_time)
    assert reboot_at_a_time == 3


def test_count_num_nodes_to_reboot_at_a_time_test_percent_round_up(data):
    pool_ips = data
    reboot_percent_at_a_time = 25

    reboot_at_a_time = number_of_nodes_to_reboot.count_num_nodes_to_reboot_at_a_time(pool_ips=pool_ips,
                                                                                     reboot_percent_at_a_time=reboot_percent_at_a_time)
    assert reboot_at_a_time == 4

def test_count_num_nodes_to_reboot_at_a_time_test_nodes_at_a_time(data):
    pool_ips = data
    reboot_nodes_at_a_time = 10

    reboot_at_a_time = number_of_nodes_to_reboot.count_num_nodes_to_reboot_at_a_time(pool_ips=pool_ips, reboot_nodes_at_a_time=reboot_nodes_at_a_time)
    assert reboot_at_a_time == 10


def test_count_num_nodes_to_reboot_at_a_time_test_default(data):
    pool_ips = data
    reboot_at_a_time = number_of_nodes_to_reboot.count_num_nodes_to_reboot_at_a_time(pool_ips=pool_ips)

    assert reboot_at_a_time == 2


# TEST choose_nodes_to_reboot_at_a_time
# =============================
def test_generate_nodes_to_reboot_success(data):
    pool_ips = data
    reboot_at_a_time = 2
    reboot_at_a_time = number_of_nodes_to_reboot.generate_nodes_to_reboot(pool_ips=pool_ips, reboot_at_a_time=reboot_at_a_time)
    assert next(reboot_at_a_time) == ["0.0.0.0", "0.0.0.1"]
    assert next(reboot_at_a_time) == ["0.0.0.2", "0.0.0.3"]
    assert next(reboot_at_a_time) == ["0.0.0.4", "0.0.0.5"]
