import os
import config
import requests
# Establish Directory
# Establish Destination
# Establish if timestamp match
# Download if no match
# Log

# Module will check existance of the base destination path from config
# and create as needed
def checkdestpath(destinationpath=config.destinationpath):
    if not os.path.exists(destinationpath):
        try:
            os.mkdir(destinationpath)
            print(destinationpath + " was created")
        except OSError as err:
            print(err)
            pass
        else:
            print(destinationpath + " already exists")

# Module strips the sourcepath defined in config.py from the URI
def pathdef(uri, sourcepath=config.sourcepath):
    path = uri.replace(sourcepath, "")
    print ("pathdef returned " + path)
    return path

# Module will test and create the directory structure for the file
# as needed
def localdir(path, destinationpath=config.destinationpath):
    if "/" not in path:
        mkpath = (destinationpath)
        filename = path
    elif path=='':
        mkpath = ''
        filename = ''
    else:
        directory = path.split("/")
        filename = directory[-1]
        directory.pop(-1)
        print(directory)
        print("directory list")
        depth = 0
        for i in directory:
            if depth == 0:
                workingpath = i
                print(workingpath + "1111111111")
            else:
        # not sure what +1 is needed
                workingpath = "\\".join(directory[0:depth+1])
                print(workingpath + "22222222")
            depth += 1
            mkpath = (destinationpath + "\\" + workingpath)
            if not os.path.exists(mkpath):
                try:
                    os.mkdir(mkpath)
                    print(mkpath + " was created")
                except OSError as err:
                    print(err)
            else:
                print(mkpath + "already exists")
    return mkpath, filename

# Will download the file using the requests module
def writethefile(writepath, dluri):
    print("Committing " + dluri + "to " + writepath)
    resp = requests.get(url=dluri, proxies=config.proxy, timeout=5, stream=True)
    with open(writepath, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
    return writepath


# Main method in the module, when called will create folder structure and
# download files for URIs passed to it  
def go(dluri, sourcepath=config.sourcepath, destpath=config.destinationpath):
    checkdestpath()
    path = pathdef(dluri)
    temppath = localdir(path)
    x = temppath[0]
    y = temppath[1]
    if x and y == '':
        print("Blank URI skipping")
    elif x == "\\":
        writepath = x + y
        writethefile(writepath, dluri)
    else:
        writepath = x + "\\" + y
        writethefile(writepath, dluri)

# Test execution
#testuri ='http://update.nai.com/products/commonupdater/current/lmasecore2000/mase_det.mcs'
#testuri2 ='http://update.nai.com/products/commonupdater/mase_det.mcs'
#testuri3 = ''
#go(testuri)
