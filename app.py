import streamlit as st
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import io
from database import guardar_analisis, obtener_analisis

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# DeepSeek
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
else:
    deepseek_client = None

# Groq
if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
else:
    groq_client = None

# ============================================
# FUNCIONES DE IMÁGENES (con Groq)
# ============================================

def extraer_texto_imagen(imagen_bytes):
    return "⚠️ El análisis de imágenes requiere Gemini. Por ahora, describe la imagen manualmente."

def analizar_diagrama(imagen_bytes):
    return "⚠️ El análisis de diagramas requiere Gemini. Por ahora, describe el diagrama manualmente."

# ============================================
# FUNCIONES DE LOS AGENTES
# ============================================

def llamar_deepseek(prompt):
    if not deepseek_client:
        return "⚠️ DeepSeek no configurado. Agrega DEEPSEEK_API_KEY en .env"
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
        return "⚠️ Groq no configurado. Agrega GROQ_API_KEY en .env"
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
# AGENTES ESPECIALIZADOS
# ============================================

def agente_contenido(texto, instrucciones):
    prompt = f"""
    Eres un Analista de Contenido Científico.
    Instrucciones: {instrucciones}
    Texto: {texto[:8000]}
    Analiza el contenido con rigor científico. Da calificación y recomendaciones.
    """
    return llamar_deepseek(prompt)

def agente_formato(texto, estilo_citas):
    prompt = f"""
    Eres un Revisor de Formato Académico.
    Texto: {texto[:5000]}
    Estilo citas: {estilo_citas}
    Verifica formato, estructura y estilo.
    """
    return llamar_groq(prompt)

def agente_citas(texto, estilo_citas):
    prompt = f"""
    Verifica TODAS las citas en el documento.
    Texto: {texto[:8000]}
    Estilo: {estilo_citas}
    Da total de citas, errores y veredicto.
    """
    return llamar_groq(prompt)

def agente_ortografia(texto):
    prompt = f"Corrige ortografía y gramática:\n{texto[:8000]}\nDa cantidad de errores y correcciones."
    return llamar_groq(prompt)

def agente_evaluador(requisitos, resultados):
    prompt = f"""
    Evalúa si se cumple el 100% de los requisitos.
    Requisitos: {requisitos}
    Resultados de agentes: {resultados}
    Da lista de verificación (✅/❌) y veredicto final.
    """
    return llamar_deepseek(prompt)

def agente_generador(texto, formato, estilo_citas, resultados):
    prompt = f"""
    Genera documento final profesional.
    Contenido original: {texto[:6000]}
    Resultados agentes: {resultados}
    Formato: {formato}
    Estilo citas: {estilo_citas}
    Incluye portada, resumen, análisis, tabla de verificación, conclusiones, bibliografía.
    """
    return llamar_groq(prompt)

# ============================================
# INTERFAZ DE STREAMLIT
# ============================================

st.set_page_config(page_title="CrewAI - Sistema Multiagente", page_icon="🤖", layout="wide")

st.title("🤖 CrewAI - Sistema Multiagente de Análisis Documental")
st.markdown("---")

with st.sidebar:
    st.header("📋 Navegación")
    opcion = st.radio("Ir a:", ["📝 Nuevo Análisis", "📚 Historial", "⚙️ Estado APIs"])
    
    st.markdown("### 🤖 Agentes")
    st.markdown("""
    | Agente | IA |
    |--------|-----|
    | Contenido | DeepSeek |
    | Formato | Groq |
    | Citas | Groq |
    | Ortografía | Groq |
    | Evaluador | DeepSeek |
    | Generador | Groq |
    """)

if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")

elif opcion == "📝 Nuevo Análisis":
    st.header("📝 Nuevo Análisis con Agentes")
    
    with st.form("form_analisis"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título del análisis")
            formato = st.selectbox("Formato salida", ["Word", "PDF", "Markdown"])
        with col2:
            estilo_citas = st.selectbox("Estilo citación", ["APA", "Vancouver", "MLA", "Chicago"])
        
        archivos = st.file_uploader(
            "Sube documentos (Word, Excel, PDF, TXT)",
            type=["txt", "md", "pdf", "docx", "xlsx"],
            accept_multiple_files=True
        )
        
        instrucciones = st.text_area("Instrucciones específicas", height=150)
        
        submitted = st.form_submit_button("🚀 Iniciar Análisis Multiagente", type="primary")
        
        if submitted:
            if not titulo or not archivos or not instrucciones:
                st.error("❌ Completa todos los campos")
            else:
                progress = st.progress(0)
                status = st.empty()
                
                # Extraer texto de documentos
                texto_completo = ""
                for doc in archivos:
                    try:
                        texto_completo += f"\n\n--- {doc.name} ---\n{doc.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {doc.name} ---\n[Binario]"
                
                progress.progress(1/6)
                
                resultados = {}
                
                status.info("🤖 Agente Contenido (DeepSeek)...")
                resultados["contenido"] = agente_contenido(texto_completo, instrucciones)
                progress.progress(2/6)
                
                status.info("📐 Agente Formato (Groq)...")
                resultados["formato"] = agente_formato(texto_completo, estilo_citas)
                progress.progress(3/6)
                
                status.info("📚 Agente Citas (Groq)...")
                resultados["citas"] = agente_citas(texto_completo, estilo_citas)
                progress.progress(4/6)
                
                status.info("✍️ Agente Ortografía (Groq)...")
                resultados["ortografia"] = agente_ortografia(texto_completo)
                progress.progress(5/6)
                
                status.info("✅ Agente Evaluador (DeepSeek)...")
                resultados["evaluacion"] = agente_evaluador(instrucciones, str(resultados)[:2000])
                progress.progress(5.5/6)
                
                status.info("📄 Agente Generador (Groq)...")
                documento_final = agente_generador(texto_completo, formato, estilo_citas, str(resultados)[:2000])
                progress.progress(6/6)
                
                status.success(f"✅ Análisis completado! {len(archivos)} archivo(s)")
                
                # Guardar en Supabase
                guardar_analisis(
                    titulo=titulo,
                    instrucciones=instrucciones,
                    formato=formato,
                    estilo=estilo_citas,
                    resultado=documento_final,
                    archivos=[a.name for a in archivos]
                )
                st.success("💾 Análisis guardado en la base de datos")
                
                st.markdown("---")
                st.header("📊 Resultados")
                
                tabs = st.tabs(["📄 Documento Final", "🔍 Agentes", "✅ Verificación"])
                
                with tabs[0]:
                    st.markdown(documento_final)
                    st.download_button("📥 Descargar", documento_final, file_name=f"{titulo}.md")
                
                with tabs[1]:
                    for nombre, resultado in resultados.items():
                        with st.expander(f"🤖 {nombre.upper()}"):
                            st.markdown(resultado)
                
                with tabs[2]:
                    st.markdown(resultados.get("evaluacion", "No disponible"))

elif opcion == "📚 Historial":
    st.header("📚 Historial de Análisis")
    
    analisis_lista = obtener_analisis()
    
    if not analisis_lista:
        st.info("No hay análisis previos. Crea uno nuevo en 'Nuevo Análisis'")
    else:
        for item in analisis_lista:
            with st.expander(f"📌 {item.get('titulo', 'Sin título')} - {item.get('fecha', '')[:10]}"):
                st.write(f"**Formato:** {item.get('formato_salida', 'N/A')}")
                st.write(f"**Estilo citas:** {item.get('estilo_citas', 'N/A')}")
                st.write(f"**Archivos:** {item.get('archivos', 'N/A')}")
                
                with st.expander("Ver resultado"):
                    st.markdown(item.get('resultado', 'No disponible')[:2000])

st.markdown("---")
st.caption("🤖 CrewAI Multiagente | DeepSeek | Groq | 6 Agentes Especializados")