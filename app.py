import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import date, timedelta, datetime
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Gestione Turni Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DI GESTIONE LICENZA E PROVA GRATUITA ---
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

    if days_remaining < 0:
        return False, 0, start_date
    else:
        return True, days_remaining, start_date

trial_active, days_left, trial_start = check_trial_status()

# --- CSS STILE BUSINESS ---
css_style = """
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    h1, h2, h3 { color: #2c3e50 !important; }
    .stButton>button { background-color: #2c3e50; color: white; border-radius: 4px; }
    .payment-container { text-align: center; padding: 50px; border: 2px solid #e74c3c; background-color: #fdf2f2; margin-top: 50px; border-radius: 10px;}
    </style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- BLOCCO SOFTWARE SE PROVA SCADUTA ---
if not trial_active:
    alert_html = f"""
    <div class="payment-container">
        <h1 style="color: #c0392b !important;">🚫 Periodo di Prova Scaduto</h1>
        <p>I tuoi {TRIAL_DAYS} giorni di prova sono terminati. Acquista la licenza per continuare.</p>
    </div>
    """
    st.markdown(alert_html, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.link_button("💳 ACQUISTA LICENZA ORA", "https://www.paypal.com/it/home") 
    st.stop()

# --- STATO SESSIONE ---
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None

# --- FUNZIONI LOGICHE ---
def generate_date_range(start_date, num_days):
    return [start_date + timedelta(days=i) for i in range(num_days)]

def calculate_target(total_days, weekly_rest):
    weeks = total_days / 7
    total_rest = round(weeks * weekly_rest)
    return max(0, total_days - total_rest)

def get_italian_day(date_obj):
    days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    return days[date_obj.weekday()]

def generate_schedule(staff_data, date_list, shift_types, prevent_consecutive, active_days_list):
    schedule = []
    
    # Contatori per l'equità
    work_counts = {name: 0 for name in staff_data.keys()}
    weekend_counts = {name: 0 for name in staff_data.keys()} # Contatore specifico weekend
    
    # Calcolo target teorici (approssimativo)
    targets = {}
    for name, data in staff_data.items():
        targets[name] = calculate_target(len(date_list), data['weekly_rest'])

    for current_day in date_list:
        day_name_it = get_italian_day(current_day)
        is_weekend = current_day.weekday() >= 5 # 5=Sabato, 6=Domenica
        
        # 1. CONTROLLO GIORNI AZIENDALI
        # Se il giorno non è tra quelli lavorativi dell'azienda, salta e metti "CHIUSO" o vuoto
        if day_name_it not in active_days_list:
            # Creiamo una riga vuota o "Chiuso" per mantenere la continuità visiva
            closed_row = {"Data": current_day, "Giorno": day_name_it}
            for s in shift_types:
                closed_row[s] = "CHIUSO"
            schedule.append(closed_row)
            continue

        day_schedule = {
            "Data": current_day,
            "Giorno": day_name_it
        }
        
        worked_today = []
        yesterday_schedule = schedule[-1] if len(schedule) > 0 else None
        
        for shift_name in shift_types:
            candidates = []
            
            for name, data in staff_data.items():
                # --- REGOLE DI ESCLUSIONE ---
                
                # A. Indisponibilità specifica (Ferie/Malattia)
                if current_day in data['unavailable']:
                    continue
                
                # B. Turno non abilitato per questa persona (es. Mario non fa la Notte)
                if shift_name not in data['allowed_shifts']:
                    continue

                # C. Target Raggiunto (Equità generale)
                if work_counts[name] >= targets[name]: 
                    continue
                
                # D. Già lavorato oggi (niente doppi turni)
                if name in worked_today: 
                    continue
                
                # E. Consecutività (Niente Mattina se ieri hai fatto Mattina, opzionale)
                if prevent_consecutive and yesterday_schedule:
                    if yesterday_schedule.get(shift_name) == name:
                        continue
                
                candidates.append(name)
            
            selected_person = "SCOPERTO"
            
            if candidates:
                # --- ALGORITMO DI SELEZIONE PRIORITARIA ---
                # Ordiniamo i candidati. 
                # Criterio 1: Se è weekend, privilegia chi ha fatto MENO weekend.
                # Criterio 2: Privilegia chi ha fatto MENO turni totali.
                # Criterio 3: Random per rompere la parità.
                
                if is_weekend:
                    # Ordina prima per weekend lavorati, poi per totale
                    candidates.sort(key=lambda x: (weekend_counts[x], work_counts[x], random.random()))
                else:
                    # Ordina solo per totale lavorato
                    candidates.sort(key=lambda x: (work_counts[x], random.random()))
                
                # Prendiamo il migliore
                chosen = candidates[0]
                
                selected_person = chosen
                
                # Aggiorna contatori
                work_counts[chosen] += 1
                if is_weekend:
                    weekend_counts[chosen] += 1
                    
                worked_today.append(chosen)
            
            day_schedule[shift_name] = selected_person
            
        schedule.append(day_schedule)
            
    return schedule

def export_to_pdf(dataframe, shift_cols):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "PIANIFICAZIONE TURNI", 0, 1, 'L')
    pdf.ln(5)
    
    page_width = 275
    date_w = 35
    day_w = 30
    rem_w = page_width - date_w - day_w
    shift_w = rem_w / len(shift_cols)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(date_w, 10, "DATA", 1, 0, 'C', True)
    pdf.cell(day_w, 10, "GIORNO", 1, 0, 'C', True)
    for s in shift_cols:
        col_name = s.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(shift_w, 10, col_name.upper(), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", size=9)
    for _, row in dataframe.iterrows():
        try:
            d_str = row['Data'].strftime('%d/%m/%Y')
        except:
            d_str = str(row['Data'])
            
        day_str = str(row['Giorno']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(date_w, 10, d_str, 1, 0, 'C')
        pdf.cell(day_w, 10, day_str, 1, 0, 'C')
        
        for s in shift_cols:
            val = str(row[s])
            val_enc = val.encode('latin-1', 'replace').decode('latin-1')
            
            if val == "SCOPERTO":
                pdf.set_text_color(180, 0, 0); pdf.set_font("Helvetica", 'B', 9)
            elif val == "CHIUSO":
                pdf.set_text_color(150, 150, 150); pdf.set_font("Helvetica", 'I', 9)
            else:
                pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", size=9)
                
            pdf.cell(shift_w, 10, val_enc, 1, 0, 'C')
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔐 Licenza Demo")
    if days_left > 3:
        st.success(f"Prova Attiva: **{days_left}** gg rimasti.")
    else:
        st.warning(f"⚠️ Scadenza tra **{days_left}** gg.")
    st.progress(days_left / TRIAL_DAYS)
    st.markdown("---")

    st.header("1. Parametri Generali")
    start_date = st.date_input("Data Inizio", date.today())
    duration = st.number_input("Giorni da pianificare", 7, 365, 30)
    
    st.subheader("Giorni Operativi Azienda")
    days_of_week_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    # Default: Lun-Ven
    active_days = st.multiselect("Seleziona giorni lavorativi", days_of_week_it, default=days_of_week_it)
    
    st.subheader("Definizione Turni")
    shifts_input = st.text_input("Nomi Turni (virgola)", "Mattina, Pomeriggio")
    shift_types = [s.strip() for s in shifts_input.split(',') if s.strip()]
    
    st.markdown("---")
    st.header("2. Gestione Staff")
    staff_input = st.text_area("Inserisci Nomi (uno per riga)", "Rossi\nBianchi\nVerdi")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# --- MAIN PAGE ---
st.title("Gestione Turni Pro")

if not staff_names or not shift_types or not active_days:
    st.warning("Configura i parametri nella barra laterale (Turni, Staff e Giorni Operativi).")
    st.stop()

# --- CONFIGURAZIONE AVANZATA DIPENDENTI ---
st.subheader("3. Dettagli e Disponibilità Risorse")
st.info("Configura qui ferie, preferenze turni e riposi per ogni dipendente.")

staff_data = {}

# Usiamo un container espandibile per ogni dipendente per pulizia visiva
for name in staff_names:
    with st.expander(f"👤 Configura: **{name}**", expanded=False):
        col_a, col_b = st.columns(2)
        
        with col_a:
            w_rest = st.slider(f"Giorni riposo/settimana ({name})", 0, 7, 2, key=f"wr_{name}")
            # Scelta turni abilitati (es. solo Mattina)
            allowed = st.multiselect(
                f"Turni abilitati per {name}", 
                options=shift_types, 
                default=shift_types, 
                key=f"all_{name}"
            )
            
        with col_b:
            # Scelta giorni di ferie/indisponibilità
            unavailable = st.date_input(
                f"Date Indisponibili/Ferie ({name})", 
                [], 
                key=f"un_{name}",
                help="Seleziona i giorni in cui il dipendente NON può lavorare."
            )
            # Converti input singolo o lista in lista sicura
            if not isinstance(unavailable, list):
                unavailable = [unavailable]
        
        # Salvataggio dati
        staff_data[name] = {
            'weekly_rest': w_rest,
            'allowed_shifts': allowed,
            'unavailable': unavailable
        }

st.markdown("---")

# --- GENERAZIONE ---
col_gen, col_info = st.columns([1, 2])
with col_gen:
    generate_btn = st.button("🚀 Genera Turni Ottimizzati", type="primary")

if generate_btn:
    date_range = generate_date_range(start_date, duration)
    
    # Esecuzione algoritmo con i nuovi parametri
    schedule_data = generate_schedule(
        staff_data, 
        date_range, 
        shift_types, 
        st.sidebar.checkbox("Evita stesso turno consecutivo", True),
        active_days
    )
    
    df = pd.DataFrame(schedule_data)
    cols_order = ['Data', 'Giorno'] + shift_types
    df = df[cols_order]
    
    st.session_state.schedule_df = df
    st.success("Turni generati con successo considerando ferie ed equità weekend!")

# --- VISUALIZZAZIONE E MODIFICA ---
if st.session_state.schedule_df is not None:
    st.subheader("📅 Pianificazione Operativa")
    st.caption("Puoi modificare manualmente le celle se necessario.")
    
    edited_df = st.data_editor(
        st.session_state.schedule_df,
        use_container_width=True,
        height=600,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", disabled=True),
            "Giorno": st.column_config.TextColumn("Giorno", disabled=True),
        },
        num_rows="fixed"
    )
    
    st.markdown("### Azioni")
    col_pdf, _ = st.columns([1, 4])
    
    with col_pdf:
        try:
            pdf_bytes = export_to_pdf(edited_df, shift_types)
            st.download_button(
                label="📥 Scarica PDF Stampa",
                data=pdf_bytes,
                file_name="Piano_Turni_Pro.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore PDF: {e}")
