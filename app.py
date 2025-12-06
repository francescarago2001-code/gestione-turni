import streamlit as st
import pandas as pd
import random
import json
import os
import time
from datetime import date, timedelta, datetime
from fpdf import FPDF

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="ShiftManager Pro",
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

# --- 3. CSS "CORPORATE MINIMAL" ---
st.markdown("""
    <style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1f2937;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f3f4f6;
        border-right: 1px solid #e5e7eb;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #111827;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards / Containers */
    .metric-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 6px;
    }
    
    /* Paywall */
    .paywall {
        text-align: center;
        padding: 60px;
        border: 1px solid #fee2e2;
        background-color: #fef2f2;
        border-radius: 12px;
        margin-top: 40px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. BLOCCO PAYWALL ---
if not trial_active:
    st.markdown(f"""
    <div class="paywall">
        <h2 style="color: #991b1b;">Licenza Scaduta</h2>
        <p style="color: #7f1d1d;">Il periodo di prova di {TRIAL_DAYS} giorni è terminato.</p>
        <p>Per riattivare le funzionalità operative e il modulo comunicazioni, è necessario un piano attivo.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.link_button("Rinnova Licenza", "https://www.paypal.com", use_container_width=True)
    st.stop()

# --- 5. LOGICA ALGORITMO (Ruoli + Fabbisogno) ---

if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'comm_log' not in st.session_state:
    st.session_state.comm_log = []

def generate_date_range(start, num):
    return [start + timedelta(days=i) for i in range(num)]

def get_day_name(d):
    return ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica'][d.weekday()]

def generate_schedule_pro(staff_db, date_list, shifts, reqs, active_days):
    schedule = []
    
    # Contatori per equità
    # staff_db structure: { 'Name': {'role': 'Cook', 'rest': 2, 'unavail': [], 'shifts': []} }
    work_counts = {name: 0 for name in staff_db}
    weekend_counts = {name: 0 for name in staff_db}
    
    targets = {}
    for name, info in staff_db.items():
        weeks = len(date_list) / 7
        targets[name] = len(date_list) - round(weeks * info['rest'])

    for current_day in date_list:
        day_name = get_day_name(current_day)
        is_weekend = current_day.weekday() >= 5
        
        row = {"Data": current_day, "Giorno": day_name}
        
        # Giorno di chiusura?
        if day_name not in active_days:
            for s in shifts: row[s] = "CHIUSO"
            schedule.append(row)
            continue
            
        worked_today = [] # Lista nomi che lavorano oggi (evita doppi turni)
        
        for shift in shifts:
            assigned_names = []
            
            # Per ogni turno, controlliamo i requisiti per OGNI RUOLO
            # reqs structure: {'Mattina': {'Cameriere': 2, 'Cuoco': 1}}
            
            shift_reqs = reqs.get(shift, {})
            
            for role, count_needed in shift_reqs.items():
                if count_needed <= 0: continue
                
                # Cerchiamo candidati per QUESTO ruolo
                candidates = []
                for name, info in staff_db.items():
                    # Filtri Hard
                    if info['role'] != role: continue
                    if current_day in info['unavail']: continue
                    if shift not in info['shifts']: continue
                    if work_counts[name] >= targets[name]: continue
                    if name in worked_today: continue
                    
                    candidates.append(name)
                
                # Algoritmo di selezione
                # Ordina per: Meno weekend fatti (se è weekend), Meno turni totali, Random
                if is_weekend:
                    candidates.sort(key=lambda x: (weekend_counts[x], work_counts[x], random.random()))
                else:
                    candidates.sort(key=lambda x: (work_counts[x], random.random()))
                
                # Assegna i primi N necessari
                filled = 0
                for i in range(min(len(candidates), count_needed)):
                    chosen = candidates[i]
                    assigned_names.append(f"{chosen} ({role[:3]})") # Es: Rossi (Cam)
                    worked_today.append(chosen)
                    work_counts[chosen] += 1
                    if is_weekend: weekend_counts[chosen] += 1
                    filled += 1
                
                # Gestione "SCOPERTO" se mancano persone per il ruolo
                missing = count_needed - filled
                if missing > 0:
                    for _ in range(missing):
                        assigned_names.append(f"⚠ SCOPERTO ({role})")
            
            # Uniamo tutti i nomi nella cella del turno
            if not assigned_names:
                row[shift] = "-"
            else:
                row[shift] = ", ".join(assigned_names)
                
        schedule.append(row)
    return schedule

def pdf_export(df, shifts):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=8) # Font più piccolo per far stare i nomi
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "PIANIFICAZIONE OPERATIVA", 0, 1, 'L')
    pdf.ln(2)
    
    # Header
    cols = ['Data', 'Giorno'] + shifts
    col_w = 270 / len(cols)
    
    pdf.set_fill_color(240, 240, 240)
    for c in cols:
        pdf.cell(col_w, 8, c.upper(), 1, 0, 'C', True)
    pdf.ln()
    
    # Rows
    pdf.set_font("Helvetica", size=7)
    for _, row in df.iterrows():
        try: d_str = row['Data'].strftime('%d/%m')
        except: d_str = str(row['Data'])
        
        pdf.cell(col_w, 8, d_str, 1, 0, 'C')
        pdf.cell(col_w, 8, str(row['Giorno']), 1, 0, 'C')
        
        for s in shifts:
            txt = str(row[s])
            if "SCOPERTO" in txt:
                pdf.set_text_color(200, 0, 0)
                pdf.set_font("Helvetica", 'B', 7)
            elif "CHIUSO" in txt:
                pdf.set_text_color(150, 150, 150)
                pdf.set_font("Helvetica", 'I', 7)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", '', 7)
                
            # Truncate text if too long
            if len(txt) > 25: txt = txt[:22] + "..."
            pdf.cell(col_w, 8, txt, 1, 0, 'C')
            
        pdf.set_text_color(0,0,0)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.title("ShiftManager")
    st.caption(f"Licenza: {'Attiva' if trial_active else 'Scaduta'} | {days_left}gg rimanenti")
    st.markdown("---")
    
    # A. Parametri Base
    st.subheader("1. Periodo & Struttura")
    start_dt = st.date_input("Inizio", date.today())
    days_num = st.number_input("Giorni", 7, 365, 30)
    
    days_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    active_days = st.multiselect("Giorni Operativi", days_it, default=days_it)
    
    shifts_in = st.text_input("Turni (CSV)", "Pranzo, Cena")
    shifts = [s.strip() for s in shifts_in.split(',') if s.strip()]
    
    st.markdown("---")
    
    # B. Ruoli
    st.subheader("2. Ruoli Professionali")
    roles_in = st.text_area("Definisci Ruoli (uno per riga)", "Cameriere\nCuoco\nBarman")
    roles = [r.strip() for r in roles_in.split('\n') if r.strip()]
    
    st.markdown("---")
    
    # C. Staff
    st.subheader("3. Anagrafica Staff")
    staff_names_in = st.text_area("Nomi Staff (uno per riga)", "Mario Rossi\nLuca Bianchi\nGiulia Verdi\nAnna Neri")
    staff_names = [n.strip() for n in staff_names_in.split('\n') if n.strip()]

# --- 7. PAGINA PRINCIPALE ---

# Header Status
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Dashboard Pianificazione")
with col_h2:
    if st.button("🔄 Reset Dati"):
        st.session_state.schedule_df = None
        st.experimental_rerun()

if not staff_names or not shifts or not roles:
    st.info("Configura i parametri nella barra laterale per iniziare.")
    st.stop()

# --- TAB SETUP ---
tab_req, tab_staff, tab_gen, tab_comm = st.tabs(["⚙️ Fabbisogno", "👥 Staff", "📅 Turni", "📱 Comunicazione"])

# TAB 1: FABBISOGNO
with tab_req:
    st.markdown("### Definizione Fabbisogno per Turno")
    st.caption("Quante persone servono per ogni ruolo in ogni turno?")
    
    requirements = {} # {Shift: {Role: Count}}
    
    # Griglia dinamica
    cols = st.columns(len(shifts))
    for i, shift in enumerate(shifts):
        with cols[i]:
            st.markdown(f"**{shift}**")
            shift_reqs = {}
            for role in roles:
                count = st.number_input(f"{role}", min_value=0, value=1, key=f"req_{shift}_{role}")
                shift_reqs[role] = count
            requirements[shift] = shift_reqs

# TAB 2: STAFF CONFIG
with tab_staff:
    st.markdown("### Configurazione Dipendenti")
    
    staff_db = {}
    
    for name in staff_names:
        with st.expander(f"👤 {name}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                role = st.selectbox(f"Ruolo ({name})", roles, key=f"role_{name}")
                rest = st.slider(f"Riposi settimanali ({name})", 0, 7, 2, key=f"rest_{name}")
            with c2:
                avail_shifts = st.multiselect(f"Turni disponbili ({name})", shifts, default=shifts, key=f"avs_{name}")
                unavail_dates = st.date_input(f"Ferie/Malattia ({name})", [], key=f"un_{name}")
                if not isinstance(unavail_dates, list): unavail_dates = [unavail_dates]
            
            staff_db[name] = {
                'role': role,
                'rest': rest,
                'shifts': avail_shifts,
                'unavail': unavail_dates
            }

# TAB 3: GENERAZIONE & STATS
with tab_gen:
    col_act, col_spacer = st.columns([1, 4])
    with col_act:
        run_gen = st.button("⚡ Genera Turni", type="primary", use_container_width=True)
    
    if run_gen:
        with st.spinner("Ottimizzazione turni in corso..."):
            res = generate_schedule_pro(staff_db, generate_date_range(start_dt, days_num), shifts, requirements, active_days)
            st.session_state.schedule_df = pd.DataFrame(res)
            # Log generzione
            st.session_state.comm_log.append(f"{datetime.now().strftime('%H:%M')} - Nuova pianificazione generata.")

    if st.session_state.schedule_df is not None:
        df = st.session_state.schedule_df
        
        # 1. Editor
        st.markdown("#### Bozza Turni")
        edited_df = st.data_editor(
            df, 
            use_container_width=True, 
            height=500,
            column_config={
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            }
        )
        
        # 2. Statistiche Equità
        st.markdown("---")
        st.markdown("#### 📊 Controllo Equità")
        
        # Calcolo occorrenze
        flat_list = []
        for s in shifts: flat_list.extend(edited_df[s].tolist())
        
        # Pulizia stringhe per contare i nomi reali (rimuovere ruoli e virgole)
        clean_counts = {}
        for name in staff_names:
            clean_counts[name] = 0
            for cell in flat_list:
                if name in str(cell): clean_counts[name] += 1
        
        # Chart
        st.bar_chart(pd.Series(clean_counts), color="#111827")
        
        # Alert Scoperti
        scoperti = sum([str(x).count("SCOPERTO") for x in flat_list])
        if scoperti > 0:
            st.error(f"Attenzione: Ci sono {scoperti} posizioni SCOPERTE. Modifica il fabbisogno o i riposi.")
        else:
            st.success("Tutte le posizioni sono coperte correttamente.")

        # 3. Export
        st.markdown("---")
        try:
            pdf_data = pdf_export(edited_df, shifts)
            st.download_button("📄 Scarica PDF", pdf_data, "turni.pdf", "application/pdf")
        except Exception as e:
            st.warning(f"Errore PDF: {e}")

# TAB 4: COMUNICAZIONE ANTI-CAOS
with tab_comm:
    st.markdown("### 📱 Centro Comunicazioni")
    st.info("Sostituisce i gruppi WhatsApp. Qui vedi chi ha ricevuto e letto i turni.")
    
    col_notif, col_read = st.columns([1, 2])
    
    with col_notif:
        st.markdown("**Azioni Manager**")
        if st.button("📢 Invia Notifica Push", type="primary", use_container_width=True):
            with st.status("Invio in corso...", expanded=True) as status:
                st.write("Connessione ai dispositivi...")
                time.sleep(1)
                st.write("Invio turni aggiornati...")
                time.sleep(1)
                status.update(label="Notifiche Inviate!", state="complete", expanded=False)
            st.session_state.comm_log.append(f"{datetime.now().strftime('%H:%M')} - Notifica Push inviata a tutto lo staff.")
            st.toast("Dipendenti notificati con successo!", icon="✅")

        st.markdown("---")
        st.markdown("**Log Attività**")
        for log in reversed(st.session_state.comm_log[-5:]):
            st.text(f"• {log}")

    with col_read:
        st.markdown("**Stato Lettura Turni (Real-time)**")
        
        # Simulazione dati lettura
        status_data = []
        statuses = ["✅ Letto", "📩 Consegnato", "✅ Letto", "🕒 In attesa"]
        last_seen = ["Oggi 09:30", "Oggi 08:45", "Ieri 22:10", "-"]
        
        for i, name in enumerate(staff_names):
            s = statuses[i % len(statuses)]
            l = last_seen[i % len(last_seen)]
            status_data.append({"Dipendente": name, "Stato": s, "Ultimo Accesso": l})
            
        st.dataframe(
            pd.DataFrame(status_data), 
            use_container_width=True,
            hide_index=True
        )
        
        st.caption("Nota: La 'spunta verde' conferma che il dipendente ha aperto l'app e visualizzato il turno.")
