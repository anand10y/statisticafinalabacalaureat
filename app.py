import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

uploaded_file = st.file_uploader("Încarcă fișierul Excel", type=["xlsx", "xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # curățăm antetele

    # coloane principale
    col_clasa = next((c for c in df.columns if "clasa" in c.lower()), None)
    col_statut = next((c for c in df.columns if "statut" in c.lower()), None)
    if not col_clasa or not col_statut:
        st.error("Nu am găsit coloanele 'Clasa' sau 'Statut' în fișier!")
        st.stop()

    # probe EA, EC, ED_*
    probe = [c for c in df.columns if c.upper().startswith(("EA","EC","ED"))]

    # culori
    culoare_rezultat = {"Reușit":"#2ecc71","Respins":"#e74c3c","Repetent":"#9b59b6"}

    # selectare clase
    st.markdown("### 🔴 Selectează clasele")
    clase = sorted(df[col_clasa].dropna().unique().tolist())
    clase_selectate = st.multiselect("Clase disponibile:", clase, default=[], label_visibility="collapsed")
    df_filtrat = df[df[col_clasa].isin(clase_selectate)] if clase_selectate else df.copy()

    # selectare probe
    st.markdown("### 🔵 Selectează probele")
    probe_selectate = st.multiselect("Probe disponibile:", options=probe, default=[], label_visibility="collapsed")

    # -------------------------
    # Statistica numerică
    # -------------------------
    st.subheader("📊 Statistica numerică elevi")
    total_elevi = len(df_filtrat)
    transferati = df_filtrat[col_statut].str.lower().str.contains("transferat").sum()
    retrasi = df_filtrat[col_statut].str.lower().str.contains("retras").sum()
    neinscrisi = df_filtrat[col_statut].str.lower().str.contains("neînscris|neinscris").sum()
    repetenti = df_filtrat[col_statut].str.lower().str.contains("repetent").sum()
    promovati = total_elevi - (transferati + retrasi + repetenti)
    inscrisi_examen = promovati - neinscrisi
    elevi_ramasi = total_elevi - transferati - retrasi

    st.markdown(f"- **Număr total elevi:** {total_elevi}")
    st.markdown(f"- **Număr transferați:** {transferati}")
    st.markdown(f"- **Număr retrași:** {retrasi}")
    st.markdown(f"- **Număr elevi rămași:** {elevi_ramasi}")
    st.markdown(f"- **Număr înscriși la examen:** {inscrisi_examen}")
    st.markdown(f"- **Număr neînscriși:** {neinscrisi}")
    st.markdown(f"- **Număr repetenți:** {repetenti}")
    st.markdown(f"- **Număr promovați:** {promovati}")

    # -------------------------
    # PIE Statut (Reușit/Respins/Repetent)
    # -------------------------
    st.subheader("📊 Distribuția pe Statut (doar participanți la examen)")
    df_exam = df_filtrat[df_filtrat[col_statut].isin(["Reușit","Respins","Repetent"])]
    counts = df_exam[col_statut].value_counts()
    if not counts.empty:
        fig_statut = px.pie(values=counts.values, names=counts.index,
                             title="Distribuția elevilor participanți la examen",
                             hole=0.3, color=counts.index, color_discrete_map=culoare_rezultat)
        procent_custom = (counts.values / counts.values.sum() * 100).reshape(-1,1)
        fig_statut.update_traces(texttemplate="%{label}\n%{customdata[0]:.2f}%\n(%{value} elevi)",
                                 textposition='inside', textfont_size=22, customdata=procent_custom)
        fig_statut.update_layout(title_font_size=26, legend_font_size=20)
        st.plotly_chart(fig_statut, use_container_width=True)

    # -------------------------
    # PIE pe probe
    # -------------------------
    for proba in probe_selectate:
        st.subheader(f"📊 Rezultate pentru {proba} (procentual)")
        df_proba = pd.to_numeric(df_filtrat[proba], errors="coerce").dropna()
        if not df_proba.empty:
            rezultate = (df_proba >= 5).map({True:"Reușit", False:"Respins"})
            counts_proba = rezultate.value_counts()
            fig_proba = px.pie(values=counts_proba.values, names=counts_proba.index,
                               title=f"Rezultate pentru {proba}",
                               hole=0.3, color=counts_proba.index,
                               color_discrete_map=culoare_rezultat)
            procent_custom = (counts_proba.values / counts_proba.values.sum() * 100).reshape(-1,1)
            fig_proba.update_traces(texttemplate="%{label}\n%{customdata[0]:.2f}%\n(%{value} elevi)",
                                    textposition='inside', textfont_size=22, customdata=procent_custom)
            fig_proba.update_layout(title_font_size=24, legend_font_size=20)
            st.plotly_chart(fig_proba, use_container_width=True)

    # -------------------------
    # PIE pe clase
    # -------------------------
    st.subheader("📊 Distribuția pe clase (doar participanți la examen)")
    numar_clase = df_exam.groupby([col_clasa,col_statut]).size().reset_index(name='Numar')
    procent_clase_list = []
    for cl in numar_clase[col_clasa].unique():
        temp = numar_clase[numar_clase[col_clasa]==cl].copy()
        total = temp['Numar'].sum()
        temp['Procent'] = temp['Numar']/total*100
        procent_clase_list.append(temp)
    procent_clase = pd.concat(procent_clase_list, ignore_index=True)

    for cl in procent_clase[col_clasa].unique():
        temp = procent_clase[procent_clase[col_clasa]==cl]
        fig_pie = px.pie(temp, values='Numar', names=col_statut,
                         title=f"Distribuția pe statut pentru clasa {cl}",
                         hole=0.3, color=col_statut, color_discrete_map=culoare_rezultat)
        procent_custom = (temp['Numar'].values / temp['Numar'].sum() * 100).reshape(-1,1)
        fig_pie.update_traces(texttemplate="%{label}\n%{customdata[0]:.2f}%\n(%{value} elevi)",
                              textposition='inside', textfont_size=22, customdata=procent_custom)
        fig_pie.update_layout(title_font_size=24, legend_font_size=20)
        st.plotly_chart(fig_pie, use_container_width=True)

    # -------------------------
    # Tabel complet
    # -------------------------
    st.subheader("📋 Tabelul complet (după filtrare)")
    st.dataframe(df_filtrat, use_container_width=True)
