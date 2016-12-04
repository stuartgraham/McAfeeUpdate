import sys
import os
import defgrab

# Define link list
linkdb = []

# Process fully qualifed links
def processsoup(soup, baseurl):
    for line in soup:
        linkdb.append(baseurl + line)

# Resolve root directory links
rootsoup = defgrab.linkdir()
processsoup(rootsoup[0], rootsoup[1])

# Resolve child diretory links
for tempuri in linkdb:
    if tempuri[-1] == '/':
        childsoup = defgrab.linkdir(tempuri)
        processsoup(childsoup[0], childsoup[1])

# Log linkdb creation
# Test for Logs Dir and existing files, rectify as needed
if not os.path.exists('logs'):
    try:
        os.mkdir('logs')
    except OSError as err:
        print(err)
        pass

if os.path.exists('logs/linkdb.log'):
    os.remove('logs/linkdb.log')

sys.stdout = open('logs/linkdb.log', 'w')
print("\n".join(linkdb))

# Process file from linkdb
for dluri in linkdb:
    if not dluri[-1] == '/':
        continue
        processfile(dluri)
