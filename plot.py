import numpy as np
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import json
from itertools import izip_longest
from meteo import calculate_height
# plotting stuff
def filter_time(time):
	# time should be increasing per package.
	# if the next sample has a higher time than the previous sample, discard it
	indices = np.where(time[:-1] > time[1:])[0]
	return list(map(lambda x: x + 1, indices))

# remove faulty data and transform timestamp to full date
def clean_data(data, basetime):
	dirty_indices = filter_time(data[0])
	arr = []
	for d in data:
		arr.append(np.delete(d, dirty_indices))
	arr[0] = list(map(lambda x: basetime + timedelta(seconds=x), arr[0]))
	return np.array(arr)

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

def parse_radio_data(data, metadata, basetime):
	time = np.array([])
	air_pressure = np.array([])
	temperature = np.array([])
	rel_hum = np.array([])
	height = np.array([])


	plt.clf()
	data = data.split()
	splitted = list(grouper(len(metadata), data))

	for line in splitted:
		t, pres, temp, rela_hum, h, lat, lon = line
		time = np.append(time, np.array(int(t)))
		air_pressure = np.append(air_pressure, np.array(float(pres)))
		temperature = np.append(temperature, np.array(float(temp)))
		rel_hum = np.append(rel_hum, np.array(float(rela_hum)))
		height = np.append(height, np.array(int(h)))
	
	dirty_indices = filter_time(time)
	time = np.delete(time, dirty_indices)
	air_pressure = np.delete(air_pressure, dirty_indices)
	temperature = np.delete(temperature, dirty_indices)
	rel_hum = np.delete(rel_hum, dirty_indices)
	height = np.delete(height, dirty_indices)
	time = list(map(lambda x: basetime + timedelta(seconds=x) , time))

	return (time, air_pressure, temperature, rel_hum, height)


def parse_cabauw_data(data, metadata, basetime):
	data = data.split()
	splitted = list(grouper(len(metadata), data))
	time = np.array([])
	wind_speed_10 = np.array([])
	wind_speed_20 = np.array([])
	wind_speed_40 = np.array([])
	wind_speed_80 = np.array([])
	wind_speed_140 = np.array([])
	wind_speed_200 = np.array([])

	wind_dir_10 = np.array([])
	wind_dir_20 = np.array([])
	wind_dir_40 = np.array([])
	wind_dir_80 = np.array([])
	wind_dir_140 = np.array([])
	wind_dir_200 = np.array([])

	air_temp_10 = np.array([])
	air_temp_20 = np.array([])
	air_temp_40 = np.array([])
	air_temp_80 = np.array([])
	air_temp_140 = np.array([])
	air_temp_200 = np.array([])

	dew_point_temp_10 = np.array([])
	dew_point_temp_20 = np.array([])
	dew_point_temp_40 = np.array([])
	dew_point_temp_80 = np.array([])
	dew_point_temp_140 = np.array([])
	dew_point_temp_200 = np.array([])

	relative_humidity_10 = np.array([])
	relative_humidity_20 = np.array([])
	relative_humidity_40 = np.array([])
	relative_humidity_80 = np.array([])
	relative_humidity_140 = np.array([])
	relative_humidity_200 = np.array([])

	visibility_10 = np.array([])
	visibility_20 = np.array([])
	visibility_40 = np.array([])
	visibility_80 = np.array([])
	visibility_140 = np.array([])
	visibility_200 = np.array([])

	air_pressure = np.array([])

	for observation in splitted:
		secs_passed = int(observation[0])
		time = np.append(time, secs_passed)
		wind_speed_token = observation[1]
		assert(wind_speed_token == 'ws')
		wind_speed_10 = np.append(wind_speed_10, float(observation[2]))
		wind_speed_20 = np.append(wind_speed_20, float(observation[3]))
		wind_speed_40 = np.append(wind_speed_40, float(observation[4]))
		wind_speed_80 = np.append(wind_speed_80, float(observation[5]))
		wind_speed_140 = np.append(wind_speed_140, float(observation[6]))
		wind_speed_200 = np.append(wind_speed_200, float(observation[7]))

		wind_dir_token = observation[8]
		assert(wind_dir_token == 'wr')
		wind_dir_10 = np.append(wind_dir_10, float(observation[9]))
		wind_dir_20 = np.append(wind_dir_20, float(observation[10]))
		wind_dir_40 = np.append(wind_dir_40, float(observation[11]))
		wind_dir_80 = np.append(wind_dir_80, float(observation[12]))
		wind_dir_140 = np.append(wind_dir_140, float(observation[13]))
		wind_dir_200 = np.append(wind_dir_200, float(observation[14]))

		air_temp_token = observation[15]
		assert(air_temp_token == 'ta')
		air_temp_10 = np.append(air_temp_10, float(observation[16]))
		air_temp_20 = np.append(air_temp_20, float(observation[17]))
		air_temp_40 = np.append(air_temp_40, float(observation[18]))
		air_temp_80 = np.append(air_temp_80, float(observation[19]))
		air_temp_140 = np.append(air_temp_140, float(observation[20]))
		air_temp_200 = np.append(air_temp_200, float(observation[21]))

		dew_point_temp_token = observation[22]
		assert(dew_point_temp_token == 'td')
		dew_point_temp_10 = np.append(dew_point_temp_10, float(observation[23]))
		dew_point_temp_20 = np.append(dew_point_temp_20, float(observation[24]))
		dew_point_temp_40 = np.append(dew_point_temp_40, float(observation[25]))
		dew_point_temp_80 = np.append(dew_point_temp_80, float(observation[26]))
		dew_point_temp_140 = np.append(dew_point_temp_140, float(observation[27]))
		dew_point_temp_200 = np.append(dew_point_temp_200, float(observation[28]))

		relative_humidity_token = observation[29]
		assert(relative_humidity_token == 'rh')
		relative_humidity_10 = np.append(relative_humidity_10, int(observation[30]))
		relative_humidity_20 = np.append(relative_humidity_20, int(observation[31]))
		relative_humidity_40 = np.append(relative_humidity_40, int(observation[32]))
		relative_humidity_80 = np.append(relative_humidity_80, int(observation[33]))
		relative_humidity_140 = np.append(relative_humidity_140, int(observation[34]))
		relative_humidity_200 = np.append(relative_humidity_200, int(observation[35]))

		visibility_token = observation[36]
		assert(visibility_token == 'zm')
		visibility_10 = np.append(visibility_10, float(observation[37]))
		visibility_20 = np.append(visibility_20, float(observation[38]))
		visibility_40 = np.append(visibility_40, float(observation[39]))
		visibility_80 = np.append(visibility_80, float(observation[40]))
		visibility_140 = np.append(visibility_140, float(observation[41]))
		visibility_200 = np.append(visibility_200, float(observation[42]))

		air_pressure_token = observation[43]
		air_pressure = np.append(air_pressure, float(observation[44]))

	# print observation
	time = list(map(lambda x: basetime + timedelta(seconds=x) , time))
	wind_speed = {
		10: wind_speed_10,
		20: wind_speed_20,
		40: wind_speed_40,
		80: wind_speed_80,
		140: wind_speed_140,
		200: wind_speed_200
	}
	wind_dir = {
		10: wind_dir_10,
		20: wind_dir_20,
		40: wind_dir_40,
		80: wind_dir_80,
		140: wind_dir_140,
		200: wind_dir_200
	}
	air_temp = {
		10: air_temp_10,
		20: air_temp_20,
		40: air_temp_40,
		80: air_temp_80,
		140: air_temp_140,
		200: air_temp_200
	}
	dew_point_temp = {
		10: dew_point_temp_10,
		20: dew_point_temp_20,
		40: dew_point_temp_40,
		80: dew_point_temp_80,
		140: dew_point_temp_140,
		200: dew_point_temp_200
	}
	relative_humidity = {
		10: relative_humidity_10,
		20: relative_humidity_20,
		40: relative_humidity_40,
		80: relative_humidity_80,
		140: relative_humidity_140,
		200: relative_humidity_200
	}
	visibility = {
		10: visibility_10,
		20: visibility_20,
		40: visibility_40,
		80: visibility_80,
		140: visibility_140,
		200: visibility_200
	}
	
	return time, wind_speed, wind_dir, air_temp, dew_point_temp, relative_humidity, visibility, air_pressure

def preproc_and_plot(data, data_cabauw, basetime, metadata, metadata_cabauw):
	time, air_pressure, temperature, rel_hum, height = parse_radio_data(data, metadata, basetime)
	time_c, wind_speeds_c, wind_directions_c, air_temperatures_c, dew_point_temperatures_c, relative_humidities_c, visibilities_c, air_pressures_c = parse_cabauw_data(data_cabauw, metadata_cabauw, basetime)
	plot(basetime, metadata, time, air_pressure, temperature, rel_hum, height, time_c, wind_speeds_c, wind_directions_c, air_temperatures_c, dew_point_temperatures_c, relative_humidities_c, visibilities_c, air_pressures_c)

def plot(basetime, metadata, time, air_pressure, temperature, rel_hum, height, time_c, wind_speeds_c, wind_directions_c, air_temperatures_c, dew_point_temperatures_c, relative_humidities_c, visibilities_c, air_pressures_c):
	# Calulate height for data
	(heights, potential_temperature) = calculate_height(air_pressure, temperature, rel_hum, 1010.75)
	print('Height (GPS): ', height[-1])
	print('Height (calc): ', heights[-1])
	i = 1
	plt.subplot(321)
	plt.plot(time, air_pressure)
	plt.plot(time_c, air_pressures_c)
	plt.ylabel(metadata[i]['units'])
	plt.xlabel('Time')
	plt.title(metadata[i]['name'])

	i = 2
	plt.subplot(322)
	plt.plot(time, temperature)
	plt.plot(time_c, air_temperatures_c[10])
	plt.plot(time_c, air_temperatures_c[20])
	plt.plot(time_c, air_temperatures_c[40])
	plt.plot(time_c, air_temperatures_c[80])
	plt.plot(time_c, air_temperatures_c[140])
	plt.plot(time_c, air_temperatures_c[200])
	# plt.plot(time, potential_temperature)
	plt.ylabel(metadata[i]['units'])
	plt.xlabel('Time')
	plt.title(metadata[i]['name'])

	i = 3
	plt.subplot(323)
	plt.plot(time, rel_hum)
	plt.plot(time_c, relative_humidities_c[10])
	plt.plot(time_c, relative_humidities_c[20])
	plt.plot(time_c, relative_humidities_c[40])
	plt.plot(time_c, relative_humidities_c[80])
	plt.plot(time_c, relative_humidities_c[140])
	plt.plot(time_c, relative_humidities_c[200])

	plt.ylabel(metadata[i]['units'])
	plt.xlabel('Time')
	plt.title(metadata[i]['name'])

	i = 4
	plt.subplot(324)
	plt.plot(time, np.abs(np.subtract(height, heights)), 'ro')
	plt.title('Absolute error between GPS and calculated')
	plt.ylabel(metadata[i]['units'])
	plt.xlabel('Time')

	plt.subplot(325)
	# plt.plot(temperature, heights)
	plt.plot(air_temperatures_c[10], [10] * len(air_temperatures_c[10]))
	plt.plot(air_temperatures_c[20], [20] * len(air_temperatures_c[10]))
	plt.plot(air_temperatures_c[40], [40] * len(air_temperatures_c[10]))
	plt.plot(air_temperatures_c[80], [80] * len(air_temperatures_c[10]))
	plt.plot(air_temperatures_c[140], [140] * len(air_temperatures_c[10]))
	plt.plot(air_temperatures_c[200], [200] * len(air_temperatures_c[10]))

	plt.title('Temp/Height profile')
	plt.ylabel('Height')
	plt.xlabel('Temperature')

	plt.subplot(326)
	plt.plot(potential_temperature, heights)
	plt.title('Temp/Height profile')
	plt.ylabel('Height')
	plt.xlabel('Potential temperature')
	plt.show(block=False)
	plt.pause(0.0001)
