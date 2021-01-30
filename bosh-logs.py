#!/usr/bin/env python
#
# demonstration code for logging into the BOSH director API, leveraging the UAA
#
# Generally this is risky code, as https://bosh.io/docs/director-api-v1 API
# documents dont reference key points below.  The endpoint for initiating logs
# gathering is undocumented, as is the /resources endpoint.
#
# This fetchs logs -- similar to the "bosh logs" command
# 1: use BOSH URL to get the information endpoint (for auth, API endpoints)
# 2: use auth endpoint to get OAuth token
# 3: Use /deployments endpoint to submit log-gathering job, wait for completion
#     This gathers the logs, and drops them onto the blobstore
# 4: Use result GUID from above to download via the /resources endpoint
#      The director seems to proxy this to the blobstore API
#

import sys
import getpass
import requests
import json
import time
from optparse import OptionParser
from urllib.parse import urlparse

# determine whether certificates should be meaningful
should_verify = False
if not should_verify:
    import urllib3
    urllib3.disable_warnings()


# get BOSH endpoint information
def bosh_info(s, url):
    info = s.get(url + "/info", verify=should_verify)
    if not info.ok:
        print("Error getting info endpoint:", url)
        sys.exit(1)
    return info.json()


# OAuth login, and related tokens
def bosh_login(s, auth_url, username, password):
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
              oauthTokenResponse.json())
        return None
    return oauthTokenResponse.json()


parser = OptionParser()
parser.add_option('-D', '--debug', dest='debug', default=False,
                  action='store_true', help='debug information')
parser.add_option('-u', '--user', dest='username', default='',
                  help='director uaa user')
parser.add_option('-p', '--pass', dest='password', default='',
                  help='director uaa password')
parser.add_option('-b', '--bosh-url', dest='bosh_url', default='',
                  help='bosh director url (protocol and port included)')
parser.add_option('-d', '--deployment', dest='deployment', default='',
                  help='bosh deployment')
parser.add_option('-j', '--job', dest='bosh_job', default='',
                  help='bosh job identifier (full)')
(options, args) = parser.parse_args()

if not options.username:
    options.username = input('username:')
if not options.password:
    options.password = getpass.getpass('password:')
if options.bosh_url == '':
    parser.error('bosh url required')
if options.bosh_job == '':
    parser.error('bosh job required')
if options.deployment == '':
    parser.error('bosh deployment required')
if options.debug:
    print("user:", options.username)
    print("pass:", options.password)
    print("job :", options.bosh_job)
    print("auth:", options.bosh_url)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json',
                  'Accept': 'application/json'})

# get authorization endpoint
endpoints = bosh_info(s, options.bosh_url)
bosh_auth_url = endpoints['user_authentication']['options']['url']
bosh_api_url = options.bosh_url

oauth = bosh_login(s, bosh_auth_url, options.username, options.password)
if oauth is None:
    print("error")
    sys.exit(1)

headers = {'Authorization':
           oauth['token_type'] + ' ' + oauth['access_token']}
s.headers.update(headers)

# if options.debug:
# print("TOKEN=\"%s %s\"" % (oauth['token_type'], oauth['access_token']))

# call logs api endpoint; expect a 302 back
# See bosh-cli/director/deployment.go:L260, cmd/logs.go:L111
logs_url = "%s/deployments/%s/jobs/%s/logs" % (
    bosh_api_url, options.deployment, options.bosh_job)
if options.debug:
    print("logs_url:", logs_url)
# redirects to the URL without the port specified, catch this and fix
logs_resp = s.get(logs_url, params={'type': 'job'},
                  allow_redirects=False, verify=should_verify)
logs_task = ''
if logs_resp.status_code == 302:
    if options.debug:
        print("redirected to", logs_resp.headers['Location'])
    # get path component of redirect, so we can fix up the missing port #
    logs_task = urlparse(logs_resp.headers['Location']).path
    if options.debug:
        print("path", logs_task)
else:
    print("fail?", logs_resp.status_code)
    print("url:", logs_resp.url)
    print(logs_resp.content.decode('utf-8'))
    for h in logs_resp.history:
        print("\t", h.status_code, " ", h.url)
    sys.exit(1)

# job queued up in task indicated by logs_task -- fetch data
# wait for it to complete, and get the result
task_state = ''
try_count = 0
while task_state != 'done' and try_count < 10:
    logs_task_resp = s.get(bosh_api_url + logs_task,
                           verify=should_verify)
    task_state = logs_task_resp.json()['state']
    if task_state != 'done':
        try_count += 1
        time.sleep(1)
        print("wait for logs task ready(%ds)" % (try_count))
task_results = s.get(bosh_api_url + logs_task + "/output",
                     params={'type': 'result'},
                     verify=should_verify)
# task_results.json()['result'] is the blobstore ID of our file
print(task_results.status_code, ":",
      json.dumps(logs_task_resp.json(), indent=2))

# get the file from /resources/<result> URL formed from the return data above
# See bosh-cli cmd/downloader.go:L95, director/director.go:L92
download_url = "/resources/%s" % (logs_task_resp.json()['result'])
job_name = options.bosh_job.replace("/", "-")
output_name = "%s-%s-logs.tgz" % (
    options.deployment, job_name)
print("Downloading ", download_url, "as", output_name)
with open(output_name, 'wb') as f:
    r = s.get(bosh_api_url + download_url, verify=should_verify)
    for chunk in r.iter_content(chunk_size=512 * 1024):
        if chunk:
            f.write(chunk)
print("downloaded")
