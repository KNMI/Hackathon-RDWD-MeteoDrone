# persistant polling
import pyftpbbc
import time
from datetime import timedelta, datetime
import json
from matplotlib import pyplot as plt

from plot import process_data, initialize_plot
basetime = datetime(2017, 6, 13, 0, 0, 0, 0)
metadata_radio = json.loads(open('metadata_radio.json').read())['metadata']['columns']
metadata_cabauw = json.loads(open('metadata_cab.json').read())['metadata']['columns']

def monitor( interval=50 ):
    data = pyftpbbc.poll(basetime.strftime('%Y%m%d') + '.txt').read()
    data_cab = pyftpbbc.poll(basetime.strftime('%Y%m%d') + '_cab.txt').read()
    radio_data, cabauw_data = process_data(data, data_cab, basetime, metadata_radio, metadata_cabauw)
    time.sleep(interval)

initialize_plot()
while True:
	monitor(12)
