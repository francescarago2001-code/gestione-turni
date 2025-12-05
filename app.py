import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import date, timedelta, datetime
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Gestione Turni Operativi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DI GESTIONE LICENZA E PROVA GRATUITA ---
LICENSE_FILE = "license_data.json"
TRIAL_DAYS = 7

def check_trial_status():
    """
    Controlla lo stato della prova.
    Ritorna: (is_active, days_remaining, start_date)
    """
    today = date.today()
    
    # Se il file di licenza non esiste, è il PRIMO ACCESSO
    if not os.path.exists(LICENSE_FILE):
        data = {"start_date": str(today)}
        with open(LICENSE_FILE, "w") as f:
            json.dump(data, f)
        return True, TRIAL_DAYS, today

    # Se esiste, leggiamo la data di inizio
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
    except:
        # Se il file è corrotto, resettiamo a oggi (o blocchiamo, qui resettiamo per sicurezza)
        return False, 0, today

    # Calcolo giorni trascorsi
    days_elapsed = (today - start_date).days
    days_remaining = TRIAL_DAYS - days_elapsed

    if days_remaining < 0:
        return False, 0, start_date
    else:
        return True, days_remaining, start_date

# ESECUZIONE CONTROLLO LICENZA
trial_active, days_left, trial_start = check_trial_status()

# --- CSS STILE BUSINESS (CLEAN, NO EMOJI) ---
st.markdown("""
    <style>
    /* Reset e Font */
    .stApp {
        background-color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica
