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


# attempt a login; get username/password
def cf_login():
    username = raw_input('username:')
    password = getpass.getpass('password:')
    oauthTokenResponse = requests.post(
        'https://login.run.pivotal.io/oauth/token?grant_type=password&client_id=cf',
        data={'username': username,
              'password': password,
              'client_id': 'cf'},
        auth=('cf', ''))
    if not oauthTokenResponse.ok:
        print "Error in authentication: ", oauthTokenResponse.json()['error_description']
        return {}
    return oauthTokenResponse.json()


# attempt to refresh an existing token - expect "refresh token"
def cf_refresh(r_token):
    oauthTokenResponse = requests.post(
        'https://login.run.pivotal.io/oauth/token?grant_type=refresh_token&client_id=cf',
        data={'refresh_token':  r_token, 'client_id': 'cf'},
        auth=('cf', ''))
    if not oauthTokenResponse.ok:
        print "Error in token refresh:", oauthTokenResponse.json()['error_description']
        return {}
    return oauthTokenResponse.json()


# initialize to "no access key"
access_key = ''

# try to refresh any existing credentials
if os.path.isfile(os.path.expanduser("~/.cf/config.json")):
    # use existing cached credentials
    with open(os.path.expanduser("~/.cf/config.json"), "r") as f:
        current_login = json.load(f)
    refresh_json = cf_refresh(current_login['RefreshToken'])
    # print json.dumps(current_login, indent=2)
    if len(refresh_json):
        access_key = refresh_json['token_type'] + ' ' + refresh_json['access_token']
    else:
        print "Credentials refresh failed"

# if a refresh was unsuccessful, revert to username/password
if access_key == '':
    # use new credentials from scratch
    login_json = cf_login()
    if len(login_json):
        access_key = login_json['token_type'] + ' ' + login_json['access_token']
    else:
        print "Login failed"

if access_key == '':
    print "All access methods failed.  Cannot connect"
    sys.exit(2)
else:
    print "Authorization permitted, getting list of apps"

appsResponse = requests.get('https://api.run.pivotal.io/v2/apps',
                            headers={'Accept': 'application/json',
                                     'Content-Type': 'application/json',
                                     'Authorization': access_key}
                            )
print json.dumps(appsResponse.json(), indent=2)

#
resources = appsResponse.json()['resources']
for r in resources:
    route = r['entity']['route_mappings_url']
    print "Entity Route", route
    r = requests.get('http://api.run.pivotal.io' + route,
                     headers={'client_id': 'cf', 'Authorization': access_key})
    if r.ok:
        print json.dumps(r.json(), indent=2)
    else:
        print "Error:", r.text
