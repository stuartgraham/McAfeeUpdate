import sys
import os
import defgrab
import processfile

# Define link list
linkdb = []

# Process fully qualifed links
def processsoup(soup, baseurl):
    for line in soup:
        linkdb.append(baseurl + line)

# Resolve root directory links
def roothttp():
    rootsoup = defgrab.linkdir()
    print("Processing root HTTP directory")
    processsoup(rootsoup[0], rootsoup[1])

# Resolve child diretory links
def childhttp():
    childsoupcounter = 0
    for tempuri in linkdb:
        if tempuri[-1] == '/':
            childsoupcounter += 1
            childsoup = defgrab.linkdir(tempuri)
            print("Processing child HTTP directory " + str(childsoupcounter) + " " + tempuri)
            processsoup(childsoup[0], childsoup[1])

# Process file from linkdb
def linksprocess(linkdb):
    for dluri in linkdb:
        if not dluri[-1] == '/':
            print("Processing " + dluri)
            processfile.go(dluri)
        else:
            print("Not working")

# Log linkdb creation
# Test for Logs Dir and existing files, rectify as needed
def loglinkdb(linkdb):
    if not os.path.exists('logs'):
        try:
            os.mkdir('logs')
        except OSError as err:
            print(err)
            pass
    if os.path.exists('logs/linkdb.log'):
        os.remove('logs/linkdb.log')
    print("Processing linkdb log")
    sys.stdout = open('logs/linkdb.log', 'w')
    print("\n".join(linkdb))

roothttp()
childhttp()
linksprocess(linkdb)
loglinkdb(linkdb)
