"""Grab HTTP directory from McAfee site and download directory structure"""

import os
import logging
import time
import hashlib
from queue import Queue
from threading import Thread
from bs4 import BeautifulSoup
import requests
import config

PROCS = os.cpu_count() * 4
FILESDELETED = 0
FILESCREATED = 0
DIRSDELETED = 0
DIRSCREATED = 0

class DownloadWorker(Thread):
    """ Defines worker threads"""
    def __init__(self, workerid, queue):
        Thread.__init__(self)
        self.queue = queue
        self.workerid = workerid

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            writepath, link = self.queue.get()
            workerid = self.workerid
            dlreq = checkfile(writepath, link, workerid)
            dlfile(dlreq, writepath, link, workerid)
            if dlreq == 1:
                incrementcounters(filescreated=1)
            self.queue.task_done()


#Logging config
try:
    os.mkdir('logs')
except OSError:
    pass
FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename=('logs/updater'+ time.strftime("%d%m%Y") +'.log'),
                    format=FORMAT, datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def purgeold(retention=config.RETENTION, rootdir=config.DESTINATIONPATH):
    """Function will walk the filesystem and remove old files and
    folders as defined in the retention setting in config.py"""
    if rootdir == 'logs':
        LOGGER.info("RETENTIONINFO : Starting retention cleanup process for logs")
    else:
        LOGGER.info("RETENTIONINFO : Starting retention cleanup process for files")
    retention += float(0.5)
    LOGGER.info("RETENTIONINFO : Retention is set to " + str(retention) +
                " days, rention setting + 0.5 day buffer")
    for root, dirs, files in os.walk(rootdir):
        if dirs == [] and files == []:
            os.removedirs(root)
            incrementcounters(dirsdeleted=1)
            LOGGER.info("RETENTIONDELETE : " + root + " was empty and has been deleted")

        for i in files:
            path = (root+"\\"+i)
            deltadays = timecalc(os.stat(path))
            if deltadays > retention:
                try:
                    os.remove(path)
                    incrementcounters(filesdeleted=1)
                    LOGGER.info("RETENTIONDELETE : " + path + " was " + str(deltadays) +
                                " days old and deleted")
                except OSError as err:
                    LOGGER.info("OSerror" + err)
            else:
                LOGGER.info("RETENTIONKEEP : " + path + " is " + str(deltadays) +
                            " days old and is retained")




def soupgen(path=config.SOURCEPATH):
    """Send URI string to requests module for resolution, if HTTP 200 pass to BeautifulSoup
     module for cleansing links and remove junk links (not files or dirs)"""
    resp = requests.get(url=path, proxies=config.PROXY, timeout=config.HTTPTIMEOUT)
    if not resp.status_code == 200:
        LOGGER.debug("DEBUG : Page not found. Fix the sourcepath setting in config.py.")
    else:
        soup = BeautifulSoup(resp.text, 'html.parser')
        prunedsoup = removejunklinks(soup)
        baseurl = path
        return prunedsoup, baseurl


def constructlinkslist():
    """Construct link list"""
    linkdump = soupgen()
    linkslist = []
    # Import cleaned links for root directory to list
    LOGGER.info("DIRPROCESS : Processing root HTTP directory")
    for line in linkdump[0]:
        linkslist.append(linkdump[1] + line)
    # Import cleaned links for child direcories to list
    childsoupcounter = 0
    for tempuri in linkslist:
        if tempuri[-1] == '/':
            childsoupcounter += 1
            linkdump = soupgen(tempuri)
            LOGGER.info("DIRPROCESS : Processing child HTTP directory " +
                        str(childsoupcounter) + " " + tempuri)
            for line in linkdump[0]:
                linkslist.append(linkdump[1] + line)
    return linkslist


def loglinkdb(linkslist):
    """Log linkdb creation. Test for Logs Dir and existing files, rectify as needed"""
    LOGGER.info("DIRPROCESS : Dump log of links processed")
    LOGGER.info("\n".join(linkslist))


def timecalc(timestamp):
    """Converts timestamp to seconds, does local conversion
    and defines delta between now and timestamp"""
    createsecs = timestamp.st_ctime
    templocaltime = time.localtime()
    currentsecs = time.mktime(templocaltime)
    deltasecs = currentsecs - createsecs
    deltadays = float(deltasecs/86400)
    deltadays = round(deltadays, 3)
    return deltadays

def incrementcounters(filesdeleted=0, filescreated=0, dirsdeleted=0, dirscreated=0):
    """Increment counters"""
    global FILESDELETED
    global FILESCREATED
    global DIRSDELETED
    global DIRSCREATED
    if filesdeleted > 0:
        FILESDELETED += filesdeleted
    if filescreated > 0:
        FILESCREATED += filescreated
    if dirsdeleted > 0:
        DIRSDELETED += dirsdeleted
    if dirscreated > 0:
        DIRSCREATED += dirscreated


def removejunklinks(soup):
    """Removes irrelevant links"""
    output = []
    for link in soup.find_all('a'):
        # drop the sorting and formatting links
        if '?' in link.get('href'):
            continue
        # drop the parent directory links
        elif '..' in link.get('href'):
            continue
        else:
            worklink = (link.get('href'))
            output.append(worklink)
    return output


def checkdestpath(destinationpath=config.DESTINATIONPATH):
    """Module will check existance of the base destination path from config and create as needed"""
    if not os.path.exists(destinationpath):
        try:
            os.makedirs(destinationpath)
            LOGGER.info("DIRCREATE : " + destinationpath + " was created")
        except OSError as err:
            LOGGER.info(err)
        else:
            LOGGER.info("DIRSKIP : " + destinationpath + " already exists, skipping mkdir")
    #Create anchor file to stop deletion
    anchorfile = (destinationpath + '\\anchor.txt')
    if not os.path.exists(anchorfile):
        with open(anchorfile, 'a'):
            os.utime(anchorfile, None)
    else:
        os.remove(anchorfile)
        with open(anchorfile, 'a'):
            os.utime(anchorfile, None)


def makedir(path, destinationpath=config.DESTINATIONPATH):
    """Test and create the directory structure for the file as needed"""
    # Prep the mkpath
    dircreated = False
    if "/" not in path:
        mkpath = (destinationpath)
        filename = path
    elif path == '':
        mkpath = ''
        filename = ''
    else:
        directory = path.split("/")
        filename = directory[-1]
        directory.pop(-1)
        workingpath = "\\".join(directory)
        mkpath = (destinationpath + "\\" + workingpath)
        # Execute makedirs to build directors
        try:
            os.makedirs(mkpath)
            LOGGER.info("DIRCHECKCREATE : " + mkpath + " was created")
            dircreated = True
        except OSError:
            LOGGER.info("DIRCHECKSKIP : " + mkpath + " already exists, skipping mkdir")
    return mkpath, filename, dircreated


def checkfile(writepath, dluri, workerid):
    """Inspect the files upstream header tags for md5 hash and compare
    before sending for download as required"""
    if os.path.exists(writepath):
        try:
            hasher = hashlib.md5()
            with open(writepath, 'rb') as tempfile:
                buf = tempfile.read()
                hasher.update(buf)
                downstreammd5 = hasher.hexdigest()

            for _ in range(config.MAXRETRIES):
                try:
                    resp = requests.head(url=dluri, proxies=config.PROXY,
                                         timeout=config.HTTPTIMEOUT)
                    upstreammd5 = resp.headers['ETag'].split(":", 1)[0]
                    upstreammd5 = upstreammd5[1:]
                    LOGGER.info("WorkerID " + str(workerid) + " : HASHCALC : Downstream MD5 Hash : "
                                + downstreammd5)
                    LOGGER.info("WorkerID " + str(workerid) + " : HASHCALC : Upstream MD5 Hash   : "
                                + upstreammd5)
                    resp.close()
                    break
                except requests.exceptions.Timeout:
                    LOGGER.error("WorkerID " + str(workerid) +
                                 " : TIMEOUT : Connecion timed out gathering the header")
            if upstreammd5 == downstreammd5:
                LOGGER.info("WorkerID " + str(workerid) +
                            " : HASHMATCH : " + writepath + " - MD5 match")
                dlreq = 0
            else:
                LOGGER.info("WorkerID " + str(workerid) + " : HASHMISMATCH : " + writepath +
                            " MD5 didnt match, progressing to download")
                dlreq = 1
        except KeyError as err:
            logging.error(err)
            dlreq = 1
    else:
        LOGGER.info("WorkerID " + str(workerid) + " : FILECHECK : " + writepath +
                    " this was not detected, sending for download")
        dlreq = 1
    return dlreq


def dlfile(dlreq, writepath, dluri, workerid):
    """Download file when dlreq is passed in as 1"""
    if dlreq == 1:
        for _ in range(config.MAXRETRIES):
            try:
                resp = requests.get(url=dluri, proxies=config.PROXY,
                                    stream=True, timeout=config.HTTPTIMEOUT)
                LOGGER.info("WorkerID " + str(workerid) + " : DOWNLOADFILE : Downloading " + dluri)
                LOGGER.info(" to " + writepath)
                with open(writepath, 'wb') as tempfile:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            tempfile.write(chunk)
                resp.close()
                break
            except requests.exceptions.Timeout:
                LOGGER.error("WorkerID " + str(workerid) +
                             " : TIMEOUT : Connection timed out downloading the file")
            except requests.exceptions.ConnectionError:
                LOGGER.error("TIMEOUT : Connection timed out downloading the file")

        LOGGER.info("WorkerID " + str(workerid) + " : DOWNLOADCOMPLETE : "
                    + writepath + " completed, sending for MD5 verification")
        checkfile(writepath, dluri, workerid)


def process(links):
    """Create folder structure and download files for URIs passed to it"""
    linkqueue = Queue()
    for link in links:
        if not link[-1] == '/':
            LOGGER.info("LINKPROCESS : Processing " + link)
            path = link.replace(config.SOURCEPATH, "")
            temppath = makedir(path)
            # Incremenent the created directory counter
            if temppath[2]:
                incrementcounters(dirscreated=1)
            # Decide how to download file
            if temppath[0] and temppath[1] == '':
                LOGGER.info("NOURL : Blank URI skipping")
            elif temppath[0] == "\\":
                writepath = temppath[0] + temppath[1]
            else:
                writepath = temppath[0] + "\\" + temppath[1]
            linkqueue.put((writepath, link))

    for worker in range(PROCS):
        worker = DownloadWorker(worker, linkqueue)
        # Setting daemon to True will let the main
        # thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()

    linkqueue.join()



# Main execution
if __name__ == "__main__":
    STARTTIME = time.time()
    LOGGER.info("###### PASS STARTED ######")
    checkdestpath()
    purgeold()
    LINKSLIST = constructlinkslist()
    process(LINKSLIST)
    loglinkdb(LINKSLIST)
    #Purge old logs
    purgeold(30, 'logs')
    COMPLETETIME = (time.time() - STARTTIME)/60
    COMPLETETIME = round(COMPLETETIME, 3)
    LOGGER.info("TIME : The pass took " + str(COMPLETETIME) + " minutes")
    LOGGER.info("RETENTIONSTATS : " + str(DIRSDELETED) + " directories were deleted")
    LOGGER.info("RETENTIONSTATS : " + str(FILESDELETED) + " files were deleted")
    LOGGER.info("DOWNLOADSTATS : " + str(DIRSCREATED) + " directories were created")
    LOGGER.info("DOWNLOADSTATS : " + str(FILESCREATED) + " files were downloaded")
    LOGGER.info("****** PASS COMPLETED ******")
