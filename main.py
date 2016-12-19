import os
import logging
import time
import defgrab
import processfile
import config

#Logging config
try:
    os.mkdir('logs')
except OSError:
    pass
FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename=('logs/updater'+ time.strftime("%d%m%Y") +'.log'),
                    format=FORMAT, datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Define link list
linkdb = []

def processsoup(soup, baseurl):
    """Process fully qualifed links"""
    for line in soup:
        linkdb.append(baseurl + line)

def roothttp():
    """Resolve root directory links"""
    rootsoup = defgrab.linkdir()
    LOGGER.info("Processing root HTTP directory")
    processsoup(rootsoup[0], rootsoup[1])

def childhttp():
    """Resolve child diretory links"""
    childsoupcounter = 0
    for tempuri in linkdb:
        if tempuri[-1] == '/':
            childsoupcounter += 1
            childsoup = defgrab.linkdir(tempuri)
            LOGGER.info("Processing child HTTP directory " + str(childsoupcounter) + " " + tempuri)
            processsoup(childsoup[0], childsoup[1])

# Process file from linkdb
def linksprocess(linkdb):
    """Process file from linkdb"""
    for dluri in linkdb:
        if not dluri[-1] == '/':
            LOGGER.info("Processing " + dluri)
            processfile.go(dluri)

# Log linkdb creation
# Test for Logs Dir and existing files, rectify as needed
def loglinkdb(linkdb):
    """Log linkdb creation. Test for Logs Dir and existing files, rectify as needed"""
    LOGGER.info("Processing linkdb log/n/n")
    LOGGER.info("\n".join(linkdb))

# Function will walk the filesystem and remove old files and folders
# as defined in the retention setting in config.py
def purgeold(retention=config.retention, rootdir=config.destinationpath):
    LOGGER.info("Starting retention cleanup process")
    retentionbuffer = float(0.5)
    retention = retention + retentionbuffer
    LOGGER.info("Retention is set to " + str(retention) + " days, rention setting + 0.5 day buffer")
    for root, dirs, files in os.walk(rootdir):
        if dirs == [] and files == []:
            os.removedirs(root)
            LOGGER.info(root + " was empty and has been deleted")

        for i in files:
            path = (root+"\\"+i)
            timestamp = os.stat(path)
            createsecs = timestamp.st_ctime
            templocaltime = time.localtime()
            currentsecs = time.mktime(templocaltime)
            deltasecs = currentsecs - createsecs
            deltadays = float(deltasecs/86400)
            deltadays = round(deltadays, 3)
            if deltadays > retention:
                try:
                    os.remove(path)
                    LOGGER.info("RETENTIONDEL: " + path + " was " + str(deltadays) + " days old and deleted")
                except OSError as err:
                    LOGGER.info("OSerror" + err)
            else:
                LOGGER.info("RETENTIONKEEP: " + path + " is " + str(deltadays) + " days old and is retained")

# Main execution
processfile.checkdestpath()
purgeold()
roothttp()
childhttp()
linksprocess(linkdb)
loglinkdb(linkdb)
LOGGER.info("****PASS COMPLETED****")
#Purge old logs
purgeold(30, 'logs')
