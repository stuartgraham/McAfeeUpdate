import os
import config
# Establish Directory
# Establish Destination
# Establish if timestamp match
# Download if no match
# Log

def pathdef (uri, sourcepath=config.sourcepath):
    path = uri.replace(sourcepath, "")
    return path

def localdir (path, destinationpath=config.destinationpath):
    directory = path.split("/")
    directory.pop(0)
    directory.pop(-1)
    depth = 0
#    print(directory)
    for i in directory:
#        print(str(depth) + ',' + i)
        if depth == 0:
            workingpath = i
        else:
# not sure what +1 is needed
            workingpath = "\\".join(directory[0:depth+1])
#       print(workingpath)
        depth += 1
        mkpath = (destinationpath + "\\" + workingpath)
        print(mkpath)
        try:
            os.mkdir(mkpath)
        except OSError:
            print(OSError.value)
            pass



#def processfile (dlurl, sourcepath=config.sourcepath, destpath=config.destinationpath):

localdir('/mail/test/path/iamhere/test.html')
