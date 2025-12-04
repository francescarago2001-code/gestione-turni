      import streamlit as st
import pandas as pd
import random
from fpdf import FPDF
import base64
from datetime import timedelta, date

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Gestore Turni", layout="wide")

# --- PARAMETRI FISSI (MODIFICA QUESTI PER OGNI CLIENTE) ---
# Invece di usare i secrets, scrivi qui i dati del cliente prima di consegnare il software
NOME_AZIENDA = "Bar Esempio"
DIPENDENTI_START = "Mario, Luigi, Anna, Giovanni" 

st.title(f"📅 {NOME_AZIENDA} - Generatore Turni")

# --- 1. INPUT DIPENDENTI (MODIFICABILE) ---
st.write("---")
st.subheader("1. Dipendenti")
st.info("Puoi modificare la lista qui sotto per questa sessione.")

# La casella parte con i nomi che hai scritto sopra, ma il cliente può cambiarli
nomi_input = st.text_area("Lista Dipendenti:", value=DIPENDENTI_START, height=100)
lista_dipendenti = [x.strip() for x in nomi_input.split(',') if x.strip()]

if not lista_dipendenti:
    st.error("⚠️ La lista dipendenti è vuota! Scrivi i nomi separati da virgola.")
    st.stop()

# --- 2. IMPOSTAZIONI ---
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
        ["Mattina", "Pomeriggio", "Notte", "Spe
