import streamlit as st
import pandas as pd
import random
import calendar
from datetime import date, timedelta

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestore Turni Intelligente", layout="wide")

# --- FUNZIONI DI UTILITÀ ---
def get_month_days(year, month):
    num_days = calendar.monthrange(year, month)[1]
    days = [date(year, month, day) for day in range(1, num_days + 1)]
    return days

def generate_schedule(staff_data, year, month, days_list):
    schedule = {}
    
    # Inizializza contatori turni per ogni persona
    work_counts = {name: 0 for name in staff_data.keys()}
    
    # Determina il target di turni lavorativi (Giorni totali - Giorni riposo richiesti)
    work_targets = {
        name: len(days_list) - data['target_riposi'] - len(data['ferie']) 
        for name, data in staff_data.items()
    }

    for current_day in days_list:
        day_str = current_day.strftime("%Y-%m-%d")
        candidates = []
        
        # 1. Filtra chi può lavorare
        for name, data in staff_data.items():
            # Se è in ferie/malattia, salta
            if current_day in data['ferie']:
                continue
            
            # Se ha segnato indisponibilità specifica per oggi, salta
            if current_day in data['indisponibilita']:
                continue
            
            # Se ha già raggiunto il massimo dei turni lavorabili (basato sui riposi chiesti), salta
            if work_counts[name] >= work_targets[name]:
                continue
                
            candidates.append(name)
        
        # 2. Assegnazione Turno
        if candidates:
            # Ordina i candidati in base a chi ha lavorato meno per equità
            candidates.sort(key=lambda x: work_counts[x])
            
            # Prendi i primi N necessari (qui assumiamo 1 persona per turno, modificabile)
            # Introduciamo un minimo di casualità tra chi ha gli stessi turni per variare
            min_work = work_counts[candidates[0]]
            best_candidates = [c for c in candidates if work_counts[c] == min_work]
            chosen_one = random.choice(best_candidates)
            
            schedule[day_str] = chosen_one
            work_counts[chosen_one] += 1
        else:
            schedule[day_str] = "⚠️ SCOPERTO"
            
    return schedule, work_counts

# --- INTERFACCIA GRAFICA ---

st.title("📅 Generatore Turni & Gestione Staff")
st.markdown("---")

# 1. SIDEBAR: Configurazione Generale
with st.sidebar:
    st.header("⚙️ Impostazioni")
    year = st.number_input("Anno", min_value=2024, max_value=2030, value=2024)
    month = st.selectbox("Mese", range(1, 13), index=date.today().month - 1)
    
    st.subheader("👥 Lista Dipendenti")
    staff_input = st.text_area("Inserisci i nomi (uno per riga)", "Mario\nLuigi\nAnna\nGiulia")
    staff_names = [x.strip() for x in staff_input.split('\n') if x.strip()]

# Calcola i giorni del mese selezionato
days_list = get_month_days(year, month)
days_formatted = [d.strftime("%Y-%m-%d") for d in days_list]

# 2. MAIN: Configurazione Dettagliata per Ogni Dipendente
st.subheader("📝 Dettagli Dipendenti")
st.info("Configura qui sotto le ferie, le indisponibilità specifiche e i giorni di riposo desiderati per ogni persona.")

staff_data = {}

# Creiamo un container espandibile per ogni dipendente per mantenere l'interfaccia pulita
for name in staff_names:
    with st.expander(f"Configurazione per **{name}**", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Input Ferie/Malattia
            leaves = st.multiselect(
                f"🌴 Ferie/Malattia ({name})",
                options=days_list,
                format_func=lambda x: x.strftime('%d/%m'),
                key=f"ferie_{name}"
            )
            
        with col2:
            # Input Indisponibilità (non sono ferie, ma giorni in cui preferisce non lavorare)
            unavailable = st.multiselect(
                f"🚫 Indisponibilità Specifica ({name})",
                options=[d for d in days_list if d not in leaves], # Escludiamo i giorni già segnati come ferie
                format_func=lambda x: x.strftime('%d/%m'),
                key=f"indisp_{name}"
            )
            
        with col3:
            # Giorni di riposo target
            # Default: 8 giorni (es. 2 a settimana)
            rest_days = st.number_input(
                f"🛌 Giorni di Riposo Obiettivo ({name})",
                min_value=0, 
                max_value=len(days_list), 
                value=8,
                key=f"riposo_{name}"
            )
            
        staff_data[name] = {
            'ferie': leaves,
            'indisponibilita': unavailable,
            'target_riposi': rest_days
        }

st.markdown("---")

# 3. GENERAZIONE
if st.button("🚀 Genera Turni", type="primary", use_container_width=True):
    with st.spinner("Elaborazione turni in corso..."):
        schedule_dict, stats = generate_schedule(staff_data, year, month, days_list)
        
        # Creazione DataFrame per visualizzazione
        df_schedule = pd.DataFrame(list(schedule_dict.items()), columns=['Data', 'Dipendente Assegnato'])
        df_schedule['Data'] = pd.to_datetime(df_schedule['Data'])
        df_schedule['Giorno'] = df_schedule['Data'].dt.day_name()
        
        # Riordina colonne
        df_schedule = df_schedule[['Data', 'Giorno', 'Dipendente Assegnato']]
        
        # --- RISULTATI ---
        col_res1, col_res2 = st.columns([2, 1])
        
        with col_res1:
            st.subheader("🗓️ Calendario Turni")
            # Evidenzia righe scoperte
            def highlight_uncovered(s):
                return ['background-color: #ffcccc' if v == "⚠️ SCOPERTO" else '' for v in s]
            
            st.dataframe(
                df_schedule.style.apply(highlight_uncovered, axis=1), 
                use_container_width=True,
                height=500
            )
            
        with col_res2:
            st.subheader("📊 Statistiche")
            df_stats = pd.DataFrame(list(stats.items()), columns=['Dipendente', 'Giorni Lavorati'])
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
            st.download_button(
                label="📥 Scarica come CSV",
                data=df_schedule.to_csv(index=False).encode('utf-8'),
                file_name=f'turni_{year}_{month}.csv',
                mime='text/csv',
            )
