# persistant polling
import pyftpbbc
import time
from datetime import timedelta, datetime
import json
from plot import preproc_and_plot
def monitor( interval=50 ):
    basetime = datetime(2017, 6, 13, 0, 0, 0, 0)
    metadata_radio = json.loads(open('metadata_radio.json').read())['metadata']['columns']
    metadata_cabauw = json.loads(open('metadata_cab.json').read())['metadata']['columns']

    data = pyftpbbc.poll(basetime.strftime('%Y%m%d') + '.txt').read()
    data_cab = pyftpbbc.poll(basetime.strftime('%Y%m%d') + '_cab.txt').read()

    preproc_and_plot(data, data_cab, basetime, metadata_radio, metadata_cabauw)
    time.sleep(interval)


for i in range(100):
	monitor(3)
