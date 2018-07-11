
class MyQueue:
    """
    Doc String can be showed with typing help(MyQueue)
    """

    def __init__(self):
        try:
            # Python 3
            import queue
        except ImportError:
            # Python 2
            import Queue as queue
        self.initiate = queue.Queue()

    def enter_single_data(self, data):
        return self.initiate.put(data)

    def enter_multiple_data(self, data_list):
        for each in data_list:
            self.initiate.put(each)

    def get_single_data(self):
        return self.initiate.get()

    def get_list_of_all_data(self):
        data_list = []
        while not self.initiate.empty():
            data_list.append(self.initiate.get())
        return data_list

    def get_dict_of_all_data(self):
        data_dict = {}
        while not self.initiate.empty():
            _ = self.initiate.get()
            for k, w in _.items():
                data_dict[k] = w
        return data_dict

    def empty(self):
        return self.initiate.empty()
