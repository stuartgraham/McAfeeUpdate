import os
import logging
import time
from bs4 import BeautifulSoup
import config
import requests

#Logging config
try:
    os.mkdir('logs')
except OSError:
    pass
FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename=('logs/updater'+ time.strftime("%d%m%Y") +'.log'),
                    format=FORMAT, datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
LOGGER = logging.getLogger(__name__)

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


def linkdir(path=config.sourcepath):
    """Sent URI string to requests module for resolution, if HTTP 200 pass to BeautifulSoup
     module for cleansing links and pass to tree.process to remove junk links"""
    resp = requests.get(url=path, proxies=config.proxy, timeout=config.httptimeout)
    if not resp.status_code == 200:
        LOGGER.debug("Page not found. Fix the sourcepath setting in config.py.")
    else:
        soup = BeautifulSoup(resp.text, 'html.parser')
        prunedsoup = removejunklinks(soup)
        baseurl = path
        return prunedsoup, baseurl
