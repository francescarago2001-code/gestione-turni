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
        # Se il file è corrotto, lo resetto (o blocchi, a tua scelta)
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
    
    /* Blocco Pagamento */
    .payment-container {
        text-align: center;
        padding: 50px;
        border: 2px solid #e74c3c;
        border-radius: 10px;
        background-color: #fdf2f2;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BLOCCO SOFTWARE SE PROVA SCADUTA ---
if not trial_active:
    st.markdown(f"""
    <div class="payment-container">
        <h1 style="color: #c0392b !important;">🚫 Periodo di Prova Scaduto</h1>
        <p style="font-size: 18px;">I tuoi {TRIAL_DAYS} giorni di prova gratuita sono terminati.</p>
        <p>Per continuare a generare turni e utilizzare il software, è necessario acquistare una licenza completa.</p>
