import sys
import defgrab
import config

# Define link list
linkdb = []
sourcepath = config.sourcepath

# Process fully qualifed links
def processsoup(soup, baseurl):
    for i in soup:
        linkdb.append(baseurl + i)

# Resolve root directory links
rootsoup = defgrab.linkdir()
processsoup(rootsoup[0], rootsoup[1])

# Resolve child diretory links
for t in linkdb:
    if t[-1] == '/':
        childsoup = defgrab.linkdir(t)
        processsoup(childsoup[0], childsoup[1])

# Log linkdb creation
sys.stdout = open('linkdb.log', 'w')
print("\n".join(linkdb))

for d in linkdb:
    if not d[-1] == '/':
        pycurl.download(d)