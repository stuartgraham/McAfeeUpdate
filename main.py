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
logging.basicConfig(filename='logs/updater.log',format=FORMAT,datefmt='%d-%b-%y %H:%M:%S',level=logging.INFO)
logger = logging.getLogger(__name__)

# Define link list
linkdb = []

# Process fully qualifed links
def processsoup(soup, baseurl):
    for line in soup:
        linkdb.append(baseurl + line)

# Resolve root directory links
def roothttp():
    rootsoup = defgrab.linkdir()
    logger.info("Processing root HTTP directory")
    processsoup(rootsoup[0], rootsoup[1])

# Resolve child diretory links
def childhttp():
    childsoupcounter = 0
    for tempuri in linkdb:
        if tempuri[-1] == '/':
            childsoupcounter += 1
            childsoup = defgrab.linkdir(tempuri)
            logger.info("Processing child HTTP directory " + str(childsoupcounter) + " " + tempuri)
            processsoup(childsoup[0], childsoup[1])

# Process file from linkdb
def linksprocess(linkdb):
    for dluri in linkdb:
        if not dluri[-1] == '/':
            logger.info("Processing " + dluri)
            processfile.go(dluri)

# Log linkdb creation
# Test for Logs Dir and existing files, rectify as needed
def loglinkdb(linkdb):
    logger.info("Processing linkdb log/n/n")
    logger.info("\n".join(linkdb))

# Function will walk the filesystem and remove old files and folders
# as defined in the retention setting in config.py
def purgeold(retention=config.retention, rootdir=config.destinationpath):
    logger.info("Starting retention cleanup process")
    retentionbuffer = float(0.5)
    retention = retention + retentionbuffer
    logger.info("Retention is set to " + str(retention) + " days, rention setting + 0.5 day buffer")
    for root, dirs, files in os.walk(rootdir):
        if dirs == [] and files == []:
            os.removedirs(root)
            logger.info(root + " was empty and has been deleted")

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
                    logger.info(path + " was " + str(deltadays) + " days old and deleted")
                except OSError as err:
                    logger.info("OSerror" + err)
            else:
                logger.info(path + " is " + str(deltadays) + " days old and is retained")

# Main execution
processfile.checkdestpath()
purgeold()
roothttp()
childhttp()
linksprocess(linkdb)
loglinkdb(linkdb)
logger.info("****PASS COMPLETED****")
