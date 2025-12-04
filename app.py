import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
import math

# --- CONFIGURAZIONE PAGINA (LIGHT & MINIMAL) ---
st.set_page_config(
    page_title="Gestione Turni | Minimal",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PER LOOK "ELEGANT & MINIMAL" ---
st.markdown("""
    <style>
    /* Sfondo e Testi Generali */
    .stApp {
        background-color: #ffffff;
        color: #333333;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: #111111 !important;
        font-weight: 600;
    }
    
    /* Card Statistiche (Stile Apple) */
    .stat-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    /* Bottoni */
    .stButton>button {
        background-color: #111111;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    
    /* Tabelle */
    .dataframe {
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI LOGICHE ---
def generate_date_range(start_date, num_days):
    return [start_date + timedelta(days=i) for i in range(num_days)]

def calculate_work_target(total_days, weekly_rest, vacation_days_count):
    weeks_covered = total_days / 7
    total_rest_needed = round(weeks_covered * weekly_rest)
    work_target = total_days - total_rest_needed - vacation_days_count
    return max(0, work_target), total_rest_needed

def generate_schedule(staff_data, date_list):
    schedule = []
    work_counts = {name: 0 for name in staff_data.keys()}
    targets = {}
    
    # Calcolo target
    for name, data in staff_data.items():
        work_target, _ = calculate_work_target(
            len(date_list), data['weekly_rest'], len(data['ferie'])
        )
        targets[name] = work_target

    # Algoritmo assegnazione
    for current_day in date_list:
        candidates = []
        for name, data in staff_data.items():
            if current_day in data['ferie']: continue
            if current_day in data['indisponibilita']: continue
            if work_counts[name] >= targets[name]: continue
            candidates.append(name)
        
        status = "⚠️ SCOPERTO"
        if candidates:
            # Ordina per chi ha lavorato meno e mischia i pari merito
            candidates.sort(key=lambda x: work_counts[x])
            min_val = work_counts[candidates[0]]
            best_candidates = [c for c in candidates if work_counts[c] == min_val]
            
            chosen = random.choice(best_candidates)
            work_counts[chosen] += 1
            status = chosen
            
        schedule.append({
            "Data": current_day,
            "Giorno": current_day.strftime("%A"),
            "Turno": status
        })
            
    return schedule, work_counts, targets

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.markdown("### 🛠️ Configurazione")
    st.markdown("---")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Inizio", date.today())
    with col_d2:
        duration_days = st.number_input("Giorni", 7, 365, 30)
        
    date_range = generate_date_range(start_date, duration_days)
    
    st.markdown("### 👥 Team")
    staff_input = st.text_area("Inserisci nomi", "Andrea\nLuca\nSofia\nChiara", height=150)
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]
    
    st.markdown("---")
    st.caption(f"Periodo: **{len(date_range)} giorni**")

# --- MAIN PAGE ---
st.title("Gestione Turni")
st.markdown("Pianificazione intelligente minimalista.")
st.markdown("<br>", unsafe_allow_html=True) # Spacer

if not staff_names:
    st.info("👈 Inizia aggiungendo i membri del team nella barra laterale.")
    st.stop()

# --- CONFIGURAZIONE STAFF (EXPANDERS PULITI) ---
st.subheader("Parametri Individuali")

# Creiamo un dizionario per raccogliere i dati
staff_data = {}

cols = st.columns(3) # Layout a griglia per risparmiare spazio verticale
for i, name in enumerate(staff_names):
    # Distribuisce i membri su 3 colonne
    with cols[i % 3]:
        with st.expander(f"⚙️ **{name}**", expanded=False):
            # Riposi
            w_rest = st.number_input(f"Riposi/Settimana", 0, 7, 2, key=f"wr_{name}")
            
            # Ferie e Indisponibilità
            leaves = st.multiselect("🌴 Ferie/Malattia", date_range, format_func=lambda x: x.strftime('%d/%m'), key=f"lv_{name}")
            unavail = st.multiselect("🚫 Indisp. Specifica", [d for d in date_range if d not in leaves], format_func=lambda x: x.strftime('%d/%m'), key=f"un_{name}")
            
            # Preview Target
            weeks = duration_days/7
            tot_rest = round(weeks * w_rest)
            target = duration_days - tot_rest - len(leaves)
            st.caption(f"Target: lavorerà circa **{max(0, target)}** giorni.")
            
            staff_data[name] = {'weekly_rest': w_rest, 'ferie': leaves, 'indisponibilita': unavail}

st.markdown("---")

# --- AZIONE ---
if st.button("Genera Pianificazione", type="primary", use_container_width=True):
    
    sched, counts, targets = generate_schedule(staff_data, date_range)
    df = pd.DataFrame(sched)
    
    # Traduzione Giorni
    it_days = {'Monday':'Lunedì','Tuesday':'Martedì','Wednesday':'Mer
