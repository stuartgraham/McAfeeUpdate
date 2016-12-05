import os
from os.path import join, getsize
import logging
import time
import defgrab
import processfile
import config

FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename='the.log',format=FORMAT,datefmt='%m-%d-%y %H:%M',level=logging.INFO)
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
        else:
            logger.info("Not working")

# Log linkdb creation
# Test for Logs Dir and existing files, rectify as needed
def loglinkdb(linkdb):
    if not os.path.exists('logs'):
        try:
            os.mkdir('logs')
        except OSError as err:
            logger.debug(err)
            pass

    logger.info("Processing linkdb log")
    logger.info("\n".join(linkdb))

# Function will walk the filesystem and remove old files and folders
# as defined in the retention setting in config.py
def purgeold(retention=config.retention, rootdir=config.destinationpath):
    logger.info("Starting retention cleanup process")
    for root, dirs, files in os.walk(rootdir):
        if dirs == [] and files == []:
            os.removedirs(root)
            logger.info(root + " was empty and has been deleted")

        for i in files:
            path = (root+"\\"+i)
            timestamp = os.stat(path)
            createsecs = timestamp.st_ctime
            currentsecs = time.time()
            deltasecs = currentsecs - createsecs
            deltadays = float(deltasecs/86400)
            rententionbuffer = float(0.5)
            rentention = retention + rententionbuffer
            if deltadays > rentention:
                try:
                    os.remove(path)
                    logger.info(path + " was " + str(deltadays) + " days old and deleted")
                except OSError as err:
                    logger.info("OSerror" + err)
            else:
                logger.info(path + " is " + str(deltadays) + " days old and is retained")

# Main execution
roothttp()
childhttp()
linksprocess(linkdb)
loglinkdb(linkdb)
purgeold()
