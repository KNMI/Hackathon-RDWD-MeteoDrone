# ftp to bbc

import json
import ftplib
from pprint import pprint
import StringIO

# load ftp credentials (not public ask maarten or andrej) 

def poll():
    with open('ftp.json') as jsonf:
        ftpdata = json.loads(jsonf.read())
        pprint(ftpdata['ftp'])

        ftp = ftplib.FTP( ftpdata['ftp']['server'] )

        # login based on account given.
        ftp.login(ftpdata['ftp']['user'] , ftpdata['ftp']['password'])

        ftp.cwd(ftpdata['ftp']['dir'])

        sio = StringIO.StringIO()

        # open(filename, 'wb').write
        def handle_binary(more_data):
            sio.write(more_data)

        filename = '20170608.txt'
        
        resp = ftp.retrbinary("RETR " + filename, callback=handle_binary )

        sio.seek(0) # Go back to the start

        return sio #.read()

        # compression option
        #zippy = gzip.GzipFile(fileobj=sio)
        #uncompressed = zippy.read()

        ftp.quit()

def connect(ftpjson):
    with open(ftpjson) as jsonf:
        ftpdata = json.loads(jsonf.read())
        pprint(ftpdata['ftp'])

        ftp = ftplib.FTP( ftpdata['ftp']['server'] )

        # login based on account given.
        ftp.login(ftpdata['ftp']['user'] , ftpdata['ftp']['password'])

        ftp.cwd(ftpdata['ftp']['dir'])

        return ftpdata
        
def upload(ftp, file):
    ext = os.path.splitext(file)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + file, open(file))
    else:
        ftp.storbinary("STOR " + file, open(file, "rb"), 1024)
 

 def download(ftp, filename):
    try:
        ftp.retrbinary("RETR " + filename ,open(filename, 'wb').write)
    except:
        print "Error"
 
