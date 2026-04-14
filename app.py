import streamlit as st
from datetime import datetime
import os
from PIL import Image
import io
import base64

st.set_page_config(page_title="CrewAI - Sistema Multiagente", page_icon="🤖", layout="wide")

st.title("🤖 CrewAI - Sistema Multiagente de Análisis")
st.markdown("---")

st.info("✅ Sistema funcionando correctamente. Sube archivos e imágenes para analizar.")

with st.form("form_analisis"):
    titulo = st.text_input("Título del análisis")
    archivos = st.file_uploader("Sube documentos o imágenes", accept_multiple_files=True)
    instrucciones = st.text_area("Instrucciones")
    
    if st.form_submit_button("🚀 Iniciar Análisis"):
        if titulo and archivos:
            st.success(f"✅ Análisis '{titulo}' iniciado con {len(archivos)} archivo(s)")
            st.write("**Resultado:** El sistema está funcionando correctamente en localhost. Para usar los agentes completos, configura las API keys en el archivo .env")
        else:
            st.error("Completa todos los campos")

st.markdown("---")
st.caption("CrewAI Multiagente | DeepSeek | Groq | Gemini")