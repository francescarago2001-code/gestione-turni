import streamlit as st
import pandas as pd
import random
import base64
from datetime import timedelta, date

# --- PROVA A IMPORTARE FPDF (Se fallisce, avvisa l'utente) ---
try:
    from fpdf import FPDF
except ImportError:
    st.error("ERRORE GRAVE: Manca 'fpdf' nel file requirements.txt. Vai su GitHub e aggiungilo!")
    st.stop()

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Gestore Turni", layout="wide")

# --- NOMI DI DEFAULT (Quelli che appaiono appena apri) ---
# Modifica questa riga prima di vendere il software al cliente
NOMI_BASE = "Mario, Luigi, Anna, Giovanni"

st.title("📅 Gestore Turni Aziendali")

# --- 1. INSERIMENTO DIPENDENTI ---
st.write("---")
col_inp, col_info = st.columns([2, 1])
with col_inp:
    st.subheader("1. Chi lavora?")
    # L'utente può modificare la lista, ma parte con quella che hai deciso tu
    nomi_text = st.text_area("Lista dipendenti (separati da virgola)", value=NOMI_BASE, height=70)
    
    # Pulizia nomi
    lista_dipendenti = [n.strip() for n in nomi_text.split(',') if n.strip()]

with col_info:
    st.info(f"Dipendenti rilevati: **{len(lista_dipendenti)}**")
    if len(lista_dipendenti) == 0:
        st.error("Inserisci almeno un nome!")
        st.stop()

# --- 2. CONFIGURAZIONE TURNI ---
st.write("---")
st.subheader("2. Impostazioni Calendario")

c1, c2, c3 = st.columns(3)
with c1:
    d_inizio = st.date_input("Data Inizio", date.today())
with c2:
    d_fine = st.date_input("Data Fine", date.today() + timedelta(days=6))
with c3:
    tipi_turno = st.multiselect(
        "Quali turni esistono?", 
        ["Mattina", "Pomeriggio", "Notte", "Spezzato"],
        default=["Mattina", "Pomeriggio"]
    )

if not tipi_turno:
    st.error("Seleziona almeno un tipo di turno.")
    st.stop()

# --- 3. GESTIONE RIPOSI ---
st.write("---")
st.subheader("3. Giorni di Riposo")
st.write("Seleziona i giorni in cui il dipendente **NON** può lavorare.")

giorni_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
indisponibilita = {}

cols = st.columns(4) # Griglia per occupare meno spazio
for i, dip in enumerate(lista_dipendenti):
    with cols[i % 4]:
        indisponibilita[dip] = st.multiselect(f"Riposo {dip}", giorni_week, key=f"no_{i}")

# --- 4. MOTORE GENERAZIONE ---
st.write("---")
if st.button("🚀 GENERA TURNI", type="primary", use_container_width=True):
    
    delta = (d_fine - d_inizio).days + 1
    dati_turni = []

    # Ciclo giorno per giorno
    for i in range(delta):
        giorno_corrente = d_inizio + timedelta(days=i)
        nome_giorno = giorni_week[giorno_corrente.weekday()] # Es: Lunedì
        
        for turno in tipi_turno:
            # Chi è disponibile oggi?
            # Uno è disponibile se il nome del giorno NON è nella sua lista di riposi
            disponibili = [
                d for d in lista_dipendenti 
                if nome_giorno not in indisponibilita.get(d, [])
            ]
            
            if disponibili:
                lavoratore = random.choice(disponibili)
            else:
                lavoratore = "⚠️ NESSUNO"
            
            dati_turni.append({
                "Data": giorno_corrente.strftime("%d/%m/%Y"),
                "Giorno": nome_giorno,
                "Turno": turno,
                "Dipendente": lavoratore
            })
            
    # --- VISUALIZZAZIONE ---
    df = pd.DataFrame(dati_turni)
    st.success("Turni generati con successo!")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # --- CREAZIONE PDF ---
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Tabella Turni", ln=1, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=10)
        # Intestazione
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(35, 10, "Data", 1, 0, 'C', True)
        pdf.cell(30, 10, "Giorno", 1, 0, 'C', True)
        pdf.cell(40, 10, "Turno", 1, 0, 'C', True)
        pdf.cell(0
