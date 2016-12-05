import os
import logging
from bs4 import BeautifulSoup
import config
import requests

#Logging config
try:
    os.mkdir('logs')
except OSError:
    pass
FORMAT = '%(asctime)s %(name)-12s %(message)s'
logging.basicConfig(filename='logs/updater.log',format=FORMAT,datefmt='%d-%b-%y %H:%M:%S',level=logging.INFO)
logger = logging.getLogger(__name__)

# Removes irrelevant links
def removejunklinks(soup):
    output = []
    for link in soup.find_all('a'):
# drop the sorting and formatting links
        if '?' in link.get('href'):
            continue
# drop the parent directory links
        elif '..' in link.get('href'):
            continue
        else:
            x = (link.get('href'))
            output.append(x)
    return output

# Sent URI string to requests module for resolution, if HTTP 200 pass to BeautifulSoup
# module for cleansing links and pass to tree.process to remove junk links
def linkdir(path=config.sourcepath):
    resp = requests.get(url=path, proxies=config.proxy, timeout=5)
    if not resp.status_code == 200:
        logger.debug("Page not found. Fix the sourcepath setting in config.py.")
    else:
        soup = BeautifulSoup(resp.text, 'html.parser')
        soup = removejunklinks(soup)
        baseurl = path
        return soup, baseurl
