import re
import urllib2
import pycurl

url = "http://server.domain/"
path = "path/"
pattern = '<A HREF="/%s.*?">(.*?)</A>' % path

response = urllib2.urlopen(url+path).read()

for filename in re.findall(pattern, response):
    fp = open(filename, "wb")
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url+path+filename)
    curl.setopt(pycurl.WRITEDATA, fp)
    curl.perform()
    curl.close()
    fp.close()