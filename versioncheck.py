from __future__ import print_function
import requests
import os.path
import time
import shutil

url = 'https://www.google.com/images/srpr/logo11w.png'
file = 'logo11w.png'
r = requests.get(url)

meta = r.headers['last-modified']
print("Web  Last Modified: {0}".format(meta))

filetime = (time.strftime('%a, %d %b %Y %X GMT', time.gmtime(os.path.getmtime(file))))
print("File Last Modified: {0}".format(filetime))

if filetime > meta:
    print("Newer file found! Downloading...")
    f = requests.get(url, stream=True)
    with open ('logo11w.png', 'wb') as out_file:
        shutil.copyfileobj(response.raw,out_file)
    del response
else:
    print('No new version found. You got the latest file!')