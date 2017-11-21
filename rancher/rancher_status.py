#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import sys
import os
import io
import pprint
import argparse
import ConfigParser
from requests.packages.urllib3.exceptions import InsecureRequestWarning 

# GLOBALS, m'kay?
BASE_URL = None
KEY = None
SECRET = None
STACKS = {}
ENVS = {}

# silly self-signed certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('-o', action="store", dest="operation", default="discover", choices=['discover', 'status'], help="What operation to perform")
parser.add_argument('-i', action="store", dest="item", nargs="?", help="Which service to check status. Use rancher id, not name")
args = parser.parse_args()


def loadCredentials():
  global BASE_URL, KEY, SECRET, TARGET_ENV
  
  configParser = ConfigParser.RawConfigParser()  
  configParser.read("config.ini")
  BASE_URL = configParser.get('base','url')
  KEY = configParser.get('base','key')
  SECRET = configParser.get('base','secret')
  TARGET_ENV = configParser.get('base','envs')


def makeGetCall(endpoint):
  global BASE_URL, KEY, SECRET

  headers = {'Content-Type': 'application/json'}
  r = requests.get(BASE_URL + endpoint, verify=False, auth=(KEY, SECRET), headers=headers)
  
  if (r.ok):
    resp = json.loads(r.content)
    return resp
  else:
    # print BASE_URL + endpoint
    pprint.pprint(r)
    print "ERROR!"


def discoverServices():
  global STACKS, ENVS, TARGET_ENV

  output = ""
  chunks = []

  resp = getAllServices()

  for svc in resp['data']:  
    if svc['accountId'] in TARGET_ENV:
      chunk = "{\"{#SERVICENAME}\": \"%s\",\"{#SERVICEID}\": \"%s\",\"{#STACKNAME}\": \"%s\",\"{#ENVNAME}\": \"%s\",\"{#ENVID}\": \"%s\"}" % (svc['name'], svc['id'], STACKS[svc['stackId']], ENVS[svc['accountId']],svc['accountId'])
      chunks.append(chunk)

  print "{\"data\": [" + ','.join(chunks) + "]}"


def buildStackLookup():
  global STACKS

  endpoint = "/stacks"
  resp = makeGetCall(endpoint)
  for stk in resp['data']:
    STACKS[stk['id']] = stk['name']


def buildEnvLookup():
  global ENVS

  endpoint = "/projects"
  resp = makeGetCall(endpoint)
  for env in resp['data']:
    ENVS[env['id']] = env['name']


def getAllServices():
  endpoint = "/services?limit=1000"
  resp = makeGetCall(endpoint)
  return resp


def getServiceStatus(serviceId):
  endpoint = "/services/%s" % serviceId
  resp = makeGetCall(endpoint)

  if resp['healthState'] != 'healthy':
    print "0"
  else:
    print "1"
 

def main():
  # do some setup
  loadCredentials()
  buildStackLookup()
  buildEnvLookup()

  # switch to operation
  if args.operation == "discover":
    discoverServices()
  elif args.operation == "status":
    getServiceStatus(args.item)
  else:
    print "Not a valid operation!"


# Start program
if __name__ == "__main__":
    main()