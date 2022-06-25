#!/usr/bin/python
#
# stolen from
# http://stackoverflow.com/questions/34717166/how-to-list-all-apps-in-cloudfoundry-using-python

import getpass
import requests
import os
import sys
import json

should_verify = False
if not should_verify:
    import urllib3
    urllib3.disable_warnings()

url_base = os.getenv('URL_BASE')
if url_base is None or len(url_base) == 0:
    print('set URL_BASE to the domain base - e.g. "run.pivotal.io"')
    sys.exit(1)

username = input('username:')
password = getpass.getpass('password:')

auth_endpoint = 'https://login.{}/oauth/token'.format(url_base)
oauth_r = requests.post(
    auth_endpoint,
    data={'username': username,
          'password': password,
          'grant_type': 'password',
          'client_id': 'cf'},
    auth=('cf', ''),
    verify=should_verify)
print(json.dumps(oauth_r.json(), indent=2, separators={',', ':'}))
authorization = '{} {}'.format(
    oauth_r.json()['token_type'],
    oauth_r.json()['access_token'])

api_endpoint = 'https://api.{}'.format(url_base)
apps_r = requests.get(
    api_endpoint + '/v2/apps',
    headers={'Accept': 'application/json',
             'Content-Type': 'application/json',
             'Authorization': authorization},
    verify=should_verify)
# print oauth_r.json()['token_type'], oauth_r.json()['access_token']
print(json.dumps(apps_r.json(), indent=2, separators={',', ':'}))
