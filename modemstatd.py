#!/usr/bin/env python
 
import urllib2
from BeautifulSoup import BeautifulSoup
import sys, time
import rrdtool
import signal
 
# Modem admin URL
url = 'http://192.168.100.1/NetGearRgConnect.asp'
# Numericable admin username
username = 'MSO'
# Numericable admin password
password = '148naBle'

is_looping = False
 
def rrdNew(filename):
    ret = rrdtool.create(filename, "--step", "300", "--start", '0',
                     "DS:snr1:GAUGE:600:U:U",
                     "DS:snr2:GAUGE:600:U:U",
                     "DS:snr3:GAUGE:600:U:U",
                     "DS:rpl1:GAUGE:600:U:U",
                     "DS:rpl2:GAUGE:600:U:U",
                     "DS:rpl3:GAUGE:600:U:U",
                     "DS:tpl:GAUGE:600:U:U",
                     "RRA:MIN:0.5:1:600",
                     "RRA:MIN:0.5:6:700",
                     "RRA:MIN:0.5:24:775",
                     "RRA:MIN:0.5:288:797",
                     "RRA:AVERAGE:0.5:1:600",
                     "RRA:AVERAGE:0.5:6:700",
                     "RRA:AVERAGE:0.5:24:775",
                     "RRA:AVERAGE:0.5:288:797",
                     "RRA:MAX:0.5:1:600",
                     "RRA:MAX:0.5:6:700",
                     "RRA:MAX:0.5:24:775",
                     "RRA:MAX:0.5:444:797")
    if ret:
        print 'rrdNew:', rrdtool.error()
 
def rrdGraph(imgfile, rrdfile):
    print 're-generating graph...'
    rrdtool.graph(imgfile, "--start", "-1d", "--vertical-label=dBmV\dB",
              "--width", "800",
              "DEF:receive1=%s:rpl1:AVERAGE" %rrdfile,
              "DEF:receive2=%s:rpl2:AVERAGE" %rrdfile,
              "DEF:receive3=%s:rpl3:AVERAGE" %rrdfile,
              "DEF:signal1=%s:snr1:AVERAGE" %rrdfile,
              "DEF:signal2=%s:snr2:AVERAGE" %rrdfile,
              "DEF:signal3=%s:snr3:AVERAGE" %rrdfile,
              "DEF:transmit=%s:tpl:AVERAGE" %rrdfile,
              "LINE1:receive1#0000FF:Receive Power Level 0",
              "GPRINT:receive1:MIN:Min \: %6.2lf dBmV",
              "GPRINT:receive1:MAX:Max \: %6.2lf dBmV",
              "GPRINT:receive1:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "LINE1:receive2#0000CC:Receive Power Level 1",
              "GPRINT:receive2:MIN:Min \: %6.2lf dBmV",
              "GPRINT:receive2:MAX:Max \: %6.2lf dBmV",
              "GPRINT:receive2:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "LINE1:receive3#000099:Receive Power Level 2",
              "GPRINT:receive3:MIN:Min \: %6.2lf dBmV",
              "GPRINT:receive3:MAX:Max \: %6.2lf dBmV",
              "GPRINT:receive3:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "COMMENT:\\n",
              "LINE1:signal1#FF0000:Signal to Noise Ratio 0",
              "GPRINT:signal1:MIN:Min \: %6.2lf dBmV",
              "GPRINT:signal1:MAX:Max \: %6.2lf dBmV",
              "GPRINT:signal1:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "LINE1:signal2#AA0000:Signal to Noise Ratio 1",
              "GPRINT:signal2:MIN:Min \: %6.2lf dBmV",
              "GPRINT:signal2:MAX:Max \: %6.2lf dBmV",
              "GPRINT:signal2:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "LINE1:signal3#550000:Signal to Noise Ratio 2",
              "GPRINT:signal3:MIN:Min \: %6.2lf dBmV",
              "GPRINT:signal3:MAX:Max \: %6.2lf dBmV",
              "GPRINT:signal3:AVERAGE:Avg \: %6.2lf dBmV\\n",
              "COMMENT:\\n",
              "LINE1:transmit#00AA00:Transmit Power Level",
              "GPRINT:transmit:MIN:Min \: %6.2lf dB",
              "GPRINT:transmit:MAX:Max \: %6.2lf dB",
              "GPRINT:transmit:AVERAGE:Avg \: %6.2lf dB\\n")
 
def rrdUpdate(rrdfile, data):
    print 'update data:', data
    ret = rrdtool.update(rrdfile, data)
    if ret:
        print 'rrdUpdate:', rrdtool.error()
 
def refresh():
    print 'refreshing...'

    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)

    try:
	page = urllib2.urlopen(url)
    except:
        # Poor mans exception; no infos, just skip the processing
	print 'refresh aborted.'
	return
    soup = BeautifulSoup(page)
    tds = soup.findAll("td")
    rpl1 = float(tds[35].string.split(' ')[0]) # Puissance de reception 0 (-5 / 10 dBmV)
    rpl2 = float(tds[54].string.split(' ')[0]) # Puissance de reception 1 (-5 / 10 dBmV)
    rpl3 = float(tds[73].string.split(' ')[0]) # Puissance de reception 2 (-5 / 10 dBmV)
    snr1 = float(tds[37].string.split(' ')[0]) # SNR canal de reception 0 (>34 dB)
    snr2 = float(tds[56].string.split(' ')[0]) # SNR canal de reception 1 (>34 dB)
    snr3 = float(tds[75].string.split(' ')[0]) # SNR canal de reception 2 (>34 dB)
    tpl  = float(tds[92].string.split(' ')[0]) # Transmit Power Level (44 / 58 dBmV)
    #print snr1, snr2, snr3, rpl1, rpl2, rpl3, tpl
    # Prepare the values and cut of the string at the end
    rrdUpdate('modem.rrd', 'N:%f:%f:%f:%f:%f:%f:%f' %(snr1, snr2, snr3, rpl1, rpl2, rpl3, tpl))
 
def handler(signum, frame):
    global is_looping
    if signum == signal.SIGHUP:
        rrdGraph('modem.png', 'modem.rrd')
    elif signum == signal.SIGQUIT:
        print 'Graceful shutdown received. Please wait...'
        is_looping = False
    elif signum == signal.SIGUSR1:
        print 'Premature status update...'
        refresh()
 
if '-n' in sys.argv:
    print 'resetting database...'
    rrdNew('modem.rrd')
    sys.exit(0)
if '-g' in sys.argv:
    rrdGraph('modem.png', 'modem.rrd')
    sys.exit(0)
if '-l' in sys.argv:
    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGUSR1, handler)
    print 'SIGHUP  handler registered: Will draw the graph when signaled.'
    print 'SIGQUIT handler registered: Graceful shutdown.'
    print 'SIGUSR1 handler registered: Force premature status update.'
    is_looping = True
    while is_looping:
        refresh()
        print 'Sleeping for 300 seconds...'
        time.sleep(300)
else:
    refresh()

