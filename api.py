import requests


def read_aas_value(url, return_value=False):
	r = requests.get(url, timeout=5)
	r.raise_for_status()
	data = r.json()
	return (round(data["value"], 2) if isinstance(data["value"], float) else data["value"]) if isinstance(data, dict) and not return_value else data


def put_aas_value(url, value):
	try:
		json = read_aas_value(url, return_value=True)
		json["value"] = str(value)
		r = requests.put(url, json=json, timeout=5)
		r.raise_for_status()
		return True
	
	except requests.exceptions.RequestException as e:
		print(f"Erreur lors de la requête : {e}")
		return None


if __name__ == "__main__":
	r = requests.get("http://localhost:8081/submodels/aHR0cHM6Ly9leGFtcGxlLmNvbS9pZHMvc20vMjA1NF80MTcxXzExNDJfMDQ3OA/submodel-elements/RUL", timeout=5)
	r.raise_for_status()
	print(r.json())
	print(put_aas_value(
		"http://localhost:8081/submodels/aHR0cHM6Ly9leGFtcGxlLmNvbS9pZHMvc20vMjA1NF80MTcxXzExNDJfMDQ3OA/submodel-elements/RUL",
		81.25))