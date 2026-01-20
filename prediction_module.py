import threading
import uvicorn
import joblib
import pandas as pd
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Configuration des chemins ---
MODEL_PATH = r"C:\Users\AMA\PycharmProjects\IHM_ASS_Battery\rul_model.pkl"
FEATURES_PATH = r"C:\Users\AMA\PycharmProjects\IHM_ASS_Battery\features_list.pkl"

# --- Initialisation de l'application FastAPI ---
app = FastAPI(
	title="API de Prédiction RUL & Monitoring",
	description="Interface REST pour la prédiction de durée de vie en temps réel.",
	version="1.0.0"
)


# --- Modèles de données Pydantic ---
class BatteryData(BaseModel):
	Capacity: float
	Voltage_measured: float
	Temperature_measured: float
	Current_measured: float
	Time: float
	id_cycle: int


class PredictionResponse(BaseModel):
	rul_predicted: int
	status: str


# --- Chargement des ressources (Modèle et Features) ---
def load_resources():
	try:
		if not os.path.exists(MODEL_PATH) or not os.path.exists(FEATURES_PATH):
			return None, None
		model = joblib.load(MODEL_PATH)
		features = joblib.load(FEATURES_PATH)
		return model, features
	except Exception:
		return None, None


model, features_order = load_resources()


# --- Endpoints de l'API ---
@app.get("/")
def health_check():
	return {"status": "online", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictionResponse)
def predict(data: BatteryData):
	if model is None:
		raise HTTPException(status_code=500, detail="Modèle non disponible.")
	
	try:
		# Transformation en DataFrame avec respect de l'ordre des colonnes
		input_df = pd.DataFrame([data.dict()])
		X = input_df[features_order]
		
		# Prédiction et post-traitement
		prediction = model.predict(X)[0]
		rul_final = max(0, int(round(prediction)))
		
		return {"rul_predicted": rul_final, "status": "success"}
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


# --- Classe Threading pour le serveur Uvicorn ---
class APIThread(threading.Thread):
	def __init__(self, host="127.0.0.1", port=8000):
		super().__init__()
		self.config = uvicorn.Config(app=app, host=host, port=port, log_level="error")
		self.server = uvicorn.Server(config=self.config)
		self.daemon = True  # Le thread s'arrête si le programme principal s'arrête
	
	def run(self):
		self.server.run()
	
	def stop(self):
		self.server.should_exit = True


# --- Programme Principal ---
if __name__ == "__main__":
	# 1. Lancement de l'API dans un thread séparé
	server_thread = APIThread(host="127.0.0.1", port=8000)
	server_thread.start()
	
	print(">>> API REST lancée sur http://127.0.0.1:8000")
	print(">>> Système de contrôle actif et prêt.")
	
	try:
		# 2. Simulation de la boucle de contrôle principale (ex: surveillance éolienne)
		# Cette boucle continue de tourner parallèlement à l'API
		while True:
			# Ici on pourrait placer la logique d'arbitrage entre Lidar et girouette
			# ou la gestion des moteurs de yaw[cite: 34].
			pass
	
	except KeyboardInterrupt:
		print("\nArrêt du système...")
		server_thread.stop()