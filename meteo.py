import numpy as np

# Meteo stuff
def get_mixing_ratio(pressure, temperature):
	return np.divide(np.multiply(0.622, es(temperature)), np.subtract(pressure, es(temperature)))

def get_true_mixing_ratio(rel_hum_frac, pressure, temp):
	return rel_hum_frac * get_mixing_ratio(pressure, temp)

def virtual_temperature(temperature, rel_hum_frac, air_pressure):
	q = get_true_mixing_ratio(rel_hum_frac, air_pressure, temperature)
	return (1.0 + 0.609 * q) * temperature

def es(temperature) :
	return 6.11*np.exp(17.269*(np.subtract(temperature, 273.16))/(np.subtract(temperature, 35.86)))

def cpd(temperature):
	return 1005 + np.divide(np.subtract(temperature, 250) ** 2,  3364.0)

def getTheta(temperature, pressure):
	Rd = 287.04
	chi = np.divide(Rd, cpd(temperature))
	return np.multiply(temperature, np.power(np.divide(1000.0, pressure), chi))

def get_height(z1, theta1, p1, theta2, p2):
	# ; inputs
	# ; 1) z1 ; height of level 1 (m)
	# ; 2) theta1: virtual potential temperature at level 1 (K)
	# ; 3) p1: pressure at level 1 (hPa)
	# ; 4) theta2: virtual potential temeprature at level 2 (K)
	# ; 5) p2: pressure at level 2 (hPa)
	# ; outputs
	# ; 1) height: the height of level 2 (m)
	r = 287.0
	g = 9.8
	p21 = np.divide(p2, p1)
	t21 = np.divide(theta2, theta1)
	p21000 = np.divide(p2, 1000.0)
	p11000 = np.divide(p1, 1000.0)
	part1 = np.multiply(theta2, np.power(p21000, 0.286))
	part2 = np.multiply(theta1, np.power(p11000, 0.286))
	part3 = np.multiply(t21, np.power(p21, 0.286))
	result = z1 - (r/g)*(np.subtract(part1, part2))*np.log(p21)/np.log(part3)
	return result

def calculate_pressure(pressu,p1,thv1,z1,thv2,z2):
	g = 9.8
	cp = 1004.0
	if thv1 == thv2:
		RESULT = (p1 ** .286 + 1000.0 ** .286 * (g/cp) * (z1-z2)/thv1) ** (1.0 / 0.286)
	else:
		RESULT = (p1 ** .286 + 1000.0 ** .286 * (g/cp) * (z1-z2) * np.log(thv1/thv2) / (thv1-thv2)) ** (1.0/0.286)
	return RESULT

def calculate_height (air_pressure, temperature, rel_hum, initial_pressure): 
	# perform conversions for functions
	kelvin_temp = list(map(lambda x: x + 273.15, temperature))
	rel_hum_frac = rel_hum * 0.01

	qs = get_mixing_ratio(air_pressure, kelvin_temp)
	q = rel_hum_frac * qs
	virt_temp = virtual_temperature(kelvin_temp, rel_hum_frac, air_pressure)
	virtual_potential_temperature = getTheta(virt_temp, air_pressure)
	potential_temperature = getTheta(kelvin_temp, air_pressure)
	start_pressure = initial_pressure
	start_height = 0
	heights = [0]
	for i in range(len(potential_temperature) - 1):
		h = get_height(start_height, virtual_potential_temperature[i], start_pressure, virtual_potential_temperature[i + 1], air_pressure[i] + (1e-5 if air_pressure[i] == start_pressure else 0))
		heights.append(h)
		start_height = heights[-1]
		start_pressure = air_pressure[i]
	return (heights, potential_temperature, qs, q)
