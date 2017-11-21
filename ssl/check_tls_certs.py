#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ssl, socket
import pprint
import argparse
from datetime import datetime

URLS_TO_CHECK = []

# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('-d', action="store_true", default=False, dest="discover", help="Zabbix discover mode.")
parser.add_argument('-u', action="store", default="", dest="url", help="URL of cert to check")
args = parser.parse_args()

def loadURLList():
  global URLS_TO_CHECK

  for line in open("/usr/lib/zabbix/externalscripts/certlist.txt"):
    URLS_TO_CHECK.append(line.strip())


def discover():
  output = ""
  chunks = []

  for line in open("/usr/lib/zabbix/externalscripts/certlist.txt"):
    chunks.append("{\"{#CERTURL}\": \"%s\"}" % line.strip() )

  print "{\"data\": [" + ','.join(chunks) + "]}"


def checkCertURL():
  global URLS_TO_CHECK

  loadURLList()

  ctx = ssl.create_default_context()
  s = ctx.wrap_socket(socket.socket(), server_hostname=args.url)
  s.connect((args.url, 443))
  cert = s.getpeercert()

  expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y GMT")
  expire_in = expire_date - datetime.now()
  print expire_in.days


def main():
  if args.discover:
    discover()
  else:
    checkCertURL()

# Start program
if __name__ == "__main__":
    main()