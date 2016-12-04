import os
import defgrab
import processfile
import logging

logging.basicConfig(filename='the.log',datefmt='%m-%d %H:%M',level=logging.INFO)
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
def purgeold():
    print("code to go here")

roothttp()
childhttp()
linksprocess(linkdb)
loglinkdb(linkdb)
