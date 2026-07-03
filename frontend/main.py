import streamlit as st
import requests
import os

# Configuration de l'API
# "backend" est le nom du service dans Docker Compose
API_URL = os.getenv("API_URL")

st.set_page_config(page_title="Flight Price Finder", page_icon="✈️", layout="wide")


st.markdown("""<style>.hero {text-align:center; padding: 2.2rem 0 1rem 0;} ... </style>""", unsafe_allow_html=True)
st.markdown("""<div class="hero"><h1>✈️ Flight Price Finder ✈️</h1></div>""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
      .hero {text-align:center; padding: 2.2rem 0 1rem 0;}
      .hero h1 {font-size: 2.2rem; margin-bottom: .2rem;}
      .hero p {opacity:.75; margin-top: 0;}
      .pill {
        display:inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        font-size: 0.85rem;
        opacity: .85;
        margin-right: 6px;
        margin-bottom: 6px;
      }
      .bigprice {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        margin: .2rem 0 .2rem 0;
      }
      .subtle {opacity:.75}
      .searchwrap {
        max-width: 920px;
        margin: 0 auto;
      }
      .stButton>button {
        border-radius: 12px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 700 !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

AIRLINES = ["Indigo", "Air_India", "Vistara", "SpiceJet", "GO_FIRST", "AirAsia"]
CITIES = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"]
TIME_BANDS = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]
STOPS_LABEL_TO_NUM = {"zero": 0, "one": 1, "two_or_more": 2}
CLASS_LABEL_TO_NUM = {"Economy": 0, "Business": 1}

# ---------- Bloc central (barre de recherche / formulaire) ----------
st.markdown('<div class="searchwrap">', unsafe_allow_html=True)
with st.container():

    c1, c2, c3 = st.columns([1.1, 1.1, 1], vertical_alignment="bottom")
    with c1:
        source_city = st.selectbox("Départ", CITIES, index=0)
    with c2:
        destination_city = st.selectbox("Arrivée", CITIES, index=1)
    with c3:
        class_label = st.segmented_control("Classe", options=["Economy", "Business"], default="Economy")

    c4, c5, c6, c7 = st.columns([1, 1, 1, 1], vertical_alignment="bottom")
    with c4:
        airline = st.selectbox("Compagnie", AIRLINES, index=0)
    with c5:
        stops_label = st.selectbox("Escales", ["zero", "one", "two_or_more"], index=0)
    with c6:
        days_left = st.slider("Jours avant le vol", min_value=1, max_value=60, value=15)
    with c7:
        duration = st.number_input("Durée (heures)", min_value=0.5, max_value=60.0, value=2.5, step=0.5)

    c8, c9 = st.columns([1, 1], vertical_alignment="bottom")
    with c8:
        departure_time = st.selectbox("Créneau départ", TIME_BANDS, index=1)
    with c9:
        arrival_time = st.selectbox("Créneau arrivée", TIME_BANDS, index=3)

    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
    run = st.button("🔎 Rechercher le meilleur prix", width='stretch')

st.markdown("</div>", unsafe_allow_html=True)

# Appel à l'API
if run:
    if source_city == destination_city:
        st.warning("Départ et arrivée identiques !")
    else:
        # On prépare le JSON à envoyer
        payload = {
            "airline": airline,
            "source_city": source_city,
            "destination_city": destination_city,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration": duration,
            "days_left": days_left,
            "stops_label": stops_label,
            "class_label": class_label
        }

        try:
            with st.spinner("Interrogation de l'IA..."):
                # C'EST ICI QUE ÇA CHANGE : Appel HTTP au lieu de joblib
                response = requests.post(f"{API_URL}/predict", json=payload)
            
            if response.status_code == 200:
                price = response.json()["estimated_price"]
                st.success(f"Prix estimé : ₹ {price:,.0f}")
            else:
                st.error(f"Erreur API : {response.text}")
        
        except requests.exceptions.ConnectionError:
            st.error("Impossible de contacter le Backend. Est-il allumé ?")