import time
import requests
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from api import read_aas_value, put_aas_value
from prediction_module import *

# =========================
# Configuration & Style
# =========================
st.set_page_config(page_title="Battery Digital Twin", layout="wide")

st.markdown("""
	<style>
	[data-testid="column"] {
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	[data-testid="stMetricValue"] { font-size: 24px; color: #007BFF; }
	#MainMenu {visibility: hidden;}
	header {visibility: hidden;}
	footer {visibility: hidden;}
	</style>
	""", unsafe_allow_html=True)

# =========================
# Constantes
# =========================
LOCAL_HOST = "127.0.0.1"
API_REST_URL = "http://" + LOCAL_HOST + ":8000/predict"
AAS_URL_DEFAULT = "http://" + LOCAL_HOST + ":8081"
ass_key = open(r"C:\Users\AMA\PycharmProjects\IHM_ASS_Battery\key.txt", 'r').read().strip()
AAS_PATH = "{}/submodels/" + ass_key + "/submodel-elements/{}"
server_thread = APIThread(host=LOCAL_HOST, port=8000)
server_thread.start()

# =========================
# Initialisation du Session State
# =========================
if "history" not in st.session_state:
	st.session_state.history = {k: [] for k in ["capacity", "voltage", "current", "temperature", "cycle_time", "id_cycle"]}

# Nouveau : Stockage de TOUS les cycles pour le Tab 4
if "all_cycles_data" not in st.session_state:
	st.session_state.all_cycles_data = {}

if "previous_id_cycle" not in st.session_state:
	st.session_state.previous_id_cycle = -1

if "estimated_rul" not in st.session_state:
	st.session_state.estimated_rul = 1000

if "sim_estimated_rul" not in st.session_state:
	st.session_state.sim_estimated_rul = 1000

# Initialiser les valeurs de simulation
if "sim_voltage" not in st.session_state:
	st.session_state.sim_voltage = 0.0
if "sim_current" not in st.session_state:
	st.session_state.sim_current = 0.0
if "sim_temperature" not in st.session_state:
	st.session_state.sim_temperature = 0.0
if "sim_time" not in st.session_state:
	st.session_state.sim_time = 0.0
if "sim_capacity" not in st.session_state:
	st.session_state.sim_capacity = 0.0
if "sim_cycle_id" not in st.session_state:
	st.session_state.sim_cycle_id = 0


# =========================
# Fonctions UI & Visualisation
# =========================
def draw_battery_icon(percentage, health_ok):
	color = "#28a745" if percentage > 50 else "#ffc107" if percentage > 20 else "#dc3545"
	if not health_ok:
		color = "#6c757d"
	
	html = f"""
	<div style="display: flex; align-items: center; justify-content: center; flex-direction: column;">
	   <p style="font-weight: bold; margin-bottom: 5px;">Health: {"Good" if health_ok else "Bad"}</p>
	   <div style="border: 4px solid #333; border-radius: 8px; width: 100px; height: 50px; position: relative; padding: 4px;">
		  <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 2px; transition: width 0.5s;"></div>
		  <div style="background-color: #333; width: 8px; height: 25px; position: absolute; right: -12px; top: 9px; border-radius: 0 4px 4px 0;"></div>
	   </div>
	   <p style="font-weight: bold; margin-top: 5px;">{percentage}%</p>
	</div>
	"""
	st.markdown(html, unsafe_allow_html=True)


def create_gauge(value, title, unit, min_val, max_val, color):
	fig = go.Figure(go.Indicator(
		mode="gauge+number",
		value=value,
		title={'text': f"{title} ({unit})", 'font': {'size': 14}},
		gauge={
			'axis': {'range': [min_val, max_val]},
			'bar': {'color': color},
			'steps': [{'range': [min_val, max_val], 'color': "#E8E8E8"}]
		}
	))
	fig.update_layout(height=180, margin=dict(l=20, r=20, t=80, b=10))
	return fig


# =========================
# Logique de Données
# =========================
def fetch_and_update(api_url, max_cap):
	try:
		raw_cap = float(read_aas_value(AAS_PATH.format(api_url, "Capacity")))
		data = {
			"raw_cap": raw_cap,
			"capacity": round((100 * raw_cap) / max_cap, 2) if max_cap > 0 else 0,
			"voltage": float(read_aas_value(AAS_PATH.format(api_url, "Voltage_measured"))),
			"current": float(read_aas_value(AAS_PATH.format(api_url, "Current_measured"))),
			"temperature": float(read_aas_value(AAS_PATH.format(api_url, "Temperature_measured"))),
			"cycle_time": float(read_aas_value(AAS_PATH.format(api_url, "Time"))),
			"id_cycle": int(read_aas_value(AAS_PATH.format(api_url, "id_cycle")))
		}
		
		# --- LOGIQUE DE STOCKAGE HISTORIQUE ---
		c_id = data["id_cycle"]
		if c_id not in st.session_state.all_cycles_data:
			st.session_state.all_cycles_data[c_id] = {k: [] for k in ["capacity", "voltage", "current", "temperature", "cycle_time"]}
		
		# On ajoute la donnée au dictionnaire global
		for key in ["capacity", "voltage", "current", "temperature", "cycle_time"]:
			st.session_state.all_cycles_data[c_id][key].append(data[key])
		
		# --- LOGIQUE TEMPS RÉEL (votre code existant) ---
		if data["id_cycle"] != st.session_state.previous_id_cycle:
			for key in st.session_state.history:
				st.session_state.history[key] = []
			st.session_state.previous_id_cycle = data["id_cycle"]
		
		# Append data
		for key in ["capacity", "voltage", "current", "temperature", "cycle_time", "id_cycle"]:
			st.session_state.history[key].append(data[key])
			if len(st.session_state.history[key]) > 100:
				st.session_state.history[key].pop(0)
		
		return data
	except Exception as e:
		st.error(f"Erreur API: {str(e)}")
		return None


# =========================
# Dashboard Principal
# =========================
st.header("🔋 Battery Simulation Dashboard", text_alignment="center")

sidebar, main = st.columns([1, 8])

with sidebar:
	st.subheader("⚙️ Configuration")
	api_url = st.text_input("AAS API URL", AAS_URL_DEFAULT)
	max_cap = st.number_input("Max Capacity (Ah)", value=2.0)
	max_cycle_id = st.number_input("Max Cycle ID", value=168)
	end_life_threshold = st.number_input("RUL threshold", value=100)
	update_freq = st.slider("Rafraîchissement (s)", 0.5, 5.0, 1.0)

with main:
	while True:
		data = fetch_and_update(api_url, max_cap)
		
		if data:
			# Calcul RUL
			predict_data = {
				"Capacity": data["raw_cap"],
				"Voltage_measured": data["voltage"],
				"Current_measured": data["current"],
				"Temperature_measured": data["temperature"],
				"Time": data["cycle_time"],
				"id_cycle": data["id_cycle"]
			}
			rul_predicted = requests.post(API_REST_URL, json=predict_data).json()["rul_predicted"]
			st.session_state.estimated_rul = min(st.session_state.estimated_rul, rul_predicted)
			put_aas_value(AAS_PATH.format(api_url, "RUL"), st.session_state.estimated_rul)
		# Affichage (utilise les données du session_state)
		if st.session_state.history["cycle_time"]:
			# Récupérer les dernières valeurs
			current_data = {
				"capacity": st.session_state.history["capacity"][-1],
				"voltage": st.session_state.history["voltage"][-1],
				"current": st.session_state.history["current"][-1],
				"temperature": st.session_state.history["temperature"][-1],
				"cycle_time": st.session_state.history["cycle_time"][-1],
				"id_cycle": st.session_state.history["id_cycle"][-1]
			}
			
			# Onglets
			tab1, tab2, tab3, tab4 = st.tabs(["📋 Données", "📊 Simulation", "📈 Graphics", "📈 Historics"])
			
			with tab1:
				# --- METRICS & BATTERY ICON ---
				st.subheader("Battery Current State", text_alignment="center")
				rul = int(max_cycle_id) - int(current_data['id_cycle'])
				battery_health = rul >= end_life_threshold
				draw_battery_icon(current_data['capacity'], battery_health)
				
				st.divider()
				
				st.subheader("Battery Current Data", text_alignment="center")
				col_m1, col_m2, col_m3 = st.columns(3)
				
				with col_m1:
					st.plotly_chart(
						create_gauge(current_data['voltage'], "Voltage", "V", 2, 4.5, "#1f77b4"),
						width='stretch',
						key="gauge_voltage"
					)
				
				with col_m2:
					st.plotly_chart(
						create_gauge(current_data['current'], "Current", "A", -5, 0, "#ff7f0e"),
						width='stretch',
						key="gauge_current"
					)
				
				with col_m3:
					st.plotly_chart(
						create_gauge(current_data['temperature'], "Temp.", "°C", 0, 50, "#d62728"),
						width='stretch',
						key="gauge_temperature"
					)
				
				col_n1, col_n2, col_n3 = st.columns(3)
				
				col_n1.metric("Cycle Time", f"{current_data['cycle_time']:.2f} s")
				col_n2.metric("Cycle ID", current_data['id_cycle'])
				col_n3.metric("Estimated RUL", f"{st.session_state.estimated_rul} cycles")
			
			with tab2:
				# Bouton pour charger les valeurs actuelles
				if st.button("🔄 Update with current values"):
					st.session_state.sim_voltage = current_data['voltage']
					st.session_state.sim_current = current_data['current']
					st.session_state.sim_temperature = current_data['temperature']
					st.session_state.sim_time = current_data['cycle_time']
					st.session_state.sim_capacity = data['raw_cap']
					st.session_state.sim_cycle_id = current_data['id_cycle']
				
				col_n1, col_n2, col_n3, col_n4 = st.columns(4)
				
				sim_voltage_measured = col_n1.number_input("Voltage", st.session_state.sim_voltage)
				sim_current_measured = col_n1.number_input("Current", st.session_state.sim_current)
				
				sim_temperature_measured = col_n2.number_input("Temperature", st.session_state.sim_temperature)
				sim_time = col_n2.number_input("Cycle Time", st.session_state.sim_time)
				
				sim_capacity = col_n3.number_input("Capacity", st.session_state.sim_capacity)
				sim_cycle_id = col_n3.number_input("Cycle ID", st.session_state.sim_cycle_id)
				
				# Calcul RUL
				sim_predict_data = {
					"Voltage_measured": sim_voltage_measured,
					"Current_measured": sim_current_measured,
					"Temperature_measured": sim_temperature_measured,
					"Capacity": sim_capacity,
					"Time": sim_time,
					"id_cycle": sim_cycle_id
				}
				sim_rul_predicted = requests.post(API_REST_URL, json=sim_predict_data).json()["rul_predicted"]
				sim_rul = min(st.session_state.sim_estimated_rul, sim_rul_predicted)
				col_n4.metric("RUL (Cycle)", f"{sim_rul} cycles")
			
			with tab3:
				# --- GRAPHIQUES ---
				fig = make_subplots(
					rows=2, cols=2,
					subplot_titles=("Voltage (V)", "Current (A)", "Temperature (°C)", "Capacity (%)")
				)
				
				conf = [
					("voltage", 1, 1, "#1f77b4"),
					("current", 1, 2, "#ff7f0e"),
					("temperature", 2, 1, "#d62728"),
					("capacity", 2, 2, "#2ca02c")
				]
				
				for key, r, c, color in conf:
					fig.add_trace(
						go.Scatter(
							x=st.session_state.history["cycle_time"],
							y=st.session_state.history[key],
							mode='lines',
							line=dict(color=color)
						),
						row=r, col=c
					)
				
				fig.update_layout(
					height=500,
					showlegend=False,
					margin=dict(l=10, r=10, t=30, b=10)
				)
				st.plotly_chart(fig, width='stretch', key="main_plots")
			
			with tab4:
				st.subheader("📚 Cycle History Analysis")
				
				if st.session_state.all_cycles_data:
					# 1. Sélection du cycle
					available_cycles = sorted(list(st.session_state.all_cycles_data.keys()), reverse=True)
					selected_cycle = st.selectbox("Select a cycle to inspect:", available_cycles, key="cycle_selector")
					
					# 2. Récupération des données du cycle choisi
					hist_data = st.session_state.all_cycles_data[selected_cycle]
					
					# 3. Affichage des métriques résumées du cycle
					col_h1, col_h2, col_h3 = st.columns(3)
					col_h1.metric("Max Temp", f"{max(hist_data['temperature']):.1f} °C")
					col_h2.metric("Min Voltage", f"{min(hist_data['voltage']):.2f} V")
					col_h3.metric("Final Capacity", f"{hist_data['capacity'][-1]:.2f} %")
					
					# 4. Graphiques du cycle sélectionné
					fig_hist = make_subplots(
						rows=2, cols=2,
						subplot_titles=("Voltage over Time", "Current over Time", "Temperature", "Capacity Fade")
					)
					
					h_conf = [
						("voltage", 1, 1, "#1f77b4", "Voltage (V)"),
						("current", 1, 2, "#ff7f0e", "Current (A)"),
						("temperature", 2, 1, "#d62728", "Temp (°C)"),
						("capacity", 2, 2, "#2ca02c", "Cap (%)")
					]
					
					for key, r, c, color, label in h_conf:
						fig_hist.add_trace(
							go.Scatter(
								x=hist_data["cycle_time"],
								y=hist_data[key],
								name=label,
								line=dict(color=color)
							),
							row=r, col=c
						)
					
					fig_hist.update_layout(height=600, showlegend=False,
										   title_text=f"Detailed Analysis: Cycle {selected_cycle}")
					st.plotly_chart(fig_hist, width='stretch')
					
					# Optionnel : Affichage de la tendance globale (Capacité vs Cycle ID)
					st.divider()
					st.subheader("📈 Global Degradation Trend")
					cycle_ids = sorted(list(st.session_state.all_cycles_data.keys()))
					final_caps = [st.session_state.all_cycles_data[i]["capacity"][-1] for i in cycle_ids]
					
					fig_trend = go.Figure()
					fig_trend.add_trace(go.Scatter(x=cycle_ids, y=final_caps, mode='lines+markers', name='SOH'))
					fig_trend.update_layout(height=300, xaxis_title="Cycle Number", yaxis_title="Final Capacity (%)")
					st.plotly_chart(fig_trend, width='stretch')
				
				else:
					st.info("No historical data recorded yet.")
		else:
			st.info("En attente de données...")
		
		time.sleep(update_freq)
		st.rerun()