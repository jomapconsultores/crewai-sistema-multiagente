import streamlit as st
from datetime import datetime
import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import io
import base64
from database import guardar_analisis, obtener_analisis

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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

# Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None

# ============================================
# FUNCIONES DE IMÁGENES
# ============================================

def extraer_texto_imagen(imagen_bytes):
    if not gemini_model:
        return "⚠️ Gemini no configurado"
    try:
        image = Image.open(io.BytesIO(imagen_bytes))
        response = gemini_model.generate_content(["Extrae todo el texto de esta imagen, describe gráficos y diagramas en detalle.", image])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def analizar_diagrama(imagen_bytes):
    if not gemini_model:
        return "⚠️ Gemini no configurado"
    try:
        image = Image.open(io.BytesIO(imagen_bytes))
        response = gemini_model.generate_content(["Analiza este diagrama: qué tipo es, qué datos muestra, qué conclusión principal tiene.", image])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

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

def llamar_gemini(prompt):
    if not gemini_model:
        return "⚠️ Gemini no configurado. Agrega GEMINI_API_KEY en .env"
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error Gemini: {str(e)}"

# ============================================
# AGENTES ESPECIALIZADOS
# ============================================

def agente_contenido(texto, analisis_imagenes, instrucciones):
    prompt = f"""
    Eres un Analista de Contenido Científico.
    Instrucciones: {instrucciones}
    Texto: {texto[:5000]}
    Imágenes: {analisis_imagenes[:2000]}
    Analiza el contenido con rigor científico. Da calificación y recomendaciones.
    """
    return llamar_deepseek(prompt)

def agente_formato(texto, estilo_citas, imagenes_info):
    prompt = f"""
    Eres un Revisor de Formato Académico.
    Texto: {texto[:3000]}
    Imágenes: {imagenes_info[:1500]}
    Estilo citas: {estilo_citas}
    Verifica formato, estructura y estilo.
    """
    return llamar_gemini(prompt)

def agente_citas(texto, estilo_citas):
    prompt = f"""
    Verifica TODAS las citas en el documento.
    Texto: {texto[:6000]}
    Estilo: {estilo_citas}
    Da total de citas, errores y veredicto.
    """
    return llamar_groq(prompt)

def agente_ortografia(texto):
    prompt = f"Corrige ortografía y gramática:\n{texto[:6000]}\nDa cantidad de errores y correcciones."
    return llamar_groq(prompt)

def agente_evaluador(requisitos, resultados):
    prompt = f"""
    Evalúa si se cumple el 100% de los requisitos.
    Requisitos: {requisitos}
    Resultados de agentes: {resultados}
    Da lista de verificación (✅/❌) y veredicto final.
    """
    return llamar_deepseek(prompt)

def agente_generador(texto, formato, estilo_citas, resultados, imagenes_info):
    prompt = f"""
    Genera documento final profesional.
    Contenido original: {texto[:4000]}
    Análisis imágenes: {imagenes_info[:1500]}
    Resultados agentes: {resultados}
    Formato: {formato}
    Estilo citas: {estilo_citas}
    Incluye portada, resumen, análisis, tabla de verificación, conclusiones, bibliografía.
    """
    return llamar_gemini(prompt)

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
    | Formato | Gemini |
    | Citas | Groq |
    | Ortografía | Groq |
    | Evaluador | DeepSeek |
    | Generador | Gemini |
    | Imágenes | Gemini |
    """)

if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")
    with col3:
        st.success("✅ Gemini") if GEMINI_API_KEY else st.error("❌ Gemini")

elif opcion == "📝 Nuevo Análisis":
    st.header("📝 Nuevo Análisis con 7 Agentes")
    
    with st.form("form_analisis"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título del análisis")
            formato = st.selectbox("Formato salida", ["Word", "PDF", "Markdown"])
        with col2:
            estilo_citas = st.selectbox("Estilo citación", ["APA", "Vancouver", "MLA", "Chicago"])
            nivel = st.select_slider("Nivel rigor", ["Básico", "Estándar", "Alto", "Máximo"])
        
        archivos = st.file_uploader(
            "Sube documentos (Word, Excel, PDF, TXT) e imágenes (PNG, JPG, GIF)",
            type=["txt", "md", "pdf", "docx", "xlsx", "png", "jpg", "jpeg", "gif"],
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
                
                # Separar imágenes y documentos
                docs = []
                imagenes = []
                for a in archivos:
                    if a.type.startswith('image'):
                        imagenes.append(a)
                    else:
                        docs.append(a)
                
                # Extraer texto de documentos
                texto_completo = ""
                for doc in docs:
                    try:
                        texto_completo += f"\n\n--- {doc.name} ---\n{doc.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {doc.name} ---\n[Binario]"
                
                progress.progress(1/7)
                
                # Analizar imágenes
                status.info("📷 Agente Imágenes (Gemini)...")
                imagenes_procesadas = []
                for img in imagenes:
                    img_bytes = img.getvalue()
                    analisis = {
                        "nombre": img.name,
                        "texto": extraer_texto_imagen(img_bytes)[:500],
                        "diagrama": analizar_diagrama(img_bytes)[:500]
                    }
                    imagenes_procesadas.append(analisis)
                
                imagenes_texto = "\n".join([f"**{i['nombre']}**: {i['texto']}" for i in imagenes_procesadas])
                progress.progress(2/7)
                
                resultados = {}
                
                status.info("🤖 Agente Contenido (DeepSeek)...")
                resultados["contenido"] = agente_contenido(texto_completo, imagenes_texto, instrucciones)
                progress.progress(3/7)
                
                status.info("📐 Agente Formato (Gemini)...")
                resultados["formato"] = agente_formato(texto_completo, estilo_citas, imagenes_texto)
                progress.progress(4/7)
                
                status.info("📚 Agente Citas (Groq)...")
                resultados["citas"] = agente_citas(texto_completo, estilo_citas)
                progress.progress(5/7)
                
                status.info("✍️ Agente Ortografía (Groq)...")
                resultados["ortografia"] = agente_ortografia(texto_completo)
                progress.progress(6/7)
                
                status.info("✅ Agente Evaluador (DeepSeek)...")
                resultados["evaluacion"] = agente_evaluador(instrucciones, str(resultados)[:2000])
                progress.progress(6.5/7)
                
                status.info("📄 Agente Generador (Gemini)...")
                documento_final = agente_generador(texto_completo, formato, estilo_citas, str(resultados)[:2000], imagenes_texto)
                progress.progress(7/7)
                
                status.success(f"✅ Análisis completado! {len(docs)} documentos + {len(imagenes)} imágenes")
                
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
                
                tabs = st.tabs(["📄 Documento Final", "🔍 Agentes", "🖼️ Imágenes", "✅ Verificación"])
                
                with tabs[0]:
                    st.markdown(documento_final)
                    st.download_button("📥 Descargar", documento_final, file_name=f"{titulo}.md")
                
                with tabs[1]:
                    for nombre, resultado in resultados.items():
                        with st.expander(f"🤖 {nombre.upper()}"):
                            st.markdown(resultado)
                
                with tabs[2]:
                    for img in imagenes:
                        st.image(img, caption=img.name, width=200)
                
                with tabs[3]:
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
st.caption("🤖 CrewAI Multiagente | DeepSeek | Gemini | Groq | 7 Agentes Especializados | Con Supabase")