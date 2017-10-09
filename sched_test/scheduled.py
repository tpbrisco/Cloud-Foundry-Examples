# /usr/bin/env python
#
# "scheduled" - sample/simple systems statistics for system availability.
# This sample sets up a very basic framework, and has a scheduled task
# that performs some statistics gathering.
#
# A sample 'run_test' is available that really does nothing but average the current time.
# A "test_login" performs a system login and gathers statistics about it

import time, os, sys
import atexit
# flask for REST API components
from flask import Flask
from flask_restful import Resource, Api
# schedule background tasks
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
# call REST/json API functions
import requests, json

# set up application and api
app = Flask(__name__)
api = Api(app)

# keep a global running statistics of what we've performed
# retain about the last 100 entries
stats = []         # track about last hundred entries
lastval = ''       # last value returned from the test
lastmsg = ''     # last message returned
interval = 30	# how often to call the routine
# for the tests, we need a username and password
username = ''
password = ''

# return a simple message if someone naively calls our "/" api
class TestRunner(Resource):
    def get(self):
        return {'message': 'use /stats for statistics, or /help for this message again'}

# return information about the statistics runner
class StatsRunner(Resource):
    def get(self):
        #
        global interval
        # calcuate last windows
        sum10 = 0
        sum50 = 0
        sum100 = 0
        max10 = min(len(stats), 10)
        max50 = min(len(stats), 50)
        max100 = min(len(stats), 100)
        # debug
        print "len:%d max10:%d max50:%d max100:%d" % (len(stats), max10, max50, max100)
        # protect against divide-by-0
        if len(stats) == 0:
            return ({'interval': 0, 'samples': 0, 'last_value': 0, 'last_message': 'starting',
                     'avg10': 0, 'avg50': 0, 'avg100': 0})
        # calcuate stats
        avg10 = sum(stats[0:9])/max10
        avg50 = sum(stats[0:49])/max50
        avg100 = sum(stats[0:99])/max100
        return ({'interval': interval,
                 'samples': len(stats),
                 'last_value': lastval,
                 'last_message': lastmsg,
                 'minimum': min(stats[0:max100]),
                 'maximum': max(stats[0:max100]),
                 'avg10': avg10,
                 'avg50': avg50,
                 'avg100': avg100})

# dummy "test" routine - this simply returns averages of the current time
def run_test():
    global stats
    global lastval
    global lastmsg
    print "test"
    stats.insert(0, time.time())
    lastval = stats[0]
    del stats[100:]
    lastmsg = "timenow: %s statsize: %d" % (time.time(), len(stats))
    print lastmsg

# test login times
# Using the username/password (global variables) time a oauth call to the UAA.
# Timeout the connection is more than 'interval/2' seconds have elapsed.
# Errors are recorded as a "-1", and the "lastmsg" is set to the error message
# Otherwise, return the average of the last 10, 50 and 100 calls, including the
# max and min values, and how many samples have been taken (to determine
# the validity of the 10/50/100 averages).
def test_login():
    global stats
    global lastval
    global lastmsg
    global interval
    #
    start = time.time()
    # otr is the oauthTokenResponse, watch for timeouts
    try:
        otr = requests.post(
            'https://login.run.pivotal.io/oauth/token?grant_type=password&client_id=cf',
            timeout=int(interval/2),
            data = {
                'username': username,
                'password': password,
                'client_id': 'cf'},
            auth=('cf', ''))
    except requests.exceptions.ConnectionError as e:
        lastmsg = 'Error connection timed out'
        print lastmsg
        stats.insert(0, -1)
        lastval = stats[0]
        del stats[100:]
    end = time.time()
    # request - successful or not - done
    if not otr.ok:
        lastmsg = 'Error in login: ', otr.json()['error_description']
        print lastmsg
    else:
        lastmsg = 'Return code %d, bytes %d' % (otr.status_code, len(otr.text))
    # update statistics - insert new value, set last value, and truncate data to 100
    stats.insert(0, end - start)
    lastval = stats[0]
    del stats[100:]
    print "timenow: %s last: %s" % (start, end-start)

# set up main routines
api.add_resource(TestRunner, '/', '/help')   # return useful info on naive queries
api.add_resource(StatsRunner, '/stats')     # actually return data

# get username, password for tests
username = os.getenv('username')
password = os.getenv('password')
if username == '' or password == '':
    print "Need to set environment variables for username and password"
    sys.exit(1)

app.debug = False

if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=test_login,
        trigger=IntervalTrigger(seconds=interval),
        id='running_test',
        name='As a test, print the time every 5 seconds',
        replace_existing=True)

# when we terminate, kill of the scheduler threads 
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    port = os.getenv("PORT", default=5000)
    app.run(host='0.0.0.0', port=port)

