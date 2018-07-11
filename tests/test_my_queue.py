from reboot_script.get_queue.my_queue import MyQueue
import pytest


# FIXTURE Setup
# =============================

@pytest.fixture(scope="function")
def setup_class_myqueue():
    print("MyQueue Setup Fixture initiated.")
    myqueue = MyQueue()
    yield myqueue
    print("MyQueue Teardown Fixture initiated.")
    del myqueue


# TEST MyQueue Class
# =============================

def test_myqueue_enter_and_get_single_data(setup_class_myqueue):
    test_var = {"test_data": 1234}

    myqueue = setup_class_myqueue

    myqueue.enter_single_data(test_var)
    get_var = myqueue.get_single_data()
    assert get_var == {"test_data": 1234}


def test_myqueue_multiple_instances_do_not_leak_information(setup_class_myqueue):
    first_test_var = {"test": 1234}
    second_test_var = {"data": 56789}

    first_class = setup_class_myqueue
    second_class = setup_class_myqueue

    first_class.enter_single_data(first_test_var)
    second_class.enter_single_data(second_test_var)

    get_first_var = first_class.get_single_data()
    get_second_var = second_class.get_single_data()

    assert get_first_var == {"test": 1234}
    assert get_second_var == {"data": 56789}


def test_myqueue_enter_and_get_multiple_list_data(setup_class_myqueue):
    data = [1, 2, 3]

    myqueue = setup_class_myqueue

    myqueue.enter_multiple_data(data)
    returned_data = myqueue.get_list_of_all_data()

    assert returned_data == [1, 2, 3]


def test_myqueue_enter_and_get_multiple_dict_data(setup_class_myqueue):
    data = [{1: "first_test"}, {2: "second_test"}]

    myqueue = setup_class_myqueue

    myqueue.enter_multiple_data(data)
    returned_data = myqueue.get_dict_of_all_data()

    assert returned_data == {1: "first_test", 2: "second_test"}
