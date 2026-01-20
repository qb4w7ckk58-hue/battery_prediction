import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


def create_and_train_model():
	df = pd.read_csv('discharge.csv')
	
	max_cycle = df['id_cycle'].max()
	df['RUL'] = max_cycle - df['id_cycle']
	
	print(f"--- Données préparées ---")
	print(f"Cycle Max détecté : {max_cycle}")
	print(df.head())
	
	features = ['Capacity', 'Voltage_measured', 'Temperature_measured', 'Current_measured', "Time"]
	X = df[features]
	y = df['RUL']
	
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
	
	model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
	model.fit(X_train, y_train)
	
	predictions = model.predict(X_test)
	mae = mean_absolute_error(y_test, predictions)
	r2 = r2_score(y_test, predictions)
	
	print(f"\n--- Performance du Modèle ---")
	print(f"Erreur Moyenne (MAE) : {mae:.2f} cycles")
	print(f"Score R² : {r2:.4f} (proche de 1 = excellent)")
	
	joblib.dump(model, 'rul_model.pkl')
	joblib.dump(features, 'features_list.pkl')
	
	print("\nFichier 'rul_model.pkl' généré avec succès.")


if __name__ == "__main__":
	create_and_train_model()