import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta
import math

# --- CONFIGURAZIONE PAGINA (LIGHT & MINIMAL) ---
st.set_page_config(
    page_title="Gestione Turni | Minimal",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PER LOOK "ELEGANT & MINIMAL" ---
st.markdown("""
    <style>
    /* Sfondo e Testi Generali */
    .stApp {
        background-color: #ffffff;
        color: #333333;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: #111111 !important;
        font-weight: 600;
    }
    
    /* Card Statistiche (Stile Apple) */
    .stat-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .stat-card:hover {


