import streamlit as st
import pandas as pd
import random
from fpdf import FPDF
import base64
from datetime import timedelta, date

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Gestore Turni Pro", layout="wide")

# --- 1. RECUPERO DIPENDENTI (MEMORIA CONDIVISA) ---
# I nomi devono essere inseriti nei "Secrets" di Streamlit per essere fissi su tutti i dispositivi.
try:
    # Se nei secrets c'è scritto: dipendenti = "Gino, Pino, Tino"
    DIPENDENTI_BASE = st.secrets["dipendenti"].split(",")
    AZIENDA = st.secrets.get("azienda", "La Mia Azienda")
except:
    # Fallback se non hai ancora impostato i secrets
    DIPENDENTI_BASE = ["Inserisci i nomi", "nei Secrets", "di Streamlit"]
    AZIENDA = "Azienda Demo"

# Pulizia spazi vuoti nei nomi
lista_dipendenti = [x.strip() for x in DIPENDENTI_BASE if x.strip()]

# --- TITOLO ---
st.title(f"📅 Pianificazione Turni: {AZIENDA}")

# --- 2. IMPOSTAZIONI CALENDARIO E TURNI ---
st.sidebar.header("⚙️ Impostazioni")

# Selezione Date (Calendario vero)
col1, col2 = st.columns(2)
with col1:
    data_inizio = st.date_input("Data Inizio", date.today())
with col2:
    data_fine = st.date_input("Data Fine", date.today() + timedelta(days=6))

# Selezione Tipi di Turno
turni_disponibili = st.multiselect(
    "Quali turni vuoi coprire ogni giorno?",
    ["Mattina", "Pomeriggio", "Notte", "Spezzato", "Extra"],
    default=["Mattina", "Pomeriggio"]
)

# --- 3. GESTIONE DIPENDENTI ---
st.subheader("👥 Dipendenti (Caricati dal server)")
st.write(f"Dipendenti attivi: **{', '.join(lista_dipendenti)}**")
st.info("💡 Per aggiungere o togliere dipendenti in modo permanente, contatta l'amministratore del software.")

# --- 4. INDISPONIBILITÀ ---
# Semplifichiamo: permettiamo di scegliere i giorni della settimana in cui uno non può lavorare
st.subheader("🚫 Indisponibilità Ricorrenti")
giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
indisponibilita = {}

with st.expander("Apri per segnare i giorni di riposo fisso"):
    for dip in lista_dipendenti:
        # Crea una chiave unica per ogni widget
        indisponibilita[dip] = st.multiselect(
            f"Giorni di riposo per {dip}", 
            giorni_settimana,
            key=f"indisp_{dip}"
        )

# --- 5. GENERAZIONE TURNI ---
if st.button("Genera Calendario Turni", type="primary"):
    if not turni_disponibili:
        st.error("Seleziona almeno un tipo di turno (es. Mattina).")
    else:
        # Calcolo giorni totali
        delta = data_fine - data_inizio
        giorni_totali = []
        for i in range(delta.days + 1):
            giorni_totali.append(data_inizio + timedelta(days=i))
            
        schedule_data = []
        
        # Algoritmo di assegnazione
        for giorno_reale in giorni_totali:
            nome_giorno = giorni_settimana[giorno_reale.weekday()] # Es: "Lunedì"
            
            for tipo_turno in turni_disponibili:
                # Trova chi può lavorare quel giorno
                # Un dipendente è disponibile se il "nome del giorno" (es. Lunedì) NON è nei suoi giorni di riposo
                disponibili = [
                    d for d in lista_dipendenti 
                    if nome_giorno not in indisponibilita.get(d, [])
                ]
                
                if not disponibili:
                    assegnato = "NESSUNO DISPONIBILE"
                else:
                    # Scelta casuale tra i disponibili
                    assegnato = random.choice(disponibili)
                
                schedule_data.append({
                    "Data": giorno_reale.strftime("%d/%m/%Y"),
                    "Giorno": nome_giorno,
                    "Turno": tipo_turno,
                    "Dipendente": assegnato
                })
        
        # Mostra Tabella
        df = pd.DataFrame(schedule_data)
        st.success("Turni generati con successo!")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # --- 6. CREAZIONE PDF ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, txt=f"Turni {AZIENDA}", ln=1, align='C')
        pdf.set_font("Arial", size=10)
        pdf.ln(5)
        
        # Intestazioni tabella PDF
        col_w_data = 35
        col_w_giorno = 30
        col_w_turno = 40
        col_w_nome = 50
        
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(col_w_data, 10, "Data", 1, 0, 'C', 1)
        pdf.cell(col_w_giorno, 10, "Giorno", 1, 0, 'C', 1)
        pdf.cell(col_w_turno, 10, "Turno", 1, 0, 'C', 1)
        pdf.cell(col_w_nome, 10, "Dipendente", 1, 1, 'C', 1)
        
        for _, row in df.iterrows():
            pdf.cell(col_w_data, 10, str(row['Data']), 1)
            pdf.cell(col_w_giorno, 10, str(row['Giorno']), 1)
            pdf.cell(col_w_turno, 10, str(row['Turno']), 1)
            pdf.cell(col_w_nome, 10, str(row['Dipendente']), 1, 1)
            
        b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="Calendario_Turni.pdf" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📄 SCARICA PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
