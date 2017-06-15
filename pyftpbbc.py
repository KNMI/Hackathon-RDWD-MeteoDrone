# ftp to bbc

import json
import ftplib
from pprint import pprint
import StringIO
import re 
def poll_all(jsonconfig, pattern):
    with open(jsonconfig) as jsonf:
        ftpdata = json.loads(jsonf.read())

        ftp = ftplib.FTP( ftpdata['ftp']['server'] )

        # login based on account given.
        ftp.login(ftpdata['ftp']['user'] , ftpdata['ftp']['password'])

        ftp.cwd(ftpdata['ftp']['dir'])

        files = ftp.nlst()

        relevant_files = filter(lambda x: x.startswith(pattern), files)

        sio = StringIO.StringIO()

        # fetch all files matching the pattern
        for f in sorted(relevant_files):
            ftp.retrbinary("RETR " + f, callback=lambda data: sio.write(data))

        sio.seek(0)
        ftp.quit()
        return sio

def poll(jsonconfig, filename):
    with open(jsonconfig) as jsonf:
        ftpdata = json.loads(jsonf.read())

        ftp = ftplib.FTP( ftpdata['ftp']['server'] )

        # login based on account given.
        ftp.login(ftpdata['ftp']['user'] , ftpdata['ftp']['password'])

        ftp.cwd(ftpdata['ftp']['dir'])

        sio = StringIO.StringIO()

        # open(filename, 'wb').write
        # load ftp credentials (not public ask maarten or andrej) 
        def handle_binary(more_data):
            sio.write(more_data)
        
        resp = ftp.retrbinary("RETR " + filename, callback=handle_binary)

        sio.seek(0) # Go back to the start
        ftp.quit()

        return sio

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
 
