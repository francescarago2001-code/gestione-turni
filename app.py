import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA (MINIMALISMO ASSOLUTO) ---
st.set_page_config(
    page_title="Pianificazione",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ANESTETICO (BIANCO/NERO/GRIGIO) ---
st.markdown("""
    <style>
    /* Reset totale colori */
    .stApp {
        background-color: #ffffff;
        color: #000000;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Intestazioni sottili */
    h1, h2, h3, h4 {
        font-weight: 400 !important;
        color: #333333 !important;
        letter-spacing: -0.5px;
    }
    
    /* Input e Sidebar puliti */
    .css-1d391kg, .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #000;
        border: 1px solid #cccccc;
        border-radius: 0px;
    }
    
    /* Bottoni minimali neri */
    .stButton>button {
        background-color: #000000;
        color: #ffffff;
        border: none;
        border-radius: 0px;
        padding: 8px 16px;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: #ffffff;
    }
    
    /* Tabelle pulite */
    .dataframe {
        font-family: 'Helvetica', sans-serif;
        font-size: 13px;
        border: none !important;
    }
    
    /* Rimozione decorazioni Streamlit */
    header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI LOGICHE ---
def generate_date_range(start_date, num_days):
    return [start_date + timedelta(days=i) for i in range(num_days)]

def calculate_target(total_days, weekly_rest, vacation_days):
    weeks = total_days / 7
    total_rest = round(weeks * weekly_rest)
    target = total_days - total_rest - vacation_days
    return max(0, target)

def generate_schedule(staff_data, date_list, shift_types):
    schedule = []
    
    # Contatore turni per equità (calcolato in background)
    work_counts = {name: 0 for name in staff_data.keys()}
    targets = {}
    
    # Calcolo target lavorativo per ogni persona
    for name, data in staff_data.items():
        targets[name] = calculate_target(len(date_list), data['weekly_rest'], len(data['ferie']))

    for current_day in date_list:
        day_schedule = {
            "Data": current_day,
            "Giorno": current_day.strftime("%A")
        }
        
        # Lista di chi ha già lavorato OGGI (per evitare doppi turni)
        worked_today = []
        
        # Iteriamo attraverso i tipi di turno (es. Mattina -> Pomeriggio -> Notte)
        for shift_name in shift_types:
            candidates = []
            
            for name, data in staff_data.items():
                # 1. È in ferie?
                if current_day in data['ferie']: continue
                
                # 2. Ha segnato indisponibilità specifica?
                if current_day in data['indisponibilita']: continue
                
                # 3. Ha già raggiunto il suo target mensile?
                if work_counts[name] >= targets[name]: continue
                
                # 4. HA GIÀ LAVORATO OGGI? (Vincolo anti-doppio turno)
                if name in worked_today: continue
                
                candidates.append(name)
            
            selected_person = "SCOPERTO"
            
            if candidates:
                # Ordina per chi ha lavorato meno (equità)
                candidates.sort(key=lambda x: work_counts[x])
                
                # Mischia i pari merito
                min_val = work_counts[candidates[0]]
                best_candidates = [c for c in candidates if work_counts[c] == min_val]
                
                chosen = random.choice(best_candidates)
                
                selected_person = chosen
                work_counts[chosen] += 1
                worked_today.append(chosen) # Aggiungi alla lista di oggi
            
            day_schedule[shift_name] = selected_person
            
        schedule.append(day_schedule)
            
    return schedule

# --- PDF EXPORT DINAMICO ---
def export_to_pdf(dataframe, shift_cols):
    pdf = FPDF(orientation='L', unit='mm', format='A4') # Landscape per più colonne
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    # Intestazione
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "PIANIFICAZIONE TURNI", 0, 1, 'L')
    pdf.ln(5)
    
    # Calcolo larghezza colonne dinamico
    page_width = 280 # A4 Landscape width approx
    date_col_w = 30
    day_col_w = 30
    
    remaining_w = page_width - date_col_w - day_col_w
    shift_col_w = remaining_w / len(shift_cols)
    
    # Header Tabella
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(date_col_w, 10, "DATA", 1)
    pdf.cell(day_col_w, 10, "GIORNO", 1)
    for s in shift_cols:
        col_name = s.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(shift_col_w, 10, col_name.upper(), 1)
    pdf.ln()
    
    # Dati
    pdf.set_font("Helvetica", size=9)
    for _, row in dataframe.iterrows():
        d_str = row['Data'].strftime('%d/%m')
        day_str = row['Giorno'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(date_col_w, 10, d_str, 1)
        pdf.cell(day_col_w, 10, day_str, 1)
        
        for s in shift_cols:
            person = str(row[s])
            person_enc = person.encode('latin-1', 'replace').decode('latin-1')
            
            if person == "SCOPERTO":
                pdf.set_text_color(150, 0, 0) # Rosso scuro elegante
                pdf.set_font("Helvetica", 'B', 9)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", size=9)
                
            pdf.cell(shift_col_w, 10, person_enc, 1)
            
        pdf.set_text_color(0, 0, 0) # Reset colore
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA ---

# Sidebar
with st.sidebar:
    st.markdown("### CONFIGURAZIONE")
    
    start_date = st.date_input("Inizio", date.today())
    duration = st.number_input("Durata (gg)", 7, 365, 30)
    
    st.markdown("---")
    st.markdown("### STRUTTURA TURNI")
    # Input tipi di turno
    shifts_input = st.text_input("Nomi Turni (separati da virgola)", "Mattina, Pomeriggio")
    shift_types = [s.strip() for s in shifts_input.split(',') if s.strip()]
    
    st.markdown("---")
    st.markdown("### PERSONALE")
    staff_input = st.text_area("Nomi", "Rossi\nBianchi\nVerdi\nNeri")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# Main
st.title("Gestione Operativa")

if not staff_names or not shift_types:
    st.text("Inserire personale e tipi di turno nella barra laterale.")
    st.stop()

# Configurazione Dettagliata (Minimal Expanders)
staff_data = {}
cols = st.columns(3)

for i, name in enumerate(staff_names):
    with cols[i % 3]:
        with st.expander(f"{name}", expanded=False):
            w_rest = st.number_input(f"Riposi settimanali", 0, 7, 1, key=f"wr_{name}")
            date_range = generate_date_range(start_date, duration)
            leaves = st.multiselect("Ferie", date_range, format_func=lambda x: x.strftime('%d/%m'), key=f"lv_{name}")
            unavail = st.multiselect("Indisponibilità", [d for d in date_range if d not in leaves], format_func=lambda x: x.strftime('%d/%m'), key=f"un_{name}")
            staff_data[name] = {'weekly_rest': w_rest, 'ferie': leaves, 'indisponibilita': unavail}

st.markdown("<br>", unsafe_allow_html=True)

if st.button("ELABORA PIANO"):
    
    # Generazione
    schedule = generate_schedule(staff_data, date_range, shift_types)
    df = pd.DataFrame(schedule)
    
    # Traduzione giorni
    it_days = {'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì', 
               'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'}
    df['Giorno'] = df['Giorno'].map(it_days)
    
    # Riordino colonne: Data, Giorno, [Turni...]
    cols_order = ['Data', 'Giorno'] + shift_types
    df = df[cols_order]

    # Visualizzazione
    st.markdown("### PIANO GENERATO")
    
    # Style: Evidenzia solo SCOPERTO con rosso testo, resto pulito
    def style_schedule(val):
        if val == "SCOPERTO":
            return 'color: #d93025; font-weight: bold;'
        return 'color: #000000;'

    st.dataframe(
        df.style.map(style_schedule),
        use_container_width=True,
        height=600,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        },
        hide_index=True
    )
    
    # Download
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("SCARICA CSV", csv, "turni.csv", "text/csv", use_container_width=True)
    with col_dl2:
        try:
            pdf_bytes = export_to_pdf(df, shift_types)
            st.download_button("SCARICA PDF", pdf_bytes, "turni.pdf", "application/pdf", use_container_width=True)
        except Exception as e:
            st.error("Errore PDF")
