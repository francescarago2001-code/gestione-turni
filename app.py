import streamlit as st
import pandas as pd
import random
from fpdf import FPDF
import base64

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Gestore Turni Pro", layout="centered")

# --- 1. RECUPERO DATI DALLA "CASSAFORTE" (SECRETS) ---
# Se non ci sono segreti impostati, usiamo valori di prova per non far rompere l'app
try:
    USER_SEGRETO = st.secrets["username"]
    PASS_SEGRETO = st.secrets["password"]
    # Recuperiamo la lista dipendenti come stringa e la trasformiamo in lista
    DIPENDENTI_BASE = st.secrets["dipendenti"].split(",")
except:
    st.error("⚠️ Configurazione mancante! Imposta i Secrets nella dashboard di Streamlit.")
    st.stop()

# --- 2. GESTIONE LOGIN ---
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Accesso Riservato")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Entra"):
            # Confronta con i dati nella cassaforte
            if user == USER_SEGRETO and password == PASS_SEGRETO: 
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenziali errate")
        return False
    return True

if not check_login():
    st.stop()

# --- INTERFACCIA PRINCIPALE ---
st.title(f"📅 Turni: {st.secrets.get('azienda', 'Generico')}")
st.sidebar.button("Esci", on_click=lambda: st.session_state.update(logged_in=False))

# --- 3. IMPOSTAZIONI ---
st.header("1. Configurazione")
col1, col2 = st.columns(2)
with col1:
    giorni_lavorativi = st.multiselect(
        "Giorni di lavoro:",
        ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        default=["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
    )
with col2:
    periodo = st.radio("Durata", ["Settimanale", "Mensile"])

# --- 4. DIPENDENTI (CARICATI DAI SECRETS) ---
st.header("2. Dipendenti")
# Qui mostriamo i dipendenti caricati dai Secrets, ma permettiamo di aggiungerne temporaneamente
nomi_input = st.text_area(
    "Modifica lista per questa sessione (i salvataggi fissi li fa l'amministratore)", 
    ", ".join(DIPENDENTI_BASE)
)
lista_dipendenti = [x.strip() for x in nomi_input.split(',') if x.strip()]

# --- 5. INDISPONIBILITÀ ---
st.header("3. Indisponibilità")
indisponibilita = {}
if lista_dipendenti:
    with st.expander("Segna chi NON può lavorare"):
        for dip in lista_dipendenti:
            indisponibilita[dip] = st.multiselect(f"No turno per {dip}", giorni_lavorativi)

# --- 6. GENERA E SCARICA (LOGICA IDENTICA A PRIMA) ---
if st.button("Genera Turni"):
    if not lista_dipendenti:
        st.error("Nessun dipendente inserito.")
    else:
        st.success("Fatto!")
        moltiplicatore = 4 if "Mensile" in periodo else 1
        giorni_finali = giorni_lavorativi * moltiplicatore
        
        schedule_data = []
        for giorno in giorni_finali:
            disponibili = [d for d in lista_dipendenti if giorno not in indisponibilita.get(d, [])]
            turno = random.choice(disponibili) if disponibili else "NESSUNO"
            schedule_data.append({"Giorno": giorno, "Dipendente": turno})
            
        df = pd.DataFrame(schedule_data)
        st.dataframe(df, use_container_width=True)

        # PDF Export
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Turni - {st.secrets.get('azienda', '')}", ln=1, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        col_w = 90
        pdf.cell(col_w, 10, "Giorno", 1)
        pdf.cell(col_w, 10, "Dipendente", 1)
        pdf.ln()
        
        for _, row in df.iterrows():
            pdf.cell(col_w, 10, str(row['Giorno']), 1)
            pdf.cell(col_w, 10, str(row['Dipendente']), 1)
            pdf.ln()
            
        b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="turni.pdf">📄 Scarica PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
