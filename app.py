import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
import math

# --- CONFIGURAZIONE PAGINA (SPATIAL UI) ---
st.set_page_config(
    page_title="TurniMaster 3000",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO PER LOOK "SPAZIALE" ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #41424C;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    h1, h2, h3 {
        color: #00e5ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI UTILITÀ ---
def generate_date_range(start_date, num_days):
    return [start_date + timedelta(days=i) for i in range(num_days)]

def calculate_work_target(total_days, weekly_rest, vacation_days_count):
    # Calcolo proporzionale: (Giorni totali / 7) * Riposi settimanali
    weeks_covered = total_days / 7
    total_rest_needed = round(weeks_covered * weekly_rest)
    
    # Target Lavorativi = Totale Giorni - Riposi Calcolati - Ferie Specificate
    work_target = total_days - total_rest_needed - vacation_days_count
    return max(0, work_target), total_rest_needed

def generate_schedule(staff_data, date_list):
    schedule = []
    
    # Inizializza contatori
    work_counts = {name: 0 for name in staff_data.keys()}
    
    # Calcolo obiettivi per ogni persona
    targets = {}
    for name, data in staff_data.items():
        work_target, rest_calc = calculate_work_target(
            len(date_list), 
            data['weekly_rest'], 
            len(data['ferie'])
        )
        targets[name] = work_target

    for current_day in date_list:
        day_str = current_day.strftime("%Y-%m-%d")
        candidates = []
        
        for name, data in staff_data.items():
            # 1. Controllo Ferie (Malattia/Ferie)
            if current_day in data['ferie']:
                continue
            
            # 2. Controllo Indisponibilità (Non posso, ma non è ferie)
            if current_day in data['indisponibilita']:
                continue
            
            # 3. Controllo Target Lavorativo
            if work_counts[name] >= targets[name]:
                continue
                
            candidates.append(name)
        
        # Selezione
        if candidates:
            # Ordina per chi ha lavorato meno (Equity) e aggiungi casualità
            candidates.sort(key=lambda x: work_counts[x])
            min_shifts = work_counts[candidates[0]]
            best_options = [c for c in candidates if work_counts[c] == min_shifts]
            
            chosen = random.choice(best_options)
            work_counts[chosen] += 1
            status = chosen
        else:
            status = "⚠️ SCOPERTO"
            
        schedule.append({
            "Data": current_day,
            "Giorno": current_day.strftime("%A"), # Nome giorno (es. Monday)
            "Assegnato": status
        })
            
    return schedule, work_counts, targets

# --- SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.title("🛸 Configurazione")
    
    st.subheader("1. Periodo Temporale")
    start_date = st.date_input("Data Inizio", date.today())
    duration_days = st.number_input("Durata (Giorni)", min_value=1, value=30, step=1)
    
    date_range = generate_date_range(start_date, duration_days)
    end_date = date_range[-1]
    
    st.info(f"🗓️ Dal: **{start_date.strftime('%d/%m')}**\n\nAl: **{end_date.strftime('%d/%m')}**")
    
    st.subheader("2. Squadra")
    staff_input = st.text_area("Nomi Staff (uno per riga)", "Mario\nLuigi\nPeach\nToad")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# --- MAIN INTERFACE ---
st.title("🚀 TurniMaster Space Edition")
st.markdown("Generatore di turni con calcolo proporzionale dei riposi.")

if not staff_names:
    st.warning("Inserisci almeno un nome nella barra laterale!")
    st.stop()

# --- INPUT DETTAGLI (Layout a griglia) ---
st.subheader("⚙️ Parametri Staff")
staff_data = {}

# Usiamo i tabs per salvare spazio se sono tanti, o expander
for name in staff_names:
    with st.expander(f"👤 Configura: {name}", expanded=False):
        c1, c2, c3 = st.columns([1, 2, 2])
        
        with c1:
            st.markdown(f"**{name}**")
            # Riposi settimanali
            weekly_rest = st.number_input(
                f"Riposi a Settimana", 
                min_value=0, max_value=7, value=2, 
                key=f"rest_{name}",
                help="Quanti giorni di riposo a settimana deve avere?"
            )
            # Preview calcolo
            weeks = duration_days / 7
            total_rest = round(weeks * weekly_rest)
            st.caption(f"Su {duration_days} giorni ≈ **{total_rest}** riposi totali.")

        with c2:
            # Ferie / Malattia (Questi giorni vengono SOTTRATTI dal monte ore lavorabile)
            leaves = st.multiselect(
                "🤒 Ferie / Malattia (Assenze Giustificate)",
                options=date_range,
                format_func=lambda x: x.strftime('%d/%m %a'),
                key=f"leaves_{name}"
            )

        with c3:
            # Indisponibilità (Non posso lavorare, ma devo recuperare il turno altrove)
            unavailable = st.multiselect(
                "🚫 Indisponibilità (Preferenze)",
                options=[d for d in date_range if d not in leaves],
                format_func=lambda x: x.strftime('%d/%m %a'),
                key=f"unav_{name}"
            )
            
        staff_data[name] = {
            'weekly_rest': weekly_rest,
            'ferie': leaves,
            'indisponibilita': unavailable
        }

st.markdown("---")

# --- GENERAZIONE ---
if st.button("✨ CALCOLA TURNI INTERSTELLARI", type="primary", use_container_width=True):
    
    final_schedule, worked_stats, target_stats = generate_schedule(staff_data, date_range)
    
    # DataFrame
    df = pd.DataFrame(final_schedule)
    # Traduciamo i giorni in italiano per bellezza (opzionale, ma carino)
    days_map = {
        'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'
    }
    df['Giorno'] = df['Giorno'].map(days_map)

    # --- VISUALIZZAZIONE RISULTATI ---
    
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🗓️ Calendario Operativo")
        
        # Funzione per colorare le righe
