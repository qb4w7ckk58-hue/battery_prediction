import time

import pandas as pd
from api import put_aas_value

ass_key = open('key.txt', 'r').read().strip()
API_URL = "http://localhost:8081"
AAS_VALUE = "{}/submodels/" + ass_key + "/submodel-elements/{}"


df = pd.read_csv("discharge.csv")
df.sort_values(by=['id_cycle', 'Time'])

simu_get_config_value = lambda t: t.split(':')[1]

simu_config = open('simu_config.txt', 'r').read().split("\n")[1:]

Voltage_Mesure = simu_get_config_value(simu_config[0])
Current_Mesure = simu_get_config_value(simu_config[1])
Voltage_Charge = simu_get_config_value(simu_config[2])
Current_Charge = simu_get_config_value(simu_config[3])
Type = simu_get_config_value(simu_config[4])
Temperature_Ambiante = simu_get_config_value(simu_config[5])
Temperature_Mesure = simu_get_config_value(simu_config[6])
Capacity = simu_get_config_value(simu_config[7])
Temps = simu_get_config_value(simu_config[8])
Numero_Cycle = simu_get_config_value(simu_config[9])
Batterie = simu_get_config_value(simu_config[10])

if __name__ == "__main__":
	while True:
		for i in range(0,len(df)):
			put_aas_value(AAS_VALUE.format(API_URL, Voltage_Mesure), df["Voltage_measured"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Current_Mesure), df["Current_measured"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Voltage_Charge), df["Voltage_charge"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Current_Charge), df["Current_charge"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Type), df["type"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Temperature_Ambiante), df["ambient_temperature"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Temperature_Mesure), df["Temperature_measured"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Capacity), df["Capacity"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Temps), df["Time"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Numero_Cycle), df["id_cycle"][i])
			put_aas_value(AAS_VALUE.format(API_URL, Batterie), df["Battery"][i])
			time.sleep(1)