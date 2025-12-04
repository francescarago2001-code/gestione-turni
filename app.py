import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Gestione Turni Operativi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STILE BUSINESS (CLEAN, NO EMOJI) ---
st.markdown("""
    <style>
    /* Reset e Font */
    .stApp {
        background-color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333333;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* Intestazioni */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 500;
        letter-spacing: -0.5px;
    }
    
    /* Bottoni */
    .stButton>button {
        background-color: #2c3e50; /* Blu Scuro */
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        width: 100%;
        transition: background 0.3s;
    }
    .stButton>button:hover {
        background-color: #1a252f;
    }
    
    /* Expander e Input */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        color: #495057;
        font-size: 14px;
    }
    div[data-baseweb="input"] {
        border-radius: 4px;
    }
    
    /* Messaggi */
    .stAlert {
        border: 1px solid #dee2e6;
        background-color: #f8f9fa;
        color: #333;
    }
    
    /* Spaziatura */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONE STATO (PER MANTENERE I DATI MENTRE SI MODIFICA) ---
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None

# --- FUNZIONI LOGICHE ---
def generate_date_range(start_date, num_days):
    return [start_date + timedelta(days=i) for i in range(num_days)]

def calculate_target(total_days, weekly_rest):
    # Calcolo semplice: Totale giorni - (Settimane * Riposi settimanali)
    weeks = total_days / 7
    total_rest = round(weeks * weekly_rest)
    target = total_days - total_rest
    return max(0, target)

def generate_schedule(staff_data, date_list, shift_types, prevent_consecutive):
    schedule = []
    
    # Inizializza contatori
    work_counts = {name: 0 for name in staff_data.keys()}
    targets = {}
    
    # Calcolo Target Lavorativo
    for name, data in staff_data.items():
        targets[name] = calculate_target(len(date_list), data['weekly_rest'])

    for current_day in date_list:
        day_schedule = {
            "Data": current_day,
            "Giorno": current_day.strftime("%A")
        }
        
        # Lista di chi ha già lavorato oggi
        worked_today = []
        
        # Recupera schedulazione di ieri (se esiste)
        yesterday_schedule = schedule[-1] if len(schedule) > 0 else None
        
        for shift_name in shift_types:
            candidates = []
            
            for name, data in staff_data.items():
                # 1. Target Raggiunto?
                if work_counts[name] >= targets[name]: continue
                
                # 2. Già lavorato oggi?
                if name in worked_today: continue
                
                # 3. CONTROLLO CONSECUTIVITÀ (OPZIONALE)
                if prevent_consecutive and yesterday_schedule:
                    # Se ieri in questo turno c'era questa persona, saltala
                    if yesterday_schedule.get(shift_name) == name:
                        continue
                
                candidates.append(name)
            
            selected_person = "SCOPERTO" # Placeholder testuale
            
            if candidates:
                # Ordina per chi ha lavorato meno (equità)
                candidates.sort(key=lambda x: work_counts[x])
                
                # Prendi i candidati con il minor numero di turni (random tra i migliori)
                min_val = work_counts[candidates[0]]
                best_candidates = [c for c in candidates if work_counts[c] == min_val]
                
                chosen = random.choice(best_candidates)
                selected_person = chosen
                work_counts[chosen] += 1
                worked_today.append(chosen)
            
            day_schedule[shift_name] = selected_person
            
        schedule.append(day_schedule)
            
    return schedule

# --- PDF EXPORT ---
def export_to_pdf(dataframe, shift_cols):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    # Intestazione
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "PIANIFICAZIONE TURNI", 0, 1, 'L')
    pdf.ln(5)
    
    # Setup Colonna
    page_width = 275
    date_w = 35
    day_w = 30
    rem_w = page_width - date_w - day_w
    shift_w = rem_w / len(shift_cols)
    
    # Header Tabella
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(date_w, 10, "DATA", 1, 0, 'C', True)
    pdf.cell(day_w, 10, "GIORNO", 1, 0, 'C', True)
    for s in shift_cols:
        col_name = s.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(shift_w, 10, col_name.upper(), 1, 0, 'C', True)
    pdf.ln()
    
    # Dati
    pdf.set_font("Helvetica", size=9)
    for _, row in dataframe.iterrows():
        # Gestione date (se è datetime o stringa modificata)
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
            
            # Evidenzia SCOPERTO in rosso nel PDF
            if val == "SCOPERTO":
                pdf.set_text_color(180, 0, 0)
                pdf.set_font("Helvetica", 'B', 9)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", size=9)
                
            pdf.cell(shift_w, 10, val_enc, 1, 0, 'C')
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.header("Impostazioni")
    
    st.subheader("Periodo")
    start_date = st.date_input("Data Inizio", date.today())
    duration = st.number_input("Giorni totali", 1, 365, 30)
    
    st.subheader("Turni")
    shifts_input = st.text_input("Nomi Turni (separati da virgola)", "Mattina, Pomeriggio")
    shift_types = [s.strip() for s in shifts_input.split(',') if s.strip()]
    
    st.subheader("Regole")
    prevent_consecutive = st.checkbox("Evita stesso turno consecutivo", value=True, help="Se attivo, chi fa Mattina oggi non farà Mattina domani.")
    
    st.subheader("Risorse")
    staff_input = st.text_area("Lista Dipendenti", "Rossi\nBianchi\nVerdi\nNeri")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# --- MAIN ---
st.title("Gestione Turni")

if not staff_names or not shift_types:
    st.warning("Compilare le impostazioni nella barra laterale per procedere.")
    st.stop()

# --- CONFIGURAZIONE RIPOSI ---
st.subheader("Configurazione Riposi")
st.caption("Indicare i giorni di riposo settimanali desiderati per ogni risorsa.")

staff_data = {}
cols = st.columns(3)
for i, name in enumerate(staff_names):
    with cols[i % 3]:
        # Minimal input: solo riposi
        w_rest = st.number_input(f"{name}", 0, 7, 2, key=f"wr_{name}")
        staff_data[name] = {'weekly_rest': w_rest}

st.markdown("---")

# --- GENERAZIONE ---
if st.button("Genera Bozza Turni", type="primary"):
    date_range = generate_date_range(start_date, duration)
    
    # Calcolo algoritmo
    schedule_data = generate_schedule(staff_data, date_range, shift_types, prevent_consecutive)
    
    # Creazione DataFrame
    df = pd.DataFrame(schedule_data)
    
    # Traduzione Giorni
    it_days = {'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì', 
               'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'}
    df['Giorno'] = df['Giorno'].map(it_days)
    
    # Ordine Colonne
    cols_order = ['Data', 'Giorno'] + shift_types
    df = df[cols_order]
    
    # Salvataggio in session_state
    st.session_state.schedule_df = df

# --- VISUALIZZAZIONE E MODIFICA ---
if st.session_state.schedule_df is not None:
    st.subheader("Pianificazione Operativa (Modificabile)")
    st.caption("Clicca sulle celle per modificare manualmente le assegnazioni.")
    
    # Data Editor: permette all'utente di modificare la tabella
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
    
    st.markdown("### Esportazione")
    col_pdf, _ = st.columns([1, 5])
    
    with col_pdf:
        try:
            # Genera il PDF basandosi su EDITED_DF (quindi include le modifiche manuali)
            pdf_bytes = export_to_pdf(edited_df, shift_types)
            st.download_button(
                label="Scarica PDF Definitivo",
                data=pdf_bytes,
                file_name="Piano_Turni.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione PDF: {e}")
