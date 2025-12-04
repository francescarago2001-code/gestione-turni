import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA (PROFESSIONAL) ---
st.set_page_config(
    page_title="Pianificazione Turni | Enterprise",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STILE "CORPORATE / PROFESSIONAL" ---
st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp {
        background-color: #f4f6f9; /* Grigio molto chiaro, tipico delle dashboard */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: #2c3e50 !important; /* Blu scuro professionale */
        font-weight: 600;
    }
    
    /* Card/Contenitori Espandibili */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        color: #34495e;
    }
    
    /* Bottoni */
    .stButton>button {
        background-color: #2c3e50; /* Blu Navy */
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #34495e;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Tabella */
    .dataframe {
        border-collapse: collapse !important;
        border: 1px solid #dee2e6 !important;
        font-size: 14px;
    }
    
    /* Rimuove padding extra */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
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
    
    # Contatori
    work_counts = {name: 0 for name in staff_data.keys()}
    targets = {}
    
    # Calcolo Target
    for name, data in staff_data.items():
        targets[name] = calculate_target(len(date_list), data['weekly_rest'], len(data['ferie']))

    for current_day in date_list:
        day_schedule = {
            "Data": current_day,
            "Giorno": current_day.strftime("%A")
        }
        
        # Lista di chi ha già lavorato OGGI (per evitare doppi turni nello stesso giorno)
        worked_today = []
        
        # Recuperiamo la schedulazione di IERI per il controllo consecutività
        yesterday_schedule = schedule[-1] if len(schedule) > 0 else None
        
        for shift_name in shift_types:
            candidates = []
            
            for name, data in staff_data.items():
                # 1. Ferie
                if current_day in data['ferie']: continue
                # 2. Indisponibilità
                if current_day in data['indisponibilita']: continue
                # 3. Target Raggiunto
                if work_counts[name] >= targets[name]: continue
                # 4. Già lavorato oggi (niente doppi turni)
                if name in worked_today: continue
                
                # 5. CONTROLLO CONSECUTIVITÀ (Nuova Logica)
                # Se ieri hai fatto "Mattina", oggi non puoi fare "Mattina".
                if yesterday_schedule:
                    # Controlliamo se ieri, in QUESTO turno specifico, c'era questa persona
                    if yesterday_schedule.get(shift_name) == name:
                        continue
                
                candidates.append(name)
            
            selected_person = "SCOPERTO"
            
            if candidates:
                # Ordina per chi ha lavorato meno
                candidates.sort(key=lambda x: work_counts[x])
                
                # Filtra i migliori
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
    
    # Intestazione Report
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(44, 62, 80) # Blu Navy
    pdf.cell(0, 10, "PIANIFICAZIONE OPERATIVA TURNI", 0, 1, 'L')
    pdf.set_font("Helvetica", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generato il: {date.today().strftime('%d/%m/%Y')}", 0, 1, 'L')
    pdf.ln(5)
    
    # Calcoli Layout
    page_width = 275
    date_col_w = 30
    day_col_w = 30
    remaining_w = page_width - date_col_w - day_col_w
    shift_col_w = remaining_w / len(shift_cols)
    
    # Header Tabella
    pdf.set_fill_color(240, 240, 240) # Sfondo grigio chiaro header
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(date_col_w, 10, "DATA", 1, 0, 'C', True)
    pdf.cell(day_col_w, 10, "GIORNO", 1, 0, 'C', True)
    for s in shift_cols:
        col_name = s.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(shift_col_w, 10, col_name.upper(), 1, 0, 'C', True)
    pdf.ln()
    
    # Body
    pdf.set_font("Helvetica", size=9)
    for _, row in dataframe.iterrows():
        d_str = row['Data'].strftime('%d/%m')
        day_str = row['Giorno'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(date_col_w, 10, d_str, 1, 0, 'C')
        pdf.cell(day_col_w, 10, day_str, 1, 0, 'C')
        
        for s in shift_cols:
            person = str(row[s])
            person_enc = person.encode('latin-1', 'replace').decode('latin-1')
            
            if person == "SCOPERTO":
                pdf.set_text_color(220, 53, 69) # Rosso Bootstrap
                pdf.set_font("Helvetica", 'B', 9)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", size=9)
                
            pdf.cell(shift_col_w, 10, person_enc, 1, 0, 'C')
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    
    st.markdown("##### 1. Periodo")
    start_date = st.date_input("Data Inizio", date.today())
    duration = st.number_input("Giorni totali", 7, 365, 30)
    
    st.markdown("##### 2. Turni")
    shifts_input = st.text_input("Tipologie (es. Mattina, Sera)", "Mattina, Pomeriggio")
    shift_types = [s.strip() for s in shifts_input.split(',') if s.strip()]
    
    st.markdown("##### 3. Team")
    staff_input = st.text_area("Elenco Dipendenti", "Rossi\nBianchi\nVerdi\nNeri")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]
    
    st.info("ℹ️ Il sistema evita che un dipendente faccia lo stesso turno per 2 giorni consecutivi.")

# --- MAIN LAYOUT ---
st.title("Gestione Turni Aziendali")
st.markdown("Strumento professionale per la generazione automatica dei turni operativi.")
st.markdown("---")

if not staff_names or not shift_types:
    st.warning("⚠️ Configurare il personale e i turni nella barra laterale per procedere.")
    st.stop()

# --- INPUT DIPENDENTI (GRID LAYOUT) ---
st.subheader("Parametri Risorse Umane")
staff_data = {}
cols = st.columns(3) # Layout a 3 colonne per professionalità

date_range = generate_date_range(start_date, duration)

for i, name in enumerate(staff_names):
    with cols[i % 3]:
        with st.expander(f"👤 {name}", expanded=False):
            w_rest = st.number_input(f"Riposi settimanali", 0, 7, 1, key=f"wr_{name}")
            leaves = st.multiselect("Ferie / Malattia", date_range, format_func=lambda x: x.strftime('%d/%m'), key=f"lv_{name}")
            unavail = st.multiselect("Indisponibilità", [d for d in date_range if d not in leaves], format_func=lambda x: x.strftime('%d/%m'), key=f"un_{name}")
            staff_data[name] = {'weekly_rest': w_rest, 'ferie': leaves, 'indisponibilita': unavail}

st.markdown("---")

# --- GENERAZIONE ---
if st.button("Genera Pianificazione", type="primary", use_container_width=True):
    
    # Processo
    schedule = generate_schedule(staff_data, date_range, shift_types)
    df = pd.DataFrame(schedule)
    
    # Localizzazione
    it_days = {'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì', 
               'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'}
    df['Giorno'] = df['Giorno'].map(it_days)
    
    # Clean Columns
    cols_order = ['Data', 'Giorno'] + shift_types
    df = df[cols_order]

    # --- OUTPUT VISIVO ---
    st.subheader("🗓️ Calendario Turni")
    
    # Funzione Stile Tabella
    def style_schedule(val):
        if val == "SCOPERTO":
            return 'background-color: #fee2e2; color: #b91c1c; font-weight: bold; border: 1px solid #fecaca;' # Rosso professionale
        return 'color: #374151;'

    st.dataframe(
        df.style.map(style_schedule),
        use_container_width=True,
        height=600,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        },
        hide_index=True
    )
    
    # --- OUTPUT PDF ---
    st.markdown("### Esportazione")
    col_pdf, _ = st.columns([1, 4])
    
    with col_pdf:
        try:
            pdf_bytes = export_to_pdf(df, shift_types)
            st.download_button(
                label="📄 Scarica Report PDF",
                data=pdf_bytes,
                file_name="Report_Turni.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore nella generazione del PDF: {e}")
