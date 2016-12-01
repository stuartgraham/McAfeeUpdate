import defgrab

def process (soup):
    for link in soup.find_all('a'):
# drop the sorting and formatting links        
        if '?' in (link.get('href')) :
            continue
# drop the parent directory links            
        elif '..' in (link.get('href')) :
            continue
# find directories to recurse       
        elif '/' in (link.get('href')) :
#           fsbuild.folders(path) 
            print(link.get('href'))    
        else :
#           fsbuild.files(path)
            print(link.get('href'));
