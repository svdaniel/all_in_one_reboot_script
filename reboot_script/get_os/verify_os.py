# IV. VERIFYING OS BY IP/NODE
# ----------------------------


def api_call(api_link, auth):
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    header = {'Content-Type': 'application/json'}
    answered = requests.get(api_link, auth=auth, headers=header, verify=False)
    return_code = answered.status_code

    if return_code == 200:
        return return_code, answered.json()
    else:
        return return_code, answered.text()


def get_os_type(username, password, ip=None, server_name=None):

    api_link = 'https://<REPLACE>.com/api/v1/server/ip/' + ip

    auth = (username, password)
    return_code, raw_output = api_call(api_link, auth=auth)
    print(api_link)
    print(raw_output)

    if return_code == 200:
        os = str(raw_output['data'][0]['os']).lower()
        print("Server: {}: is OS: {}.\n".format(server_name if server_name else ip, os))
        return os
    else:
        print("Server: {}: ERROR: for OS returned: {}.\n".format(server_name, raw_output))
        return raw_output
