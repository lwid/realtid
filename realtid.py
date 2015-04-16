import os
import time
import json
import urllib2
import unicodedata
import serial
import ConfigParser
import dateutil.parser
import badge

# Parse the config
config = ConfigParser.ConfigParser()
config.read('config')

#########################

# Setup, and open, the serial device for the display
dev = config.get('DISPLAY','SerialPort')
speed = config.get('DISPLAY','SerialSpeed')
ser = serial.Serial(dev, speed)

#########################

# Setup a list of departures which we can populate from
# multiple sources before sorting
deps=[]

# A list of information messages
msgs=[]


#########################

########################

# Setup data source for SL (TBD: Extract into a module once we have multiple sources)
a=config.get('SL', 'Url')
b=config.get('SL', 'Key')
c=config.getint('SL', 'siteid')
d=config.getint('SL', 'TimeWindow')
url = "%s?key=%s&siteid=%s&TimeWindow=%s" % (a,b,c,d)

# Fetch data from SL
data = json.load(urllib2.urlopen(url))

# Concat the scrolling message
for train in data['ResponseData']['Trains']:
  t=dateutil.parser.parse(train['DisplayTime'])
  deps.append([t, "SL"])

for dev in data['ResponseData']['StopPointDeviations']:
  msgs.append(dev['Deviation']['Text'])

###################################



url=config.get('SJ', 'Url')
key=config.get('SJ', 'Key')
loc=config.get('SJ', 'Loc')
dst=config.get('SJ', 'Dst')

xml='<REQUEST> <LOGIN authenticationkey="%s" /> <QUERY objecttype="TrainAnnouncement" orderby="AdvertisedTimeAtLocation"> <FILTER> <AND> <EQ name="ActivityType" value="Avgang" /> <EQ name="LocationSignature" value="%s" /> <EQ name="InformationOwner" value="SJ" /> <LIKE name="ToLocation" value="/%s/" /> <OR> <AND> <GT name="AdvertisedTimeAtLocation" value="$dateadd(-00:02:00)" /> <LT name="AdvertisedTimeAtLocation" value="$dateadd(01:30:00)" /> </AND> <AND> <LT name="AdvertisedTimeAtLocation" value="$dateadd(01:30:00)" /> <GT name="EstimatedTimeAtLocation" value="$dateadd(-00:02:00)" /> </AND> </OR> </AND> </FILTER> <INCLUDE>AdvertisedTrainIdent</INCLUDE> <INCLUDE>AdvertisedTimeAtLocation</INCLUDE> <INCLUDE>TrackAtLocation</INCLUDE> <INCLUDE>ToLocation</INCLUDE> </QUERY> </REQUEST>' % (key, loc, dst)

data = json.load(urllib2.urlopen(urllib2.Request(url=url, data=xml, headers={'Content-Type': 'text/xml'})))
for d in data['RESPONSE']['RESULT'][0]['TrainAnnouncement']:
  t=dateutil.parser.parse(d['AdvertisedTimeAtLocation'])
  deps.append([t, "SJ"])

#############################

#a=config.get('SL2', 'Url')
#b=config.get('SL2', 'Key')
#c=config.getint('SL2', 'siteid')
#d=config.get('SL2', 'TransportMode')
#e=config.getint('SL2', 'LineNumber')
#url = "%s?key=%s&siteid=%s&LineNumber=%s&TransportMode=%s" % (a,b,c,e,d)

# Fetch data from SL
#data = json.load(urllib2.urlopen(url))

# Concat the scrolling message
#for d in data['ResponseData']:
  #print d['Header']
  #msg+= d['Header']

#############################

# Build the message string
msg=""
for dep in sorted(deps, key=lambda d: d[0]):
  msg+="%s (%s) " % (dep[0].strftime("%H:%M"), dep[1])
for m in msgs:
  msg+=m

# Normalize the unicode into plain ASCII (the display /can/ handle Unicode, TBD...)
msg=unicodedata.normalize('NFKD', msg).encode('ascii','ignore')

# Pipe the message to the display device
pkts = badge.build_packets(0x600, badge.message_file(msg, speed='5', action=badge.ACTION_ROTATE))
for p in pkts:
    ser.write(p.format())
ser.close()

