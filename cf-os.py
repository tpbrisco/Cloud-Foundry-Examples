#!/usr/bin/python
#
# stolen from
# http://stackoverflow.com/questions/34717166/how-to-list-all-apps-in-cloudfoundry-using-python

import os, sys
import getpass
import requests
import json

current_login = {}

if os.path.isfile(os.path.expanduser("~/.cf/config.json")):
    # use existing cached credentials
    with open(os.path.expanduser("~/.cf/config.json"), "r") as f:
        current_login = json.load(f)
    authorization = current_login['AccessToken']
    # refresh the token
    oauthTokenResponse = requests.post(
        'https://login.run.pivotal.io/oauth/token?grant_type=refresh_token&client_id=cf',
        data={'refresh_token':  current_login['RefreshToken'],
              'client_id': 'cf',
              'Authorization': authorization},
        auth=('cf', ''))
    if not oauthTokenResponse.ok:
        print "Error in token refresh:", oauthTokenResponse.text
        sys.exit(1)

    authorization = oauthTokenResponse.json()['token_type'] + ' ' + oauthTokenResponse.json()['access_token']
    print "refreshed auth:\"" + authorization + "\""
else:
    # use new credentials
    username = raw_input('username:')
    password = getpass.getpass('password:')

    oauthTokenResponse = requests.post(
        'https://login.run.pivotal.io/oauth/token?grant_type=password&client_id=cf',
        data={'username': username,
              'password': password,
              'client_id': 'cf'},
        auth=('cf',''))
    if not oauthTokenResponse.ok:
        print "Error in authentication: ",oauthTokenResponse.text
        sys.exit(1)
    
    authorization = oauthTokenResponse.json()['token_type'] + ' ' + oauthTokenResponse.json()['access_token']
    print "authorization:\"" + authorization + "\""

appsResponse = requests.get('https://api.run.pivotal.io/v2/apps',
                            headers={'Accept': 'application/json', 'Content-Type': 'application/json',
                                     'Authorization': authorization}
                            )
# print oauthTokenResponse.json()['token_type'], oauthTokenResponse.json()['access_token']
print json.dumps(appsResponse.json(), indent=2, separators={',',':'})
