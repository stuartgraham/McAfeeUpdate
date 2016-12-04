import os
import config
# Establish Directory
# Establish Destination
# Establish if timestamp match
# Download if no match
# Log

# Module will check existance of the base destination path from config
# and create as needed
def checkdestpath (destinationpath=config.destinationpath):
    if not os.path.exists(destinationpath):
        try:
            os.mkdir(destinationpath)
            print(destinationpath + " was created")
        except OSError as err:
            print(err)
            pass
        else:
            print(destinationpath + "already exists")

# Module strips the sourcepath defined in config.py from the URI
def pathdef (uri, sourcepath=config.sourcepath):
    path = uri.replace(sourcepath, "")
    return path

# Module will test and create the directory structure for the file
# as needed
def localdir (path, destinationpath=config.destinationpath):
    directory = path.split("/")
    directory.pop(0)
    filename = directory[-1]
    directory.pop(-1)
    depth = 0
    for i in directory:
        if depth == 0:
            workingpath = i
        else:
# not sure what +1 is needed
            workingpath = "\\".join(directory[0:depth+1])
#       print(workingpath)
        depth += 1
        mkpath = (destinationpath + "\\" + workingpath)
        if not os.path.exists(mkpath):
            try:
                os.mkdir(mkpath)
                print(mkpath + " was created")
            except OSError as err:
                print(err)
            pass
        else:
            print(mkpath + "already exists")
    return filename, mkpath


def processfile (dluri, sourcepath=config.sourcepath, destpath=config.destinationpath):
    checkdestpath()
    path = pathdef(dluri)
    z = localdir(path)



# Test execution
#test2 = localdir('/mail/test/path/iamhere/test.html')
#print(test2[0])
#print(test2[1])
