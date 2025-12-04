import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
from fpdf import FPDF
import base64

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Gestione Turni | Minimal",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STILE MINIMAL E BIANCO ---
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #333333;
        font-family: 'Arial', sans-serif;
    }
    h1, h2, h3 {
        color: #000000 !important;
    }
    .stat-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Rimuove padding eccessivo in alto */
    .block-container {
        padding-top: 2rem;
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

    for current_day in date_list:
        candidates = []
        for name, data in staff_data.items():
            if current_day in data['ferie']: continue
            if current_day in data['indisponibilita']: continue
            if work_counts[name] >= targets[name]: continue
            candidates.append(name)
        
        status = "SCOPERTO" # Rimosso emoji per evitare errori nel PDF base
        if candidates:
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

# --- FUNZIONE GENERAZIONE PDF ---
def export_to_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Gestione Turni - Report", ln=True, align='C')
    pdf.ln(10)
    
    # Intestazioni Tabella
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(40, 10, "Giorno", 1)
    pdf.cell(60, 10, "Dipendente", 1)
    pdf.ln()
    
    # Dati
    pdf.set_font("Arial", size=10)
    for index, row in dataframe.iterrows():
        # Formattazione data stringa
        date_str = row['Data'].strftime('%d/%m/%Y')
        # Encoding latin-1 per caratteri italiani
        day_str = row['Giorno'].encode('latin-1', 'replace').decode('latin-1')
        staff_str = str(row['Turno']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(40, 10, date_str, 1)
        pdf.cell(40, 10, day_str, 1)
        
        # Se è scoperto colora di rosso (nel PDF non si colora facilmente la cella standard, usiamo testo)
        if staff_str == "SCOPERTO":
            pdf.set_text_color(255, 0, 0)
            pdf.cell(60, 10, staff_str, 1)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(60, 10, staff_str, 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛠️ Impostazioni")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Inizio", date.today())
    with col_d2:
        duration_days = st.number_input("Giorni", 7, 365, 30)
    
    date_range = generate_date_range(start_date, duration_days)
    
    st.markdown("### 👥 Personale")
    staff_input = st.text_area("Lista Nomi", "Andrea\nLuca\nSofia\nChiara")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# --- MAIN PAGE ---
st.title("Gestione Turni Minimal")
if not staff_names:
    st.warning("Aggiungi i nomi nella sidebar per iniziare.")
    st.stop()

# Configurazione Staff
staff_data = {}
cols = st.columns(3)
for i, name in enumerate(staff_names):
    with cols[i % 3]:
        with st.expander(f"👤 {name}", expanded=False):
            w_rest = st.number_input(f"Riposi/Settimana", 0, 7, 2, key=f"wr_{name}")
            leaves = st.multiselect("Ferie", date_range, format_func=lambda x: x.strftime('%d/%m'), key=f"lv_{name}")
            unavail = st.multiselect("Indisponibile", [d for d in date_range if d not in leaves], format_func=lambda x: x.strftime('%d/%m'), key=f"un_{name}")
            staff_data[name] = {'weekly_rest': w_rest, 'ferie': leaves, 'indisponibilita': unavail}

st.markdown("---")

# Generazione
if st.button("Genera Turni", type="primary", use_container_width=True):
    sched, counts, targets = generate_schedule(staff_data, date_range)
    df = pd.DataFrame(sched)
    
    # Traduzione Giorni
    it_days = {'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì', 
               'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'}
    df['Giorno'] = df['Giorno'].map(it_days)

    col_res, col_stat = st.columns([2, 1])

    with col_res:
        st.subheader("Calendario")
        # Visualizzazione tabella colorata
        def highlight_vals(val):
            return 'background-color: #ffebee; color: red; font-weight: bold' if val == "SCOPERTO" else ''
        
        st.dataframe(
            df.style.map(highlight_vals, subset=['Turno']),
            use_container_width=True,
            height=500,
            hide_index=True
        )

    with col_stat:
        st.subheader("Statistiche")
        for name in staff_names:
            done = counts[name]
            goal = targets[name]
            diff = done - goal
            
            # Colore Bordo Card
            b_col = "#4CAF50" if diff == 0 else "#FF9800" if diff > 0 else "#F44336"
            msg = "Target Raggiunto" if diff == 0 else f"{diff} Extra" if diff > 0 else f"{diff} Mancanti"
            
            st.markdown(f"""
            <div class="stat-card" style="border-left: 5px solid {b_col};">
                <strong>{name}</strong><br>
                <span style="font-size:12px; color:#666">Turni: {done} / {goal}</span><br>
                <span style="font-size:12px; font-weight:bold; color:{b_col}">{msg}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📥 Download")
        
        # 1. CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Scarica CSV (Excel)", csv, "turni.csv", "text/csv", use_container_width=True)
        
        # 2. PDF
        try:
            pdf_bytes = export_to_pdf(df)
            st.download_button(
                label="Scarica PDF",
                data=pdf_bytes,
                file_name="turni_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione PDF: {e}")
