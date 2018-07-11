# Dependencies:
#   yum install -y krb5-workstation


def gather_parameters(user=None, password=None, realm=None, path_to_keytab=None, force=False):
    import os

    user = os.getenv("krb_user")
    if user is None:
        try:
            user = input("Please input, Kerberos user: (default: default_sa_jenkins)")
        except SyntaxError:
            user = 'default_jenkins'

    password = os.getenv("krb_password")
    if password is None:
        password = input("Please input, Kerberos password: ")

    realm = os.getenv("krb_realm")
    if realm is None:
        try:
            realm = input("Please input, Kerberos realm: (default: <REPLACE>.COM)")
        except SyntaxError:
            realm = '<REPLACE>.COM'

    path_to_keytab = os.getenv("path_to_keytab")
    if path_to_keytab is None:
        try:
            path_to_keytab = input("Please input, path to keytab: (default: ~/.keytab/)")
        except SyntaxError:
            path_to_keytab = None

    force = os.getenv("force")
    if force.lower() == 'true':
        force = True
    elif force is None:
        try:
            force = input("Please input, force re-write if keytab already created: (default: False)")
        except SyntaxError:
            pass
    else:
        force = False

    return user, password, realm, path_to_keytab, force


# I. Initial Setup of Kerberos Configuration on HOST SERVER
#       THIS PART MUST BE RUN UNDER SUDO!
def setup_kerberos_config(path=None, realm=None):

    # Setup /etc/krb5.conf for our realm
    print("NOTE: krb5.conf is owned by root, you must run this under root or sudo.")

    if path is None:
        path = "/etc/krb5.conf"
        print("No path override argument given, setting up default kerb path for CentOS: {}".format(path))

    if realm is None:
        realm = "<REPLACE>.COM"
        print("No realm override argument given, setting up default realm: {}".format(realm))

    kerberos_config = """\
    [logging]
     default = FILE:/var/log/krb5libs.log
     kdc = FILE:/var/log/krb5kdc.log
     admin_server = FILE:/var/log/kadmind.log

    [libdefaults]
     default_realm = """ + realm + """
     dns_lookup_realm = true
     dns_lookup_kdc = true
     ticket_lifetime = 24h
     renew_lifetime = 7d
     forwardable = true"""

    with open(path, "w") as f:
        f.write(kerberos_config)

    print("SUCCESS >> Setting up /etc/krb5.conf with the following values: \n {}".format(kerberos_config))

    return


# II. Initial Setup of Kerberos Keytab for specific user/sa account
def setup_kerberos_keytab(password=None, user=None, realm=None, path=None, force=False):
    import os
    import subprocess

    if password is None:
        password = os.getenv('krb_pwd')

    if user is None:
        user = "default_sa_jenkins"
        print("No user override argument given, setting up default user: {}".format(user))

    if realm is None:
        realm = "<REPLACE>.COM"
        print("No realm override argument given, setting up default kerb realm: {}".format(realm))

    if path is None:
        path = os.getenv("HOME") + '/.keytab/'

    if os.path.isdir(path):
        print("{} Directory already exists, no need to create it.".format(path))
    else:
        print("{} Directory does not yet exist, creating...".format(path))
        os.makedirs(path)

    print("Verifying if user keytab file already exists:")
    if os.path.isfile(path + user + '.keytab'):
        if force is True:
            pass
        else:
            print("File already exist, exitting")
            return

    print("User keytab either doesnt exist or override is set to true, creating...")

    keytab_details = "addent -password -p " + user + "@" + realm + " -k 1 -e RC4-HMAC\n" + password + "\nwkt " + \
                     path + user + ".keytab\nq"

    cmd = 'echo -e """' + keytab_details + '""" | ktutil'
    print(cmd)

    # Setup keytab for automatic auth against Kerberos
    try:
        create_keytab = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print("Initial callout to create keytab for {}".format(user))
        print("Keytab ended with this result: {}".format(create_keytab))

    except subprocess.CalledProcessError:
        print("Looks like the keytab creation has gone side ways!")

    print("SUCCESS >> Setting up Kerberos keytab for auto authentication!")

    return


# III. ALWAYS TO BE RUN - Get Kerberos ticket
def kinit_krb_tkt(user=None, realm=None, path_to_keytab=None):
    import os
    import subprocess

    # Request ticket from Kerberos
    if user is None:
        user = "default_sa_jenkins"
        print("No user override argument given, setting up default user: {}".format(user))

    if realm is None:
        realm = "<REPLACE>.COM"
        print("No realm override argument given, setting up default kerb realm: {}".format(realm))

    if path_to_keytab is None:
        path_to_keytab = os.getenv("HOME") + '/.keytab/' + user + ".keytab"
        print("No 'path to keytab' override argument given, looking for {} in current directory".format(path_to_keytab))

    cmd = "kinit " + user + "@" + realm + " -k -t " + path_to_keytab

    try:
        print("Initiating kinit call for user: {}".format(user))
        kinit_call = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        if kinit_call == '':
            print("SUCCESS >> Kinit call has been successful!")

    except subprocess.CalledProcessError:
        print("Looks like the kinit call has gone side ways!")

    return


if __name__ == '__main__':

    print("""
    Please use python3 for this script
    Programatic use: export the following env. vars.:
        krb_user
        krb_password
        krb_realm
        path_to_keytab
        force
    """)

    gather_parameters()
    setup_kerberos_config()
    setup_kerberos_keytab()
    kinit_krb_tkt()
