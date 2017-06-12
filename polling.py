# persistant polling
import pyftpbbc
import time

def monitor( interval=50 ):
    #ftp = FTP(server)
    #ftp.login()
    #ftp.cwd(directory)
    print time.ctime()
    print len(pyftpbbc.poll().read())

    time.sleep(interval)


for i in range(100):
	monitor(1)