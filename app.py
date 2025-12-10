import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import date, timedelta, datetime
from fpdf import FPDF

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Snobol Enterprise",
    # page_icon="logo_icon.png", # SE VUOI L'ICONCINA SULLA SCHEDA DEL BROWSER, DECOMMENTA E METTI IL FILE
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SISTEMA LICENZA (Backend invariato) ---
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

# --- 3. CSS "ENTERPRISE LIGHT THEME" (Bianco Professionale) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-color: #ffffff;          /* Bianco puro */
        --sidebar-bg: #f8fafc;        /* Grigio chiarissimo per contrasto */
        --text-primary: #0f172a;      /* Nero/Blu scuro per testi principali */
        --text-secondary: #64748b;    /* Grigio medio per testi secondari */
        --accent: #00f2ff;            /* Ciano Snobol (brand) */
        --accent-dark: #0ea5e9;       /* Versione più scura per hover */
        --border: #e2e8f0;            /* Bordi grigio chiaro */
    }

    /* RESET GENERALE */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    h1, h2, h3, h4 {
        font-weight: 600;
        letter-spacing: -0.5px;
        color: var(--text-primary) !important;
    }
    
    p, label, span, div.stMarkdown {
        color: var(--text-secondary) !important;
        font-size: 0.9rem;
    }

    /* SIDEBAR PULITA */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--border);
    }
    # [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
    }

    /* INPUT FIELDS (Stile Tecnico Chiaro) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-dark) !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1) !important;
    }

    /* SELECTBOX & TAGS */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: var(--border) !important;
        border-radius: 4px !important;
        color: var(--text-primary) !important;
    }
    span[data-baseweb="tag"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 2px !important;
    }
    span[data-baseweb="tag"] span {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
    }

    /* BOTTONI (Stile Software) */
    .stButton > button {
        background-color: var(--text-primary) !important;
        color: white !important;
        border-radius: 4px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        text-transform: none !important;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: var(--accent-dark) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* BOTTONI SECONDARI (Download) */
    [data-testid="stDownloadButton"] > button {
        background: white !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        border-color: var(--text-primary) !important;
        background: #f8fafc !important;
    }

    /* TABS (Minimal Light) */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border);
        gap: 30px;
        background-color: white;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--text-secondary) !important;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-dark) !important;
        border-bottom: 2px solid var(--accent-dark) !important;
    }

    /* TABELLE DATI */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        background-color: white;
    }
    
    /* EXPANDER */
    .streamlit-expanderHeader {
        background-color: white !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 4px !important;
    }
    
    /* ALERT CUSTOM LIGHT */
    .stAlert {
        background-color: #f8fafc;
        border: 1px solid var(--border);
        color: var(--text-primary);
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. CONTROLLO LICENZA ---
if not trial_active:
    st.error(f"Licenza scaduta. Contattare l'amministrazione.")
    st.stop()

# --- 5. LOGICA ALGORITMO (Identica) ---
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
            for s in shifts: row[s] = "-"
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
                        assigned_names.append(f"UNASSIGNED ({role.upper()})")
            
            row[shift] = ", ".join(assigned_names) if assigned_names else "-"
        schedule.append(row)
        prev_day_assignments = current_day_assignments
    return schedule

def pdf_export(df, shifts):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 10, "SNOBOL // REPORT PIANIFICAZIONE", 0, 1, 'L')
    pdf.ln(2)
    cols = ['Data', 'Giorno'] + shifts
    col_w = 275 / len(cols)
    pdf.set_fill_color(245, 245, 245) 
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
            if "UNASSIGNED" in txt:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)
            if len(txt) > 30: txt = txt[:27] + "..."
            pdf.cell(col_w, 8, txt, 1, 0, 'C')
        pdf.set_text_color(0,0,0)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR (Pannello Controllo con LOGO IMMAGINE) ---
with st.sidebar:
    # --- INSERIMENTO LOGO ---
    # Assicurati che il file "logo.png" sia nella stessa cartella di questo script.
    # Se il tuo file si chiama diversamente (es. "snobol_logo.jpg"), modifica il nome qui sotto.
    try:
        st.image("logo.png", width=150) 
    except:
        # Fallback se l'immagine non viene trovata
        st.warning("File 'logo.png' non trovato.")
        st.markdown("### Snobol Enterprise")

    st.markdown("---")
    
    st.markdown("#### CONFIGURAZIONE GLOBALE")
    start_dt = st.date_input("Inizio Periodo", date.today())
    days_num = st.number_input("Durata (giorni)", 7, 365, 30)
    
    days_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    active_days = st.multiselect("Giorni Operativi", days_it, default=days_it)
    
    shifts_in = st.text_input("Definizione Turni (CSV)", "Pranzo, Cena")
    shifts = [s.strip() for s in shifts_in.split(',') if s.strip()]

    avoid_consecutive = st.checkbox("Blocco Turni Consecutivi", value=True)
    
    st.markdown("---")
    st.markdown("#### DATABASE PERSONALE")
    roles_in = st.text_area("Lista Ruoli", "Cameriere\nCuoco\nBarman")
    roles = [r.strip() for r in roles_in.split('\n') if r.strip()]
    
    staff_names_in = st.text_area("Anagrafica Dipendenti", "Mario Rossi\nLuca Bianchi\nGiulia Verdi")
    staff_names = [n.strip() for n in staff_names_in.split('\n') if n.strip()]
    
    st.markdown("---")
    # Esempio di badge di stato professionale
    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 10px; font-size: 0.8rem; color: #64748b; background: #f1f5f9; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0;'>
            <div style='width: 8px; height: 8px; background: #22c55e; border-radius: 50%;'></div>
            Licenza Attiva ({days_left}gg)
        </div>
    """, unsafe_allow_html=True)

# --- 7. HEADER PAGINA PRINCIPALE ---

col_head, col_action = st.columns([3, 1])

with col_head:
    st.title("Pianificazione Operativa")
    st.markdown("Dashboard di allocazione risorse e gestione turnistica.")

with col_action:
    if st.button("Reset Pianificazione"):
        st.session_state.schedule_df = None
        st.rerun()

if not staff_names or not shifts or not roles:
    st.warning("Configurazione incompleta. Verificare parametri nel pannello laterale.")
    st.stop()

# TAB NAVIGATION (Nomi tecnici)
tab_req, tab_staff, tab_gen, tab_comm = st.tabs(["FABBISOGNO", "ANAGRAFICA", "ELABORAZIONE", "EXPORT"])

# TAB 1: FABBISOGNO
with tab_req:
    st.markdown("#### Definizione Carico di Lavoro")
    st.markdown("Indicare il numero di risorse necessarie per ruolo in ogni turno.")
    
    requirements = {}
    cols = st.columns(len(shifts))
    for i, shift in enumerate(shifts):
        with cols[i]:
            # Box per il nome del turno
            st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px 12px; border-radius: 4px; font-weight: 600; text-align: center; margin-bottom: 15px; color: #0f172a;">
                    TURNO: {shift.upper()}
                </div>
            """, unsafe_allow_html=True)
            shift_reqs = {}
            for role in roles:
                count = st.number_input(f"{role}", min_value=0, value=1, key=f"req_{shift}_{role}")
                shift_reqs[role] = count
            requirements[shift] = shift_reqs

# TAB 2: STAFF
with tab_staff:
    st.markdown("#### Parametri Individuali")
    st.markdown("Configurazione vincoli contrattuali e disponibilità.")
    staff_db = {}
    
    for name in staff_names:
        with st.expander(f"{name}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                role = st.selectbox(f"Ruolo", roles, key=f"role_{name}")
                rest = st.slider(f"Riposi/Settimana", 0, 7, 2, key=f"rest_{name}")
            with c2:
                avail_shifts = st.multiselect(f"Competenze Turno", shifts, default=shifts, key=f"avs_{name}")
                unavail_dates = st.date_input(f"Indisponibilità (Ferie/Malattia)", [], key=f"un_{name}")
                if not isinstance(unavail_dates, list): unavail_dates = [unavail_dates]
            
            staff_db[name] = {'role': role, 'rest': rest, 'shifts': avail_shifts, 'unavail': unavail_dates}

# TAB 3: GENERAZIONE
with tab_gen:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Avvia Algoritmo di Allocazione"):
        with st.spinner("Calcolo ottimizzazione in corso..."):
            res = generate_schedule_pro(
                staff_db, 
                generate_date_range(start_dt, days_num), 
                shifts, 
                requirements, 
                active_days,
                avoid_consecutive
            )
            st.session_state.schedule_df = pd.DataFrame(res)

    if st.session_state.schedule_df is not None:
        df = st.session_state.schedule_df
        
        st.markdown("#### Output Pianificazione")
        edited_df = st.data_editor(
            df, 
            use_container_width=True, 
            height=600,
            column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY")}
        )
        
        flat_list = []
        for s in shifts: flat_list.extend(edited_df[s].tolist())
        scoperti = sum([str(x).count("UNASSIGNED") for x in flat_list])
        
        if scoperti == 0:
            st.success("Allocazione completata con successo. Nessuna posizione scoperta.")
        else:
            st.error(f"Attenzione: rilevate {scoperti} posizioni non coperte.")

        try:
            pdf_data = pdf_export(edited_df, shifts)
            st.download_button("Download Report PDF", pdf_data, "planning_report.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Errore generazione PDF: {e}")

# TAB 4: COMUNICAZIONI
with tab_comm:
    st.markdown("#### Testo per Comunicazione Interna")
    st.markdown("Formato testo semplice per la distribuzione rapida.")
    
    if st.session_state.schedule_df is not None:
        wa_text = f"SNOBOL // PLANNING OPERATIVO - DAL {start_dt.strftime('%d/%m')}\n\n"
        df = st.session_state.schedule_df
        for index, row in df.iterrows():
            if row['Giorno'] not in active_days: continue
            date_str = row['Data'].strftime('%d/%m') if hasattr(row['Data'], 'strftime') else str(row['Data'])
            wa_text += f"[{row['Giorno']} {date_str}]\n"
            for s in shifts:
                staff_str = str(row[s])
                if staff_str == "-" or staff_str == "CHIUSO":
                    continue
                staff_list = staff_str.split(", ")
                formatted_staff = "\n".join([f"- {p}" for p in staff_list])
                wa_text += f"{s.upper()}:\n{formatted_staff}\n"
            wa_text += "-------------------\n"
        
        st.text_area("Raw Text Output:", wa_text, height=400)
    else:
        st.warning("Nessun dato di pianificazione disponibile.")
