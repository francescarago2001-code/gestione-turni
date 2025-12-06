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

# --- 3. CSS "CORPORATE TOTAL BLUE" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    :root {
        --primary-color: #0f172a; /* Blu scuro professionale */
        --hover-color: #1e293b;
        --accent-color: #3b82f6; /* Blu più chiaro per dettagli */
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1f2937;
    }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* --- BOTTONI --- */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: var(--hover-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* --- TABS (La riga sotto le tab) --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary-color) !important;
        border-bottom: 3px solid var(--primary-color) !important; /* Riga Blu Scuro */
        font-weight: 700;
    }
    
    /* --- MULTISELECT & TAGS (I giorni della settimana) --- */
    /* Sfondo del tag selezionato */
    span[data-baseweb="tag"] {
        background-color: #e0f2fe !important; /* Blu chiarissimo */
        border: 1px solid #bae6fd;
    }
    /* Testo del tag */
    span[data-baseweb="tag"] span {
        color: #0c4a6e !important; /* Blu scuro testo */
    }
    /* Icona X per chiudere il tag */
    span[data-baseweb="tag"] svg {
        fill: #0c4a6e !important;
    }

    /* --- SLIDER --- */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--primary-color) !important; /* Pallino blu */
    }
    div[data-baseweb="slider"] div {
        background-color: #cbd5e1; /* Barra grigia */
    }
    div[data-baseweb="slider"] div[style*="width"] {
        background-color: var(--primary-color) !important; /* Barra piena blu */
    }

    /* --- CHECKBOX --- */
    /* Quando selezionata */
    [data-baseweb="checkbox"] div[class*="checked"] {
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
    }

    /* --- INPUT FIELDS FOCUS (Bordi blu invece di arancioni) --- */
    input:focus, textarea:focus, select:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }

    /* --- HEADERS --- */
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 700;
    }
    
    /* --- ALERTS --- */
    .stAlert {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. BLOCCO PAYWALL ---
if not trial_active:
    st.error(f"Licenza Scaduta. Il periodo di prova di {TRIAL_DAYS} giorni è terminato.")
    st.info("Per continuare a utilizzare il software è necessario sottoscrivere un piano.")
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
                        if name in people_yesterday_same_shift:
                            continue 

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
    
    pdf.set_fill_color(240, 248, 255) # Blu chiarissimo per header PDF
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
                pdf.set_text_color(185, 28, 28); pdf.set_font("Helvetica", 'B', 7) # Rosso scuro
            elif "CHIUSO" in txt:
                pdf.set_text_color(148, 163, 184); pdf.set_font("Helvetica", 'I', 7) # Grigio
            else:
                pdf.set_text_color(15, 23, 42); pdf.set_font("Helvetica", '', 7) # Blu scuro
            
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

    avoid_consecutive = st.checkbox("Evita stesso turno consecutivo", value=True, help="Se attivo, chi fa 'Pranzo' oggi non farà 'Pranzo' domani.")
    
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
            st.markdown(f"**{shift}**")
            shift_reqs = {}
            for role in roles:
                count = st.number_input(f"{role}", min_value=0, value=1, key=f"req_{shift}_{role}")
                shift_reqs[role] = count
            requirements[shift] = shift_reqs

# TAB 2: STAFF
with tab_staff:
    st.subheader("Dettagli Dipendenti")
    staff_db = {}
    
    for name in staff_names:
        with st.expander(f"{name}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                role = st.selectbox(f"Ruolo", roles, key=f"role_{name}")
                rest = st.slider(f"Riposi settimanali", 0, 7, 2, key=f"rest_{name}")
            with c2:
                avail_shifts = st.multiselect(f"Turni Abilitati", shifts, default=shifts, key=f"avs_{name}")
                unavail_dates = st.date_input(f"Giorni Indisponibili (Ferie)", [], key=f"un_{name}")
                if not isinstance(unavail_dates, list): unavail_dates = [unavail_dates]
            
            staff_db[name] = {'role': role, 'rest': rest, 'shifts': avail_shifts, 'unavail': unavail_dates}

# TAB 3: GENERAZIONE
with tab_gen:
    if st.button("ELABORA TURNI", type="primary"):
        with st.spinner("Calcolo combinazioni ottimali..."):
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
        
        st.markdown("### Risultato Pianificazione")
        edited_df = st.data_editor(
            df, 
            use_container_width=True, 
            height=500,
            column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY")}
        )
        
        flat_list = []
        for s in shifts: flat_list.extend(edited_df[s].tolist())
        scoperti = sum([str(x).count("SCOPERTO") for x in flat_list])
        
        if scoperti == 0:
            st.success("Tutti i turni sono coperti correttamente.")
        else:
            st.error(f"Attenzione: {scoperti} posizioni risultano scoperte.")

        try:
            pdf_data = pdf_export(edited_df, shifts)
            st.download_button("SCARICA PDF", pdf_data, "turni.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Errore PDF: {e}")

# TAB 4: COMUNICAZIONI (SOLO WHATSAPP)
with tab_comm:
    st.subheader("Esportazione per Chat")
    st.info("Genera un messaggio formattato pronto per essere inviato sul gruppo aziendale.")
    
    if st.session_state.schedule_df is not None:
        wa_text = f"*TURNI SETTIMANALI - DAL {start_dt.strftime('%d/%m')}*\n\n"
        df = st.session_state.schedule_df
        for index, row in df.iterrows():
            if row['Giorno'] not in active_days: continue
            date_str = row['Data'].strftime('%d/%m') if hasattr(row['Data'], 'strftime') else str(row['Data'])
            wa_text += f"📅 *{row['Giorno']} {date_str}*\n"
            for s in shifts:
                staff_str = str(row[s])
                if staff_str == "-" or staff_str == "CHIUSO":
                    continue
                staff_list = staff_str.split(", ")
                formatted_staff = "\n".join([f"   ▫ {p}" for p in staff_list])
                wa_text += f"   *{s.upper()}*:\n{formatted_staff}\n"
            wa_text += "-------------------\n"
        st.text_area("Copia questo testo:", wa_text, height=400)
    else:
        st.warning("Genera prima i turni per vedere l'anteprima del messaggio.")
