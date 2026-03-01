"""Grab HTTP directory from McAfee site and download directory structure"""

import os
import logging
import time
import hashlib
from queue import Queue
from threading import Thread, Lock
from bs4 import BeautifulSoup
import requests
import config

PROCS = (os.cpu_count() or 4) * 4

# Thread-safe counters
_counter_lock = Lock()
FILESDELETED = 0
FILESCREATED = 0
DIRSDELETED = 0
DIRSCREATED = 0

class DownloadWorker(Thread):
    """ Defines worker threads"""
    def __init__(self, workerid, queue, session):
        Thread.__init__(self)
        self.queue = queue
        self.workerid = workerid
        self.session = session

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            writepath, link = self.queue.get()
            dlreq = checkfile(writepath, link, self.session, self.workerid)
            dlfile(dlreq, writepath, link, self.session, self.workerid)
            if dlreq == 1:
                incrementcounters(filescreated=1)
            self.queue.task_done()


# Logging config
try:
    os.mkdir('logs')
except OSError:
    pass

FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(
    filename=('logs/updater'+ time.strftime("%d%m%Y") +'.log'),
    format=FORMAT,
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


def purgeold(retention=config.RETENTION, rootdir=config.DESTINATIONPATH):
    """Function will walk the filesystem and remove old files and
    folders as defined in the retention setting in config.py"""
    if rootdir == 'logs':
        LOGGER.info("RETENTIONINFO : Starting retention cleanup process for logs")
    else:
        LOGGER.info("RETENTIONINFO : Starting retention cleanup process for files")
    
    retention += 0.5
    LOGGER.info("RETENTIONINFO : Retention is set to %.1f days, retention setting + 0.5 day buffer", retention)
    
    for root, dirs, files in os.walk(rootdir):
        if dirs == [] and files == []:
            os.removedirs(root)
            incrementcounters(dirsdeleted=1)
            LOGGER.info("RETENTIONDELETE : %s was empty and has been deleted", root)

        for i in files:
            path = os.path.join(root, i)
            deltadays = timecalc(os.stat(path))
            if deltadays > retention:
                try:
                    os.remove(path)
                    incrementcounters(filesdeleted=1)
                    LOGGER.info("RETENTIONDELETE : %s was %.3f days old and deleted", path, deltadays)
                except OSError as err:
                    LOGGER.error("OSerror: %s", err)
            else:
                LOGGER.debug("RETENTIONKEEP : %s is %.3f days old and is retained", path, deltadays)


def soupgen(path=config.SOURCEPATH, session=None):
    """Send URI string to requests module for resolution, if HTTP 200 pass to BeautifulSoup
     module for cleansing links and remove junk links (not files or dirs)"""
    if session is None:
        session = requests.Session()
    
    resp = session.get(url=path, proxies=config.PROXY, timeout=config.HTTPTIMEOUT)
    if resp.status_code != 200:
        LOGGER.debug("DEBUG : Page not found. Fix the sourcepath setting in config.py.")
        resp.close()
        return None, path
    else:
        soup = BeautifulSoup(resp.text, 'html.parser')
        prunedsoup = removejunklinks(soup)
        resp.close()
        return prunedsoup, path


def constructlinkslist(session=None):
    """Construct link list"""
    if session is None:
        session = requests.Session()
    
    linkdump = soupgen(config.SOURCEPATH, session)
    if linkdump[0] is None:
        return []
    
    linkslist = []
    # Import cleaned links for root directory to list
    LOGGER.info("DIRPROCESS : Processing root HTTP directory")
    for line in linkdump[0]:
        linkslist.append(linkdump[1] + line)
    
    # Import cleaned links for child direcories to list
    # Use index-based iteration to handle dynamically growing list
    childsoupcounter = 0
    i = 0
    while i < len(linkslist):
        tempuri = linkslist[i]
        if tempuri[-1] == '/':
            childsoupcounter += 1
            linkdump = soupgen(tempuri, session)
            if linkdump[0] is not None:
                LOGGER.info("DIRPROCESS : Processing child HTTP directory %d %s", childsoupcounter, tempuri)
                for line in linkdump[0]:
                    linkslist.append(linkdump[1] + line)
        i += 1
    
    return linkslist


def loglinkdb(linkslist):
    """Log linkdb creation. Test for Logs Dir and existing files, rectify as needed"""
    LOGGER.info("DIRPROCESS : Dump log of links processed")
    LOGGER.info("\n".join(linkslist))


def timecalc(timestamp):
    """Converts timestamp to seconds, does local conversion
    and defines delta between now and timestamp"""
    createsecs = timestamp.st_ctime
    currentsecs = time.time()
    deltasecs = currentsecs - createsecs
    deltadays = deltasecs / 86400
    return round(deltadays, 3)


def incrementcounters(filesdeleted=0, filescreated=0, dirsdeleted=0, dirscreated=0):
    """Increment counters (thread-safe)"""
    global FILESDELETED, FILESCREATED, DIRSDELETED, DIRSCREATED
    
    with _counter_lock:
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
        href = link.get('href')
        if href is None:
            continue
        # drop the sorting and formatting links
        if '?' in href:
            continue
        # drop the parent directory links
        if '..' in href:
            continue
        output.append(href)
    return output


def checkdestpath(destinationpath=config.DESTINATIONPATH):
    """Module will check existance of the base destination path from config and create as needed"""
    if not os.path.exists(destinationpath):
        try:
            os.makedirs(destinationpath)
            LOGGER.info("DIRCREATE : %s was created", destinationpath)
        except OSError as err:
            LOGGER.error("%s", err)
    else:
        LOGGER.info("DIRSKIP : %s already exists, skipping mkdir", destinationpath)
    
    # Create anchor file to stop deletion
    anchorfile = os.path.join(destinationpath, 'anchor.txt')
    try:
        with open(anchorfile, 'a'):
            os.utime(anchorfile, None)
    except OSError as err:
        LOGGER.error("Failed to create anchor file: %s", err)


def makedir(path, destinationpath=config.DESTINATIONPATH):
    """Test and create the directory structure for the file as needed"""
    dircreated = False
    
    if "/" not in path:
        mkpath = destinationpath
        filename = path
    elif path == '':
        mkpath = ''
        filename = ''
    else:
        directory = path.split("/")
        filename = directory[-1]
        directory.pop(-1)
        workingpath = "/".join(directory)
        mkpath = os.path.join(destinationpath, workingpath)
        # Execute makedirs to build directories
        try:
            os.makedirs(mkpath)
            LOGGER.info("DIRCHECKCREATE : %s was created", mkpath)
            dircreated = True
        except OSError:
            LOGGER.debug("DIRCHECKSKIP : %s already exists, skipping mkdir", mkpath)
    
    return mkpath, filename, dircreated


def calculate_md5(filepath, chunk_size=8192):
    """Calculate MD5 hash of a file using streaming (memory efficient)"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def checkfile(writepath, dluri, session, workerid=None):
    """Inspect the files upstream header tags for md5 hash and compare
    before sending for download as required"""
    worker_prefix = f"WorkerID {workerid} : " if workerid is not None else ""
    
    if os.path.exists(writepath):
        try:
            downstreammd5 = calculate_md5(writepath)
            upstreammd5 = None
            
            for attempt in range(config.MAXRETRIES):
                try:
                    resp = session.head(url=dluri, proxies=config.PROXY,
                                       timeout=config.HTTPTIMEOUT)
                    etag = resp.headers.get('ETag', '')
                    if etag:
                        upstreammd5 = etag.split(":", 1)[0].strip('"')
                    resp.close()
                    break
                except requests.exceptions.Timeout:
                    LOGGER.error("%sTIMEOUT : Connection timed out gathering the header (attempt %d)", 
                               worker_prefix, attempt + 1)
            
            LOGGER.info("%sHASHCALC : Downstream MD5 Hash : %s", worker_prefix, downstreammd5)
            LOGGER.info("%sHASHCALC : Upstream MD5 Hash   : %s", worker_prefix, upstreammd5 or "N/A")
            
            if upstreammd5 and upstreammd5 == downstreammd5:
                LOGGER.info("%sHASHMATCH: %s MD5 match", worker_prefix, writepath)
                return 0
            else:
                LOGGER.info("%sHASHMISMATCH : %s MD5 didn't match, progressing to download", 
                          worker_prefix, writepath)
                return 1
                
        except (KeyError, OSError) as err:
            LOGGER.error("%sError checking file: %s", worker_prefix, err)
            return 1
    else:
        LOGGER.info("%sFILECHECK : %s this was not detected, sending for download", 
                   worker_prefix, writepath)
        return 1


def dlfile(dlreq, writepath, dluri, session, workerid=None):
    """Download file when dlreq is passed in as 1"""
    worker_prefix = f"WorkerID {workerid} : " if workerid is not None else ""
    
    if dlreq == 1:
        for attempt in range(config.MAXRETRIES):
            try:
                resp = session.get(url=dluri, proxies=config.PROXY,
                                 stream=True, timeout=config.HTTPTIMEOUT)
                LOGGER.info("%sDOWNLOADFILE : Downloading %s to %s", worker_prefix, dluri, writepath)
                
                with open(writepath, 'wb') as tempfile:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            tempfile.write(chunk)
                
                resp.close()
                LOGGER.info("%sDOWNLOADCOMPLETE : %s completed, sending for MD5 verification", 
                          worker_prefix, writepath)
                checkfile(writepath, dluri, session, workerid)
                return
                
            except requests.exceptions.Timeout:
                LOGGER.error("%sTIMEOUT : Connection timed out downloading the file (attempt %d)", 
                           worker_prefix, attempt + 1)
            except requests.exceptions.ConnectionError as err:
                LOGGER.error("%sConnection error downloading file (attempt %d): %s", 
                           worker_prefix, attempt + 1, err)


def process(links):
    """Create folder structure and download files for URIs passed to it"""
    linkqueue = Queue()
    
    # Pre-process all links to create directory structure
    for link in links:
        if not link[-1] == '/':
            LOGGER.info("LINKPROCESS : Processing %s", link)
            path = link.replace(config.SOURCEPATH, "")
            temppath = makedir(path)
            # Increment the created directory counter
            if temppath[2]:
                incrementcounters(dirscreated=1)
            
            # Decide how to download file
            if temppath[0] and temppath[1] == '':
                LOGGER.info("NOURL : Blank URI skipping")
                continue
            elif temppath[0] == os.sep:
                writepath = temppath[0] + temppath[1]
            else:
                writepath = os.path.join(temppath[0], temppath[1])
            
            linkqueue.put((writepath, link))
    
    # Create shared session for connection pooling
    session = requests.Session()
    
    # Start worker threads
    workers = []
    for worker_id in range(PROCS):
        worker = DownloadWorker(worker_id, linkqueue, session)
        worker.daemon = True
        worker.start()
        workers.append(worker)
    
    # Wait for all tasks to complete
    linkqueue.join()


# Main execution
if __name__ == "__main__":
    STARTTIME = time.time()
    LOGGER.info("###### PASS STARTED ######")
    
    checkdestpath()
    purgeold()
    
    # Create session for directory discovery
    session = requests.Session()
    LINKSLIST = constructlinkslist(session)
    session.close()
    
    process(LINKSLIST)
    loglinkdb(LINKSLIST)
    
    # Purge old logs
    purgeold(30, 'logs')
    
    COMPLETETIME = (time.time() - STARTTIME) / 60
    COMPLETETIME = round(COMPLETETIME, 3)
    
    LOGGER.info("TIME : The pass took %.3f minutes", COMPLETETIME)
    LOGGER.info("RETENTIONSTATS : %d directories were deleted", DIRSDELETED)
    LOGGER.info("RETENTIONSTATS : %d files were deleted", FILESDELETED)
    LOGGER.info("DOWNLOADSTATS : %d directories were created", DIRSCREATED)
    LOGGER.info("DOWNLOADSTATS : %d files were downloaded", FILESCREATED)
    LOGGER.info("****** PASS COMPLETED ******")
