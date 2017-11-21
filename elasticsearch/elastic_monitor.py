#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import ConfigParser
import json
import urllib3
import pprint

#######################################################################################
#
# Retrieves and parses values via the Elasticsearch API
#
#######################################################################################
POOL = None
HEADERS = None
HOST = None

# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('-dn', action="store_true", default=False, dest="discovernodes", help="Discover cluster nodes")
parser.add_argument('-di', action="store_true", default=False, dest="discoverindices", help="Discover cluster indices")
parser.add_argument('field', nargs='?', help="Field to check")
parser.add_argument('id', nargs='?', help="Id of item to check (e.g. node id or index name)")
args = parser.parse_args()

def loadCredentials():
  global USER, PASS, HEADERS, HOST
  
  try:
    configParser = ConfigParser.RawConfigParser()  
    configParser.read("esconfig.ini")
    USER = configParser.get('base','user')
    PASS = configParser.get('base','pass')
    HOST = configParser.get('base','host')
    HEADERS = urllib3.util.make_headers(basic_auth="%s:%s" % (USER,PASS))
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
    result = POOL.request('GET', 'http://%s/%s' % (HOST,uri), headers=HEADERS)

    if result.status != 200:
      print "Failed to request data from ES! %s" % result.data
    else:
      return result
  except Exception, e:
    print "ERROR: %s" % e.message
    sys.exit(1)


def discovernodes():
  output = ""
  chunks = []
  
  result = json.loads(doRequest('_nodes').data)

  for k,v in result['nodes'].iteritems():
    chunks.append("{\"{#NODENAME}\": \"%s\", \"{#NODEID}\": \"%s\"}" % (v['name'], k))

  print "{\"data\": [" + ','.join(chunks) + "]}"


def discoverindices():
  output = ""
  chunks = []
  
  result = json.loads(doRequest('_stats').data)

  for k,v in result['indices'].iteritems():
    if '.' not in k:
      chunks.append("{\"{#INDEXNAME}\": \"%s\", \"{#DOCCOUNT}\": \"%s\"}" % (k, v['primaries']['docs']['count']))

  print "{\"data\": [" + ','.join(chunks) + "]}"


def getValue():
  if args.field == "node_jvm_heap":
    result = json.loads(doRequest('_nodes/%s/stats/jvm' % args.id).data)
    print result['nodes'][args.id]['jvm']['mem']['heap_used_percent']
  elif args.field == "node_jvm_threads":
    result = json.loads(doRequest('_nodes/%s/stats/jvm' % args.id).data)
    print result['nodes'][args.id]['jvm']['threads']['count']
  elif args.field == "node_total_virtual":
    result = json.loads(doRequest('_nodes/%s/stats/process' % args.id).data)
    print result['nodes'][args.id]['process']['mem']['total_virtual_in_bytes']
  elif args.field == "cluster_max_wait_time":
    result = json.loads(doRequest('_cluster/health').data)
    print result['task_max_waiting_in_queue_millis']
  elif args.field == "number_of_nodes":
    result = json.loads(doRequest('_cluster/health').data)
    print result['number_of_nodes']
  elif args.field == "index_doc_count":
    result = json.loads(doRequest('%s/_stats' % args.id).data)
    print result['indices'][args.id]['primaries']['docs']['count']
  elif args.field == "index_store_bytes":
    result = json.loads(doRequest('%s/_stats' % args.id).data)
    print result['indices'][args.id]['primaries']['store']['size_in_bytes']
  elif args.field == "cluster_health":
    result = json.loads(doRequest('_cluster/health').data)
    if result['status'] == "green":
      print "0"
    elif result['status'] == "yellow":
      print "1"
    else:
      print "2"
  else:
    print "ERROR! Unknown value requested: %s" % args.field

def main():
  loadCredentials()
  initialConnect()
  
  if args.discovernodes:
    discovernodes()
  elif args.discoverindices:
    discoverindices()
  else:
    getValue()

# Start program
if __name__ == "__main__":
    main()