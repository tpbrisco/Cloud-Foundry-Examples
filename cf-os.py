#!/usr/bin/python
#
# This is demonstration code for using Python as a client for the
# CF environment.
#
# It lists applications running in the cloud foundry environment, and
# then prints out the route mappings associated with each.
#
# This leverages existing CF credentials (if they exist) and attempts
# to refresh the credentials.  If that fails, it reverts to requesting
# username/password for the CF environment.
#
# It's not bug-free, and could probably be improved - but it should
# get anyone started.
#
# inspiration / borrowed from
# http://stackoverflow.com/questions/34717166/how-to-list-all-apps-in-cloudfoundry-using-python

import os
import sys
import getpass
import requests
import json

should_verify = False
if not should_verify:
    import urllib3
    urllib3.disable_warnings()


# attempt a login; get username/password
def cf_login(config):
    username = input('username: ')
    password = getpass.getpass('password: ')
    oauth_r = requests.post(
        config['AuthorizationEndpoint'] + "/oauth/token",
        data={
            'username': username,
            'password': password,
            'grant_type': 'password',
            'client_id': 'cf'},
        auth=('cf', ''),
        verify=should_verify)
    if not oauth_r.ok:
        print("Error in authentication: ", oauth_r.json()['error_description'])
        return {}
    return oauth_r.json()


# attempt to refresh an existing token - expect "refresh token"
def cf_refresh(config):
    oauth_r = requests.post(
        config['AuthorizationEndpoint'] + "/oauth/token",
        data={
            'refresh_token':  config['RefreshToken'],
            'grant_type': 'refresh_token',
            'client_id': 'cf'},
        auth=('cf', ''),
        verify=should_verify)
    if not oauth_r.ok:
        print("Error in token refresh:", oauth_r.json()['error_description'])
        return {}
    return oauth_r.json()


# initialize to "no access key"
access_key = ''

# try to refresh any existing credentials
config_file = os.getenv('CF_HOME')
if len(config_file) == 0:
    config_file = os.getenv('HOME')
config_file = config_file + "/.cf/config.json"
with open(config_file, "r") as f:
    config = json.load(f)

refresh_json = cf_refresh(config)
# print json.dumps(config, indent=2)
if len(refresh_json):
    access_key = "{} {}".format(
        refresh_json['token_type'],
        refresh_json['access_token'])
else:
    print("Credentials refresh failed")

# if a refresh was unsuccessful, revert to username/password
if access_key == '':
    # use new credentials from scratch
    login_json = cf_login(config)
    if len(login_json):
        access_key = "{} {}".format(
            login_json['token_type'],
            login_json['access_token'])
    else:
        print("Login failed")

if access_key == '':
    print("All access methods failed.  Cannot connect")
    sys.exit(2)
else:
    print("Authorization permitted, getting list of apps")

# get list of applications
apps_r = requests.get(
    config['Target'] + "/v2/apps",
    headers={'Accept': 'application/json',
             'Content-Type': 'application/json',
             'Request-Type': 'application/json',
             'Authorization': access_key},
    verify=should_verify)
print(json.dumps(apps_r.json(), indent=2))

# get their routes
resources = apps_r.json()['resources']
for r in resources:
    route = r['entity']['route_mappings_url']
    print("Entity Route", route)
    r = requests.get(
        config['Target'] + route,
        headers={'client_id': 'cf',
                 'Authorization': access_key,
                 'Request-Type': 'application/json',
                 'Content-Type': 'application/json'},
        verify=should_verify)
    if r.ok:
        print(json.dumps(r.json(), indent=2))
    else:
        print("Error:", r.text)
