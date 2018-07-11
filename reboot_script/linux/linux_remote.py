
class CommandLinux:
    """
    use CommandLinux class to authenticate and issue
    Terminal commands to any Linux machine you have access to.
    """

    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password

    @staticmethod
    def fill_queue(data, queue):
        print("adding data: {} into Queue".format(data))
        queue.put(data)

    @staticmethod
    def get_all_from_queue_one_at_time(queue):
        while not queue.empty():
            yield queue.get()

    def remote_call_linux(self, command, await_output=True):
        import subprocess

        # Note: we can pass server names or ips under "server" variable as ssh cmd is compiled the same way
        full_cmd = "sshpass -p " + self.password + " ssh -o StrictHostKeyChecking=no " + self.username + "@" + self.server + " " + command

        answer_download = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Note: await_output is useful when you dont use/want to wait for output or the subprocess would hang waiting
        # for terminal output infinitely (e.g. reboot hangs the terminal)
        if await_output is True:
            stdout, stderr = answer_download.communicate()

            if answer_download.returncode == 0 or answer_download.returncode == 3:
                return True, stdout
            else:
                print("Server: {}, Something's gone wrong".format(self.server))
                return False, stdout
        else:
            return True

    def sudo_remote_call_linux(self, command, await_output=True):
        import subprocess

        # Note: we can pass server names or ips under "server" variable as ssh cmd is compiled the same way
        full_cmd = "sshpass -p " + self.password + " ssh -o StrictHostKeyChecking=no " + self.username + "@" + self.server + " 'echo " + self.password + " | sudo -S bash; " + command + "'"

        answer_download = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Note: await_output is useful when you dont use/want to wait for output or the subprocess would hang waiting
        # for terminal output infinitely (e.g. reboot hangs the terminal)
        if await_output is True:
            stdout, stderr = answer_download.communicate()

            if answer_download.returncode == 0 or answer_download.returncode == 3:
                return True, stdout
            else:
                print("Server: {}, Something's gone wrong".format(self.server))
                return False, stdout
        else:
            return True

    @staticmethod
    def sleep_after_reboot(seconds):
        import time
        time.sleep(seconds)

    def reboot_linux(self):
        reboot_cmd = 'sudo /usr/sbin/reboot'

        print("Server: {}, Initiating reboot".format(self.server))
        success = self.sudo_remote_call_linux(reboot_cmd, await_output=False)

        return success

    def verify_rebooted(self):

        command = "uptime | awk '{print $3,$4}'"
        success, output = self.remote_call_linux(command)

        if success is True:
            try:
                raw_output = output.split(" ")
                uptime_digit = int(raw_output[0])
                uptime_timeframe = raw_output[1][:-2]

                if uptime_timeframe == 'min' and uptime_digit <= 5:
                    print("Server: {}, Yeeey uptime is less than 5min! Actual uptime: {} {}".format(self.server,
                                                                                                    uptime_digit,
                                                                                                    uptime_timeframe))
                    return True
                else:
                    print("Server: {}, The server has NOT been Rebooted! The uptime is still {} {}".format(
                        self.server, uptime_digit, uptime_timeframe))
                    return False
            except ValueError:
                print("Server: {}, Unexpected output given: {}".format(self.server, output))
                return False
        else:
            print("Server: {}, Something's gone wrong along the way of retrieving uptime".format(self.server))
            return False

    def stop_start_restart_service(self, service, action="restart"):
        # CentOS v7x and above :  "systemctl status httpd"
        # CentOS v6x and bellow:  "service httpd status"

        service_cmd = 'sudo /sbin/service {} {}"'.format(service, action)

        print("Server: {}, initiating action: {} {}.\n".format(self.server, service, action))
        success, output = self.remote_call_linux(service_cmd)

        return success, output
