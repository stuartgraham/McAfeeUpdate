import os
import hashlib
import logging
import requests
import config

#Logging config
FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename='the.log',format=FORMAT,datefmt='%m-%d-%y %H:%M:%S',level=logging.INFO)
logger = logging.getLogger(__name__)

# Module will check existance of the base destination path from config
# and create as needed
def checkdestpath(destinationpath=config.destinationpath):
    if not os.path.exists(destinationpath):
        try:
            os.mkdir(destinationpath)
            logger.info(destinationpath + " directory was created")
        except OSError as err:
            logger.info(err)
            pass
        else:
            logger.info(destinationpath + " directory already exists skipping")

# Module strips the sourcepath defined in config.py from the URI
def pathdef(uri, sourcepath=config.sourcepath):
    path = uri.replace(sourcepath, "")
    return path

# Module will test and create the directory structure for the file
# as needed
def localdir(path, destinationpath=config.destinationpath):
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
        depth = 0
        for i in directory:
            if depth == 0:
                workingpath = i
            else:
                workingpath = "\\".join(directory[0:depth+1])
            depth += 1
            mkpath = (destinationpath + "\\" + workingpath)
            if not os.path.exists(mkpath):
                try:
                    os.mkdir(mkpath)
                    logger.info("DIRCHECK: " + mkpath + " was created")
                except OSError as err:
                    logger.info(err)
            else:
                logger.info("DIRCHECK: " + mkpath + " already exists, skipping mkdir for this directory")
    return mkpath, filename

# Will download the file using the requests module
def checkfile(writepath, dluri):
    if os.path.exists(writepath):
        try:
            hasher = hashlib.md5()
            with open(writepath, 'rb') as m:
                buf = m.read()
                hasher.update(buf)
                downstreammd5 = hasher.hexdigest()
            logger.info("Downstream MD5 Hash : " + downstreammd5)
            resp = requests.get(url=dluri, proxies=config.proxy, timeout=5)
            upstreammd5 = resp.headers['ETag'].split(":", 1)[0]
            upstreammd5 = upstreammd5[1:]
            logger.info("Downstream MD5 Hash : " + downstreammd5)
            logger.info("Upstream MD5 Hash   : " + upstreammd5)
            if upstreammd5 == downstreammd5:
                logger.info(writepath + " MD5 match, skip downloading")
                dlreq = 0
            else:
                logger.info(writepath + " MD5 didnt match, progressing to download")
                dlreq = 1
        except KeyError as err:
            logging.error(err)
            dlreq = 1
    else:
        logger.info(writepath + " this was not detected, sending for download")
        dlreq = 1
    return dlreq

def dlfile(dlreq, writepath, dluri):
    if dlreq == 1:
        resp = requests.get(url=dluri, proxies=config.proxy, stream=True)
        logger.info("Committing " + dluri + " to " + writepath)
        with open(writepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        logger.info(writepath + " completed, sending for MD5 verification")
        checkfile(writepath, dluri)

# Main method in the module, when called will create folder structure and
# download files for URIs passed to it
def go(dluri, sourcepath=config.sourcepath, destpath=config.destinationpath):
    checkdestpath()
    path = pathdef(dluri)
    temppath = localdir(path)
    x = temppath[0]
    y = temppath[1]
    if x and y == '':
        logger.info("Blank URI skipping")
    elif x == "\\":
        writepath = x + y
        dlreq = checkfile(writepath, dluri)
        dlfile(dlreq, writepath, dluri)
    else:
        writepath = x + "\\" + y
        dlreq = checkfile(writepath, dluri)
        dlfile(dlreq, writepath, dluri)
