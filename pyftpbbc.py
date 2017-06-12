# ftp to bbc

import json
import ftplib
from pprint import pprint
import StringIO

# load ftp credentials (not public ask maarten or andrej) 
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

    print sio.read()

    # compression option
    #zippy = gzip.GzipFile(fileobj=sio)
    #uncompressed = zippy.read()

    ftp.quit()

