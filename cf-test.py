#!/usr/bin/python
#
# stolen from
# http://stackoverflow.com/questions/34717166/how-to-list-all-apps-in-cloudfoundry-using-python

import os
import sys
import getpass
import requests
import json

username = raw_input('username:')
password = getpass.getpass('password:')
oauthTokenResponse = requests.post(
    'https://login.run.pivotal.io/oauth/token?grant_type=password&client_id=cf',
    data={'username': username,
          'password': password,
          'client_id': 'cf'},
    auth=('cf', ''))
print json.dumps(oauthTokenResponse.json(), indent=2, separators={',', ':'})
authorization = oauthTokenResponse.json()['token_type'] + \
    ' ' + oauthTokenResponse.json()['access_token']

appsResponse = requests.get('https://api.run.pivotal.io/v2/apps',
                            headers={'Accept': 'application/json',
                                     'Content-Type': 'application/json',
                                     'Authorization': authorization}
                            )
# print oauthTokenResponse.json()['token_type'], oauthTokenResponse.json()['access_token']
print json.dumps(appsResponse.json(), indent=2, separators={',', ':'})
