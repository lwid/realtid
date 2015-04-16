import os
import time
import json
import urllib2
import unicodedata
import serial
import ConfigParser
import badge

config = ConfigParser.ConfigParser()
config.read('config')

# Data source, including the secret API key
a=config.get('SL', 'Url')
b=config.get('SL', 'Key')
c=config.getint('SL', 'siteid')
d=config.getint('SL', 'TimeWindow')
url = "%s?key=%s&siteid=%s&TimeWindow=%s" % (a,b,c,d)

# Serial device for the display
dev = config.get('DISPLAY','SerialPort')
speed = config.get('DISPLAY','SerialSpeed')
ser = serial.Serial(dev, speed)

# Fetch data from SL
data = json.load(urllib2.urlopen(url))

# Concat the scrolling message
msg=""
for train in data['ResponseData']['Trains']:
#  for (k, v) in train.items():
#    print k, v
  print "%s, %s (%s)" % (train['Destination'], train['DisplayTime'], train['Deviations'])
  msg+= "%s, %s (%s) " % (train['Destination'], train['DisplayTime'], train['Deviations'])

# Normalize the unicode into plain ASCII
msg=unicodedata.normalize('NFKD', msg).encode('ascii','ignore')

# Pipe the message to the display device
pkts = badge.build_packets(0x600, badge.message_file(msg, speed='5', action=badge.ACTION_ROTATE))
for p in pkts:
    ser.write(p.format())
#f.flush()
ser.close()

