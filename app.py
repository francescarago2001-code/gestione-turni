import streamlit as st
import pandas as pd
import random
from fpdf import FPDF
import base64
from datetime import timedelta, date

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Gestore Turni", layout="wide")

# --- 1. RECUPERO DIPENDENTI BASE (DAI SECRETS) ---
# Cerchiamo di prendere i nomi salvati nel server, altrimenti mettiamo dei nomi di esempio
try:
    NOMI_DEFAULT = st.secrets["dipendenti"] # Es: "Mario, Luigi, Anna"
    AZIENDA = st.secrets.get("azienda", "La Mia Azienda")
except:
    NOMI_DEFAULT = "Mario Rossi, Luigi Bianchi, Anna Verdi"
    AZIENDA = "Gestione Turni"

st.title(f"📅 {AZIENDA} - Generatore Turni")

# --- 2. INPUT DIPENDENTI (MODIFICABILE) ---
st.write("---")
st.subheader("1. Inserisci i Dipendenti")
st.info("Modifica la lista qui sotto. Separa i nomi con una virgola.")

# QUI C'È LA MODIFICA: La casella di testo parte con i nomi salvati, ma l'utente può cambiarli!
nomi_input = st.text_area("Lista Dipendenti:", value=NOMI_DEFAULT, height=100)

# Trasformiamo il testo in una lista pulita
lista_dipendenti = [x.strip() for x in nomi_input.split(',') if x.strip()]

if not lista_dipendenti:
    st.warning("⚠️ Inserisci almeno un nome per continuare.")
    st.stop()

# --- 3. IMPOSTAZIONI CALENDARIO E TURNI ---
st.write("---")
st.subheader("2. Impostazioni Turni")

col1, col2, col3 = st.columns(3)
with col1:
    data_inizio = st.date_input("Data Inizio", date.today())
with col2:
    data_fine = st.date_input("Data Fine", date.today() + timedelta(days=6))
with col3:
    turni_disponibili = st.multiselect(
        "Tipi di turno:",
        ["Mattina", "Pomeriggio", "Notte", "Spezzato", "Extra"],
        default=["Mattina", "Pomeriggio"]
    )

# --- 4. INDISPONIBILITÀ (RIPOSI) ---
st.write("---")
st.subheader("3. Gestione Riposi e Indisponibilità")
st.write("Seleziona i giorni in cui i dipendenti **NON** possono lavorare.")

giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
indisponibilita = {}

# Creiamo le colonne per rendere la pagina più compatta
cols = st.columns(3) 
for i, dip in enumerate(lista_dipendenti):
    with cols[i % 3]: # Distribuisce i dipendenti su 3 colonne
        indisponibilita[dip] = st.multiselect(
            f"Riposi per {dip}", 
            giorni_settimana,
            key=f"indisp_{dip}"
        )

# --- 5. GENERAZIONE E PDF ---
st.write("---")
if st.button("🚀 GENERA TURNI E PDF", type="primary", use_container_width=True):
    if not turni_disponibili:
        st.error("Seleziona almeno un tipo di turno!")
    else:
        # Calcoli date
        delta = data_fine - data_inizio
        giorni_totali = [data_inizio + timedelta(days=i) for i in range(delta.days + 1)]
        
        schedule_data = []
        
        # Algoritmo Assegnazione
        for giorno_reale in giorni_totali:
            nome_giorno = giorni_settimana[giorno_reale.weekday()] # Es: Lunedì
            
            for tipo_turno in turni_disponibili:
                # Cerca chi è disponibile
                disponibili = [
                    d for d in lista_dipendenti 
                    if nome_giorno not in indisponibilita.get(d, [])
                ]
                
                dipendente_scelto = random.choice(disponibili) if disponibili else "⚠️ NESSUNO"
                
                schedule_data.append({
                    "Data": giorno_reale.strftime("%d/%m/%Y"),
                    "Giorno": nome_giorno,
                    "Turno": tipo_turno,
                    "Dipendente": dipendente_scelto
                })
        
        # Mostra tabella a video
        df = pd.DataFrame(schedule_data)
        st.success("Turni generati!")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Genera PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 10, txt=f"Turni: {AZIENDA}", ln=1, align='C')
        pdf.set_font("Arial", size=10)
        pdf.ln(10)
        
        # Intestazione Tabella PDF
        # Larghezze colonne
        w_data, w_giorno, w_turno, w_dip = 35, 30, 40, 80
        
        pdf.set_fill_color(200, 220, 255) # Azzurrino
        pdf.cell(w_data, 10, "Data", 1
