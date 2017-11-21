#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import ConfigParser
import json
import urllib3
import pprint
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#######################################################################################
#
# Retrieves status from Jenkins
#
#######################################################################################
POOL = None
HEADERS = None
HOST = None
JOBS = {}

# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('-q', action="store_true", default=False, dest="queue", help="Get number of builds waiting in queue")
parser.add_argument('-r', action="store_true", default=False, dest="numrunning", help="Get number of running builds")
parser.add_argument('-s', action="store_true", default=False, dest="slow", help="Check for slow/stuck jobs")
args = parser.parse_args()

def loadCredentials():
  global HEADERS, HOST
  
  try:
    configParser = ConfigParser.RawConfigParser()  
    configParser.read("jenkinsconfig.ini")
    TOKEN = configParser.get('base','token')
    USER = configParser.get('base','user')
    HOST = configParser.get('base','host')
    HEADERS = urllib3.util.make_headers(basic_auth="%s:%s" % (USER,TOKEN))
  except Exception, e:
    print "ERROR: %s" % e.message
    sys.exit(1)

def initialConnect():
  global POOL

  POOL = urllib3.PoolManager()


def doRequest(uri):
  global HEADERS, POOL, HOST

  result = None

  try:
    result = POOL.request('GET', '%s/%s' % (HOST,uri), headers=HEADERS)

    if result.status != 200:
      print "Failed to request data from Jenkins! %s" % result.data
    else:
      return result
  except Exception, e:
    print "ERROR: %s" % e.message
    sys.exit(1)


def getRunningJobs():
  global JOBS

  #get base list
  result = json.loads(doRequest('api/json?tree=jobs[name,url,buildable,lastBuild[number,building,timestamp,duration,estimatedDuration],jobs[name,fullName,buildable,lastBuild[number,timestamp,building,duration,estimatedDuration,timestamp]]]').data)
  
  for job in result['jobs']:
    if "WorkflowMultiBranchProject" not in job['_class']:
      if job['buildable'] == True and job['lastBuild'] != None:
        JOBS[job['name']] = {"Building": job['lastBuild']['building'], "Duration": job['lastBuild']['duration'], "EstimatedDuration": job['lastBuild']['estimatedDuration']}
    else:
      for subjob in job['jobs']:
        if subjob['buildable'] == True and subjob['lastBuild'] != None:
          JOBS[subjob['fullName']] = {"Building": subjob['lastBuild']['building'], "Duration": subjob['lastBuild']['duration'], "EstimatedDuration": subjob['lastBuild']['estimatedDuration']}


def getCountOfRunningJobs():
  global JOBS
  
  x = 0
  for name,job in JOBS.iteritems():
    if job['Building']:
      x = x + 1
  
  print x


def getSlowJobs():
  global JOBS

  for name,job in JOBS.iteritems():
    if job['Duration'] > (2 * job['EstimatedDuration']) and job['Building']:
      print "%s: Too long" % name
      print "Est: %s, Duration: %s" % (job['EstimatedDuration'],job['Duration'])


def getCountOfSlowJobs():
  global JOBS
  
  x = 0  
  for name,job in JOBS.iteritems():
    if job['Duration'] > (2 * job['EstimatedDuration']) and job['Building']:
      x = x + 1
  
  print x


def getQueueLength():
  result = json.loads(doRequest('queue/api/json').data)
  print len(result['items'])


def main():
  loadCredentials()
  initialConnect()
  
  if args.queue:
    getQueueLength()
  elif args.numrunning:
    getRunningJobs()
    getCountOfRunningJobs()
  elif args.slow:
    getRunningJobs()
    getCountIdSlowJobs()



# Start program
if __name__ == "__main__":
    main()