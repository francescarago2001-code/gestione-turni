import streamlit as st
import pandas as pd
import random
from fpdf import FPDF
import base64

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestore Turni Semplice", layout="centered")

# --- 1. GESTIONE LOGIN (SEMPLICE) ---
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Accesso Gestore Turni")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Entra"):
            # QUI PUOI CAMBIARE USERNAME E PASSWORD
            if user == "admin" and password == "1234": 
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenziali errate")
        return False
    return True

if not check_login():
    st.stop()

# --- INTERFACCIA PRINCIPALE ---
st.title("📅 Generatore Turni & PDF")
st.sidebar.button("Esci / Logout", on_click=lambda: st.session_state.update(logged_in=False))

# --- 2. CONFIGURAZIONE GENERALE ---
st.header("1. Impostazioni")
col1, col2 = st.columns(2)
with col1:
    giorni_lavorativi = st.multiselect(
        "Seleziona i giorni di lavoro:",
        ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        default=["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
    )
with col2:
    periodo = st.radio("Periodo", ["Settimanale (1 settimana)", "Mensile (4 settimane)"])

# --- 3. INSERIMENTO DIPENDENTI ---
st.header("2. Dipendenti")
st.info("Scrivi i nomi dei dipendenti separati da una virgola.")
nomi_input = st.text_area("Nomi dipendenti", "Mario Rossi, Luca Bianchi, Giulia Verdi")
lista_dipendenti = [x.strip() for x in nomi_input.split(',') if x.strip()]

# --- 4. INDISPONIBILITÀ ---
st.header("3. Indisponibilità")
indisponibilita = {}
if lista_dipendenti:
    with st.expander("Segna chi NON può lavorare in certi giorni"):
        for dip in lista_dipendenti:
            indisponibilita[dip] = st.multiselect(f"Giorni OFF per {dip}", giorni_lavorativi)

# --- 5. GENERAZIONE TURNI ---
if st.button("Genera Turni"):
    if not lista_dipendenti or not giorni_lavorativi:
        st.error("Inserisci almeno un dipendente e un giorno lavorativo.")
    else:
        st.success("Turni generati!")
        
        # Logica base: Se è mensile, moltiplichiamo i giorni per 4
        giorni_finali = giorni_lavorativi * (4 if "Mensile" in periodo else 1)
        
        schedule_data = []
        
        # Algoritmo Semplificato: Assegna a caso tra chi è disponibile
        for giorno in giorni_finali:
            disponibili = [d for d in lista_dipendenti if giorno not in indisponibilita.get(d, [])]
            
            if not disponibili:
                turno = "NESSUNO DISPONIBILE"
            else:
                # Qui puoi modificare la logica (es. turnazione rotativa)
                turno = random.choice(disponibili) 
            
            schedule_data.append({"Giorno": giorno, "Dipendente": turno})
            
        df = pd.DataFrame(schedule_data)
        st.dataframe(df, use_container_width=True)

        # --- 6. CREAZIONE PDF ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Tabella Turni", ln=1, align='C')
        
        pdf.set_font("Arial", size=10)
        col_width = pdf.w / 2.5
        row_height = 10
        
        # Intestazione
        pdf.cell(col_width, row_height, "Giorno", border=1)
        pdf.cell(col_width, row_height, "Dipendente Assegnato", border=1)
        pdf.ln(row_height)
        
        # Righe
        for index, row in df.iterrows():
            pdf.cell(col_width, row_height, str(row['Giorno']), border=1)
            pdf.cell(col_width, row_height, str(row['Dipendente']), border=1)
            pdf.ln(row_height)
            
        # Download
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="turni.pdf">📄 Scarica PDF Turni</a>'
        st.markdown(href, unsafe_allow_html=True)
