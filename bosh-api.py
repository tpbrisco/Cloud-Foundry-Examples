#!/usr/bin/env python
#
# demonstration code for logging into the BOSH director API, leveraging the UAA
# print out the OAuth token for curl usage

import getpass
import sys
import requests
from optparse import OptionParser

should_verify = False
if not should_verify:
    import urllib3
    urllib3.disable_warnings()


def bosh_info(url):
    info = requests.get(url + "/info", verify=should_verify)
    if not info.ok:
        print("Error geting info endpoint:", url)
        sys.exit(1)
    return info.json()


def bosh_login(auth_url, username, password):
    oauthTokenResponse = requests.post(
        auth_url + "/oauth/token",
        data={'username': username,
              'password': password,
              'grant_type': 'password',
              'client_id': 'bosh_cli'},
        auth=('bosh_cli', ''),
        verify=should_verify)
    if not oauthTokenResponse.ok:
        print("Error in authentication:",
              oauthTokenResponse.json()['error_description'])
        sys.exit(1)
    return oauthTokenResponse.json()


parser = OptionParser()
parser.add_option('--user', dest='username', default='',
                  help='director uaa user')
parser.add_option('--pass', dest='password', default='',
                  help='director uaa password')
parser.add_option("--url", dest='bosh_url', default='',
                  help='bosh url (https://<ip>:25555)')
(options, args) = parser.parse_args()

if not options.username:
    options.username = input('username:')
if not options.password:
    options.password = getpass.getpass('password:')
if not options.bosh_url:
    print("need bosh url")
    sys.exit(1)

info = bosh_info(options.bosh_url)
oauth = bosh_login(info['user_authentication']['options']['url'],
                   options.username, options.password)
print("TOKEN=\"%s %s\"" % (oauth['token_type'], oauth['access_token']))
