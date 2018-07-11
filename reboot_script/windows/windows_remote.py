
class CommandWindows:
    """
    use CommandWindows class to authenticate through kerberos and issue
    Powershell/Terminal commands to any Windows machine you have access to.
    """

    def __init__(self, server, user=None, realm=None):
        self.server = server
        self.user = user
        if self.user is None:
            self.user = "default_sa_jenkins"
        self.realm = realm
        if self.realm is None:
            self.realm = "<REPLACE>.COM"

        self.home_path = ""

    @staticmethod
    def get_home_path():
        import os
        return os.getenv("HOME")

    def get_kinit_command(self, home_path=None, path_to_keytab=None):
        # Request ticket from Kerberos

        if home_path:
            self.home_path = home_path
        else:
            self.home_path = self.get_home_path()

        if path_to_keytab is None:
            path_to_keytab = str(self.home_path) + '/.keytab/' + self.user + ".keytab"

        print("Initiating kinit call for user: {}".format(self.user))

        kinit_command = "kinit " + self.user + "@" + self.realm + " -k -t " + path_to_keytab

        return kinit_command

    @staticmethod
    def kinit_krb_tkt(kinit_command):
        from requests_kerberos.exceptions import KerberosExchangeError
        import subprocess

        try:
            kinit_call = subprocess.check_output(kinit_command, shell=True, stderr=subprocess.STDOUT)
            if kinit_call == '':
                print("SUCCESS >> Kinit call has been successful!")

        except subprocess.CalledProcessError:
            print("Looks like the kinit call has gone side ways!")
            exit(99)

        except KerberosExchangeError:
            print("Encountered difficulty getting authenticated using Kerberos, it may not be yet configured on this "
                  "server, run the 'setup_kerberos_config', then 'setup_kerberos_keytab' functions as remediation steps.")

    def decide_winrm_link(self):
        # if server is IP use different link than with server-name

        if self.server[:2].isdigit():
            winrm_link = "http://{}:5985/wsman".format(self.server)
        else:
            winrm_link = "http://{}.concurasp.com:5985/wsman".format(self.server)

        return winrm_link

    @staticmethod
    def fill_queue(data, queue):
        print("adding data: {} into Queue".format(data))
        queue.put(data)

    @staticmethod
    def get_all_from_queue_one_at_time(queue):
        while not queue.empty():
            yield queue.get()

    def call_winrm_powershell(self, command):
        from requests import exceptions
        import winrm

        # Get correct link for winrm
        winrm_link = self.decide_winrm_link()

        try:
            win_session = winrm.Session(winrm_link, auth=(None, None), transport='kerberos')
            raw_response = win_session.run_ps(command)
            output = raw_response.std_out
            error = raw_response.std_err

            if raw_response.status_code == 1:
                return False, error

            else:
                return True, output

        except exceptions.ConnectionError:
            print("Server: {}, refused connection, most likely the server is not yet fully up after reboot.".format(self.server))
        except winrm.exceptions.WinRMTransportError:
            print("Server: {}, side winrm encountered error.".format(self.server))

    @staticmethod
    def sleep_after_reboot(seconds):
        import time
        time.sleep(seconds)

    def reboot_windows(self, reboot_message=None):
        if reboot_message is None:
            reboot_message = "Remote triggered reboot from SM Automation Tool as part of Puppet Apply routine"

        reboot_cmd = 'shutdown /r /t 0 /c "' + reboot_message + '" /d P:4:1'

        print("Server: {}, initiating reboot.".format(self.server))
        success, output = self.call_winrm_powershell(reboot_cmd)

        return success, output

    def verify_rebooted(self):
        win_verify_rebooted_cmd = """\
        Function Get-Uptime {
        $os = Get-WmiObject win32_operatingsystem -ErrorAction SilentlyContinue
        $uptime = (Get-Date) - $os.ConvertToDateTime($os.LastBootUpTime)
        Write-Output ("" + $uptime.Days + " Days " + $uptime.Hours + " Hours " + $uptime.Minutes + " Minutes " )
        }
        Get-Uptime"""

        success, raw_uptime = self.call_winrm_powershell(win_verify_rebooted_cmd)

        if success is True:
            uptime = raw_uptime.split(" ")

            if int(uptime[0]) == 0 and int(uptime[2]) == 0 and int(uptime[4]) <= 5:
                print("Server: {} has been successfully rebooted, its uptime is: {}".format(self.server, raw_uptime))
                return True

            elif int(uptime[0]) > 0 or int(uptime[2]) > 0 or int(uptime[4]) > 5:
                print("Server: {} seems to have FAILED Rebooting, its uptime is : {}".format(self.server, raw_uptime))
                return False
            else:
                print("Server: {}, Something's gone wrong, cannot read from output of uptime! Output is: {}".format(self.server, raw_uptime))
                # response = "Failed to reboot, uptime grater than 5min >> uptime {}".format(raw_uptime)
                return False

    def recycle_iis(self):
        # Available from IIS7
        # shutdownTimeLimit = default 90s

        iis_recycle = """\
        Import-Module WebAdministration
        $AppPool = Get-ChildItem -Path IIS:\AppPools
        ForEach ($Pool in $AppPool.Name) {Write-Output "Recycling AppPool: $Pool"; Restart-WebAppPool $Pool}"""

        print("Server: {}, initiating IIS Recycle.\n".format(self.server))
        success, output = self.call_winrm_powershell(iis_recycle)

        return success, output

    def stop_start_restart_service(self, service, action="restart"):

        if action == "stop":
            service_cmd = "Stop-Service " + service
        elif action == "start":
            service_cmd = "Start-Service " + service
        else:
            service_cmd = "Restart-Service " + service

        print("Server: {}, initiating action: {} {}.\n".format(self.server, service, action))
        success, output = self.call_winrm_powershell(service_cmd)

        return success, output


def verify_ui_web_healthcheck(server=None, ip=None):
    import requests

    print("Verifying:\n\tASP-http-lifecheck-1.1")
    if server:
        api_link = "http://" + server + ".concurasp.com/lifechkstatus.asp?nodb=1"

    else:
        api_link = "http://" + ip + "/lifechkstatus.asp?nodb=1"

    print("\tHealthcheck of {}".format(server if server else ip))
    print("\tLink: {}.".format(api_link))

    # link prepared for lifechkstatusv2:
    # api_link = "http://" + server + "/api/home/lifechkstatusv2"

    try:
        response = requests.get(api_link)

        if "status: OK" in response.text:
            print("Life-Health-Check passed, all OK! Full response: {}".format(response.text))
            return True
        else:
            print("Server API seems running, but healtcheck did NOT return OK, it returned: \n{}".format(response.text))
            return False

    except requests.ConnectionError:
        print("Server API is down, seems Puppet was not applied correctly or something fundamental is missing!")
        return False
