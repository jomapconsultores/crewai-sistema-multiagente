import streamlit as st
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
from database import guardar_analisis, obtener_analisis

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Clientes API
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None
groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

# ============================================
# FUNCIONES DE LLAMADAS A API
# ============================================

def llamar_deepseek(prompt):
    if not deepseek_client:
        return "⚠️ DeepSeek no configurado"
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error DeepSeek: {str(e)}"

def llamar_groq(prompt):
    if not groq_client:
        return "⚠️ Groq no configurado"
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error Groq: {str(e)}"

# ============================================
# INTERFAZ DE STREAMLIT
# ============================================

st.set_page_config(page_title="CrewAI - Sistema Multiagente", page_icon="🤖", layout="wide")

st.title("🤖 CrewAI - Sistema Multiagente")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📋 Menú")
    opcion = st.radio("Ir a:", ["📝 Nuevo Análisis", "📚 Historial", "⚙️ Estado APIs"])
    
    st.markdown("---")
    st.markdown("### 🤖 Agentes")
    st.markdown("""
    | Agente | IA |
    |--------|-----|
    | Analista | DeepSeek |
    | Revisor | Groq |
    | Generador | Groq |
    """)

# Estado de APIs
if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")

# Nuevo Análisis
elif opcion == "📝 Nuevo Análisis":
    st.header("📝 Nuevo Análisis")
    
    with st.form("form_analisis"):
        titulo = st.text_input("Título del análisis")
        formato = st.selectbox("Formato salida", ["Markdown", "Word", "PDF"])
        estilo_citas = st.selectbox("Estilo citación", ["APA", "Vancouver", "MLA"])
        
        archivos = st.file_uploader(
            "Sube documentos (TXT, PDF, Word, Excel)",
            type=["txt", "md", "pdf", "docx", "xlsx"],
            accept_multiple_files=True
        )
        
        instrucciones = st.text_area("Instrucciones", height=100)
        
        submitted = st.form_submit_button("🚀 Iniciar Análisis", type="primary")
        
        if submitted:
            if not titulo:
                st.error("❌ Ingresa un título")
            elif not archivos:
                st.error("❌ Sube al menos un archivo")
            else:
                with st.spinner("Procesando..."):
                    # Extraer texto
                    texto = ""
                    for a in archivos:
                        try:
                            texto += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                        except:
                            texto += f"\n\n--- {a.name} ---\n[Contenido binario]"
                    
                    # Agente 1: Análisis con DeepSeek
                    st.write("🔍 **Agente 1/3 - Analizando contenido (DeepSeek)...**")
                    analisis = llamar_deepseek(f"Analiza este contenido con rigor científico:\n\n{texto[:6000]}\n\nInstrucciones: {instrucciones}")
                    
                    # Agente 2: Revisión con Groq
                    st.write("📝 **Agente 2/3 - Revisando formato y citas (Groq)...**")
                    revision = llamar_groq(f"Revisa este análisis. Verifica formato y citas según {estilo_citas}:\n\n{analisis[:4000]}")
                    
                    # Agente 3: Documento final con Groq
                    st.write("📄 **Agente 3/3 - Generando documento final (Groq)...**")
                    documento_final = llamar_groq(f"Genera un informe final profesional con portada, resumen, desarrollo, conclusiones y bibliografía según {estilo_citas}. Basado en:\n\nAnálisis: {analisis[:3000]}\n\nRevisión: {revision[:2000]}")
                    
                    # Guardar en Supabase
                    guardar_analisis(titulo, instrucciones, formato, estilo_citas, documento_final, [a.name for a in archivos])
                    
                    st.success("✅ Análisis completado!")
                    st.markdown("---")
                    st.markdown("## 📄 Resultado")
                    st.markdown(documento_final)
                    
                    st.download_button("📥 Descargar", documento_final, file_name=f"{titulo}.md")

# Historial
elif opcion == "📚 Historial":
    st.header("📚 Historial de Análisis")
    
    lista = obtener_analisis()
    
    if not lista:
        st.info("No hay análisis previos")
    else:
        for item in lista:
            with st.expander(f"📌 {item.get('titulo', 'Sin título')} - {item.get('fecha', '')[:10]}"):
                st.write(f"**Formato:** {item.get('formato_salida', 'N/A')}")
                st.write(f"**Estilo:** {item.get('estilo_citas', 'N/A')}")
                st.write(f"**Archivos:** {item.get('archivos', 'N/A')}")
                with st.expander("Ver resultado"):
                    st.markdown(item.get('resultado', 'No disponible')[:3000])

st.markdown("---")
st.caption("CrewAI Multiagente | DeepSeek + Groq")