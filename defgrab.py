import config
import tree
import requests
from bs4 import BeautifulSoup

#Gather root HTML and configure the soup
def grabber(pathext = ''):
    resp = requests.get(config.SourcePath + pathext, proxies=config.Proxy, timeout=5)
    if not resp.status_code == 200:
        print ("Page not found. Fix the SourcePath setting.")
    else:  
        soup = BeautifulSoup(resp.text, 'html.parser')
        tree.process(soup)
    