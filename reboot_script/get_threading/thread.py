
def my_threading(func, threading_list, *args):
    import threading

    temp_thread_count = []

    while threading_list:
        server = threading_list.pop(0)
        try:
            t = threading.Thread(target=func, args=(server, args), name=server)

            # if daemon_mode is True:
            t.daemon = True
            # else:
            #     t.daemon = False

            t.start()
            temp_thread_count.append(t)
            print("Starting thread for: {}".format(server))

        except ValueError:
            print("ValueError while initiating Thread")
            exit(11)

    print("Now Waiting for all threads to finish before going forth")
    print("Current number of active threads: {}".format(len(temp_thread_count)))
    for every in temp_thread_count:
        every.join()

    print("threads are complete!")


def choose_max_threads(func, threading_list, max_threads, *args):
    import threading

    temp_thread_count = []

    while threading_list:
        for each in range(max_threads):
            try:
                server = threading_list.pop(0)
            except IndexError:
                continue
            try:
                t = threading.Thread(target=func, args=(server, args), name=server)

                # if daemon_mode is True:
                t.daemon = True
                # else:
                #     t.daemon = False

                t.start()
                temp_thread_count.append(t)
                print("Starting thread for: {}".format(server))

            except ValueError:
                print("ValueError while initiating Thread")
                exit(11)

    print("Now Waiting for all threads to finish before going forth")
    print("Current number of active threads: {}".format(len(temp_thread_count)))
    for every in temp_thread_count:
        every.join()

    print("threads are complete!")
