import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import date, timedelta, datetime
from fpdf import FPDF

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="ShiftManager Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SISTEMA LICENZA ---
LICENSE_FILE = "license_data.json"
TRIAL_DAYS = 7

def check_trial_status():
    today = date.today()
    if not os.path.exists(LICENSE_FILE):
        data = {"start_date": str(today)}
        with open(LICENSE_FILE, "w") as f:
            json.dump(data, f)
        return True, TRIAL_DAYS, today
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
    except:
        return False, 0, today
    days_elapsed = (today - start_date).days
    days_remaining = TRIAL_DAYS - days_elapsed
    return (days_remaining >= 0), max(0, days_remaining), start_date

trial_active, days_left, trial_start = check_trial_status()

# --- 3. CSS "NUCLEAR BLUE" (Sovrascrittura Totale) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    :root {
        --primary-blue: #0056b3;
        --dark-blue: #004494;
        --light-blue-bg: #eff6ff;
        --text-color: #0f172a;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color) !important;
        background-color: #ffffff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* ==============================================
       FIX AGGRESSIVO PER COLORI ARANCIONI/ROSSI
       ============================================== */

    /* 1. SLIDER: La barra di riempimento */
    div[data-baseweb="slider"] div[style*="background-color: rgb(255, 75, 75)"], 
    div[data-baseweb="slider"] div[style*="background-color: #ff4b4b"] {
        background-color: var(--primary-blue) !important;
    }

    /* 2. SLIDER: Il numero sopra */
    div[data-testid="stSlider"] div[data-baseweb="slider"] div {
        color: var(--primary-blue) !important;
        font-weight: bold !important;
    }

    /* 3. SLIDER: Il pallino */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--primary-blue) !important;
        box-shadow: 0 0 5px rgba(0, 86, 179, 0.5) !important;
    }

    /* 4. CHECKBOX: Il quadratino quando selezionato */
    div[data-baseweb="checkbox"] div[aria-checked="true"] {
        background-color: var(--primary-blue) !important;
        border-color: var(--primary-blue) !important;
    }
    
    /* 5. MULTISELECT & TAGS: Colore di sfondo e testo */
    span[data-baseweb="tag"] {
        background-color: var(--light-blue-bg) !important;
        border: 1px solid #bfdbfe !important;
    }
    span[data-baseweb="tag"] span {
        color: var(--primary-blue) !important;
    }
    span[data-baseweb="tag"] svg {
        fill: var(--primary-blue) !important;
    }

    /* 6. INPUT FOCUS: Bordi blu quando scrivi */
    input:focus, textarea:focus, select:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 1px var(--primary-blue) !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 1px var(--primary-blue) !important;
    }

    /* --- ALTRI STILI --- */
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #e2e8f0; }
    .stTabs [aria-selected="true"] {
        color: var(--primary-blue) !important;
        border-bottom-color: var(--primary-blue) !important;
    }

    /* Bottoni */
    .stButton>button {
        background-color: var(--primary-blue);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background-color: var(--dark-blue);
        color: white;
    }

    /* Headers */
    h1, h2, h3, h4 { color: #111827 !important; font-weight: 700; }
    
    /* Alerts */
    .stAlert { background-color: #f0fdf4; border: 1px solid #dcfce7; }
    </style>
""", unsafe_allow_html=True)

# --- 4. BLOCCO PAYWALL ---
if not trial_active:
    st.error(f"Licenza Scaduta. Il periodo di prova di {TRIAL_DAYS} giorni è terminato.")
    st.link_button("Rinnova Licenza", "https://www.paypal.com")
    st.stop()

# --- 5. LOGICA ALGORITMO ---

if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None

def generate_date_range(start, num):
    return [start + timedelta(days=i) for i in range(num)]

def get_day_name(d):
    return ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica'][d.weekday()]

def generate_schedule_pro(staff_db, date_list, shifts, reqs, active_days, avoid_same_consecutive):
    schedule = []
    work_counts = {name: 0 for name in staff_db}
    weekend_counts = {name: 0 for name in staff_db}
    targets = {}
    for name, info in staff_db.items():
        weeks = len(date_list) / 7
        targets[name] = len(date_list) - round(weeks * info['rest'])

    prev_day_assignments = {} 

    for current_day in date_list:
        day_name = get_day_name(current_day)
        is_weekend = current_day.weekday() >= 5
        row = {"Data": current_day, "Giorno": day_name}
        current_day_assignments = {s: [] for s in shifts} 
        
        if day_name not in active_days:
            for s in shifts: row[s] = "CHIUSO"
            schedule.append(row)
            prev_day_assignments = {}
            continue
            
        worked_today = [] 
        for shift in shifts:
            assigned_names = []
            shift_reqs = reqs.get(shift, {})
            for role, count_needed in shift_reqs.items():
                if count_needed <= 0: continue
                candidates = []
                for name, info in staff_db.items():
                    if info['role'] != role: continue
                    if current_day in info['unavail']: continue
                    if shift not in info['shifts']: continue
                    if work_counts[name] >= targets[name]: continue
                    if name in worked_today: continue
                    if avoid_same_consecutive and prev_day_assignments:
                        people_yesterday_same_shift = prev_day_assignments.get(shift, [])
                        if name in people_yesterday_same_shift: continue 
                    candidates.append(name)
                
                if is_weekend:
                    candidates.sort(key=lambda x: (weekend_counts[x], work_counts[x], random.random()))
                else:
                    candidates.sort(key=lambda x: (work_counts[x], random.random()))
                
                for i in range(min(len(candidates), count_needed)):
                    chosen = candidates[i]
                    display_name = f"{chosen} ({role[:3].upper()})"
                    assigned_names.append(display_name)
                    worked_today.append(chosen)
                    current_day_assignments[shift].append(chosen)
                    work_counts[chosen] += 1
                    if is_weekend: weekend_counts[chosen] += 1
                
                filled_role_count = len([x for x in assigned_names if role[:3].upper() in x])
                missing = count_needed - filled_role_count
                if missing > 0:
                    for _ in range(missing):
                        assigned_names.append(f"SCOPERTO ({role.upper()})")
            
            row[shift] = ", ".join(assigned_names) if assigned_names else "-"
        
        schedule.append(row)
        prev_day_assignments = current_day_assignments

    return schedule

def pdf_export(df, shifts):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "PIANIFICAZIONE OPERATIVA", 0, 1, 'L')
    pdf.ln(5)
    
    cols = ['Data', 'Giorno'] + shifts
    col_w = 275 / len(cols)
    
    pdf.set_fill_color(240, 248, 255) 
    pdf.set_font("Helvetica", 'B', 8)
    for c in cols:
        pdf.cell(col_w, 8, c.upper(), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", size=7)
    for _, row in df.iterrows():
        d_str = row['Data'].strftime('%d/%m') if hasattr(row['Data'], 'strftime') else str(row['Data'])
        pdf.cell(col_w, 8, d_str, 1, 0, 'C')
        pdf.cell(col_w, 8, str(row['Giorno']), 1, 0, 'C')
        
        for s in shifts:
            txt = str(row[s])
            if "SCOPERTO" in txt:
                pdf.set_text_color(185, 28, 28); pdf.set_font("Helvetica", 'B', 7) 
            elif "CHIUSO" in txt:
                pdf.set_text_color(148, 163, 184); pdf.set_font("Helvetica", 'I', 7) 
            else:
                pdf.set_text_color(15, 23, 42); pdf.set_font("Helvetica", '', 7) 
            
            if len(txt) > 30: txt = txt[:27] + "..."
            pdf.cell(col_w, 8, txt, 1, 0, 'C')
            
        pdf.set_text_color(0,0,0)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.header("ShiftManager")
    st.caption(f"Licenza: {'Attiva' if trial_active else 'Scaduta'} | {days_left}gg rimanenti")
    st.markdown("---")
    
    st.subheader("Generale")
    start_dt = st.date_input("Data Inizio", date.today())
    days_num = st.number_input("Giorni da pianificare", 7, 365, 30)
    
    days_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    active_days = st.multiselect("Giorni Operativi", days_it, default=days_it)
    
    shifts_in = st.text_input("Turni (separati da virgola)", "Pranzo, Cena")
    shifts = [s.strip() for s in shifts_in.split(',') if s.strip()]

    avoid_consecutive = st.checkbox("Evita stesso turno consecutivo", value=True)
    
    st.markdown("---")
    st.subheader("Ruoli & Staff")
    roles_in = st.text_area("Ruoli (uno per riga)", "Cameriere\nCuoco\nBarman")
    roles = [r.strip() for r in roles_in.split('\n') if r.strip()]
    
    staff_names_in = st.text_area("Dipendenti (uno per riga)", "Mario Rossi\nLuca Bianchi\nGiulia Verdi")
    staff_names = [n.strip() for n in staff_names_in.split('\n') if n.strip()]

# --- 7. PAGINA PRINCIPALE ---

col_main, col_reset = st.columns([4,1])
with col_main:
    st.title("Pianificazione Turni")
with col_reset:
    if st.button("Nuova Pianificazione"):
        st.session_state.schedule_df = None
        st.rerun()

if not staff_names or not shifts or not roles:
    st.warning("Configurazione incompleta. Compila la barra laterale.")
    st.stop()

# TAB NAVIGATION
tab_req, tab_staff, tab_gen, tab_comm = st.tabs(["Fabbisogno", "Staff", "Generazione Turni", "WhatsApp Export"])

# TAB 1: FABBISOGNO
with tab_req:
    st.subheader("Fabbisogno Personale per Turno")
    st.caption("Definisci quante persone servono per ogni ruolo.")
    
    requirements = {}
    cols = st.columns(len(shifts))
    for i, shift in enumerate(shifts):
        with cols[i]:
            st.markdown(f"
