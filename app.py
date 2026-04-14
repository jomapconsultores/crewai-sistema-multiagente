import streamlit as st
from datetime import datetime
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from database import guardar_analisis, obtener_analisis
import json
import re

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None
groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

# ============================================
# FUNCIONES DE BÚSQUEDA EN INTERNET
# ============================================

def buscar_en_internet(consulta):
    prompt = f"""
    Busca en fuentes oficiales y acreditadas información sobre:
    {consulta}
    
    Incluye:
    1. Fuentes oficiales (gobierno, universidades, organismos internacionales)
    2. Artículos académicos relevantes
    3. Datos estadísticos actualizados
    4. Referencias bibliográficas completas
    
    Proporciona la información de manera estructurada.
    """
    return llamar_groq(prompt)

def buscar_perfiles_profesionales(requisitos):
    prompt = f"""
    Analiza estos requisitos de un proyecto y determina:
    
    === REQUISITOS ===
    {requisitos}
    
    Responde con:
    1. LISTA DE PERFILES PROFESIONALES NECESARIOS
    2. PARA CADA PERFIL: experiencia requerida, habilidades específicas
    3. PERFILES QUE FALTAN (que no están en los documentos adjuntos)
    4. SUGERENCIAS DE DÓNDE ENCONTRAR ESTOS PERFILES
    """
    return llamar_deepseek(prompt)

# ============================================
# FUNCIONES DE ANÁLISIS PROFUNDO
# ============================================

def extraer_requisitos_linea_por_linea(texto):
    prompt = f"""
    Extrae TODOS los requisitos específicos del siguiente documento.
    Analiza línea por línea, párrafo por párrafo.
    
    === DOCUMENTO ===
    {texto[:8000]}
    
    Responde con formato JSON:
    {{
        "requisitos_generales": ["lista de requisitos generales"],
        "requisitos_tecnicos": ["lista de requisitos técnicos"],
        "requisitos_administrativos": ["lista de requisitos administrativos"],
        "fechas_plazos": ["fechas importantes"],
        "presupuesto_estimado": "monto si existe",
        "perfiles_necesarios": ["perfiles profesionales mencionados"]
    }}
    """
    respuesta = llamar_deepseek(prompt)
    try:
        return json.loads(respuesta)
    except:
        return {"error": respuesta, "texto_original": respuesta}

def analizar_profundidad(texto, requisitos):
    prompt = f"""
    Realiza un análisis a nivel POSTDOCTORADO del siguiente contenido.
    
    === CONTENIDO ===
    {texto[:6000]}
    
    === REQUISITOS IDENTIFICADOS ===
    {requisitos}
    
    Tu análisis debe incluir:
    1. EVALUACIÓN CRÍTICA DEL CONTENIDO (fortalezas, debilidades, brechas)
    2. ANÁLISIS METODOLÓGICO (si la metodología es adecuada)
    3. EVALUACIÓN ESTADÍSTICA (qué cálculos se necesitan)
    4. REFERENCIAS CRUZADAS (qué fuentes faltan)
    5. RECOMENDACIONES ESPECÍFICAS para cumplir cada requisito
    """
    return llamar_deepseek(prompt)

def generar_propuesta(analisis, requisitos, busqueda_internet, formato):
    prompt = f"""
    Genera una PROPUESTA COMPLETA Y PROFESIONAL basada en:
    
    === ANÁLISIS PROFUNDO ===
    {analisis[:4000]}
    
    === REQUISITOS ===
    {requisitos}
    
    === INFORMACIÓN DE FUENTES EXTERNAS ===
    {busqueda_internet[:3000]}
    
    === FORMATO SOLICITADO ===
    {formato}
    
    La propuesta debe incluir:
    1. PORTADA (título, autores, fecha, institución)
    2. RESUMEN EJECUTIVO (máximo 500 palabras)
    3. INTRODUCCIÓN Y JUSTIFICACIÓN (con citas)
    4. OBJETIVOS (general y específicos)
    5. METODOLOGÍA (detallada, con técnicas e instrumentos)
    6. CRONOGRAMA DE ACTIVIDADES (tabla)
    7. PRESUPUESTO DETALLADO (tabla)
    8. EQUIPO DE TRABAJO (perfiles y responsabilidades)
    9. RESULTADOS ESPERADOS E IMPACTO
    10. REFERENCIAS BIBLIOGRÁFICAS (formato APA)
    
    Usa formato profesional, con tablas donde corresponda.
    """
    return llamar_groq(prompt)

def verificar_cumplimiento(propuesta, requisitos):
    prompt = f"""
    Verifica si la siguiente propuesta cumple con CADA UNO de los requisitos.
    
    === PROPUESTA ===
    {propuesta[:5000]}
    
    === REQUISITOS ===
    {requisitos}
    
    Responde con:
    1. TABLA DE VERIFICACIÓN (cada requisito: ✅ CUMPLE / ❌ NO CUMPLE)
    2. PARA CADA REQUISITO NO CUMPLIDO: qué falta específicamente
    3. CALIFICACIÓN GENERAL (0-100%)
    4. RECOMENDACIONES DE MEJORA específicas
    """
    return llamar_deepseek(prompt)

def sugerir_mejoras(propuesta, evaluacion):
    prompt = f"""
    Basado en la evaluación, sugiere MEJORAS ESPECÍFICAS.
    
    === PROPUESTA ACTUAL ===
    {propuesta[:3000]}
    
    === EVALUACIÓN ===
    {evaluacion}
    
    Responde con:
    1. LISTA DE CAMBIOS NECESARIOS (prioridad alta/media/baja)
    2. PARA CADA CAMBIO: instrucción exacta de cómo modificarlo
    3. CONTENIDO SUGERIDO para reemplazar secciones débiles
    4. ELEMENTOS QUE FALTAN añadir
    """
    return llamar_groq(prompt)

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

st.set_page_config(page_title="CrewAI - Sistema Postdoctorado", page_icon="🎓", layout="wide")

st.title("🎓 CrewAI - Sistema de Análisis Postdoctorado")
st.markdown("---")

if "propuesta_actual" not in st.session_state:
    st.session_state.propuesta_actual = None
if "evaluacion_actual" not in st.session_state:
    st.session_state.evaluacion_actual = None
if "requisitos_extraidos" not in st.session_state:
    st.session_state.requisitos_extraidos = None

with st.sidebar:
    st.header("📋 Menú")
    opcion = st.radio("Ir a:", ["📝 Nuevo Análisis", "🔄 Mejorar Propuesta", "📚 Historial", "⚙️ Estado APIs"])
    
    st.markdown("---")
    st.markdown("### 🎓 Agentes Postdoctorado")
    st.markdown("""
    | Agente | IA | Función |
    |--------|-----|---------|
    | Extractor | DeepSeek | Extrae requisitos línea por línea |
    | Analizador | DeepSeek | Análisis crítico profundo |
    | Buscador | Groq | Búsqueda en internet |
    | Generador | Groq | Crea propuesta completa |
    | Verificador | DeepSeek | Verifica cumplimiento punto por punto |
    | Mejorador | Groq | Sugiere cambios iterativos |
    """)

if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")

elif opcion == "📝 Nuevo Análisis":
    st.header("📝 Análisis Postdoctorado de Documentos")
    
    with st.form("form_analisis"):
        titulo = st.text_input("Título del proyecto")
        
        col1, col2 = st.columns(2)
        with col1:
            formato_salida = st.selectbox("Formato de salida", ["Word (.docx)", "PDF (.pdf)", "Markdown (.md)"])
        with col2:
            estilo_citas = st.selectbox("Estilo de citación", ["APA 7ª edición", "Vancouver", "MLA", "Chicago"])
        
        archivos = st.file_uploader(
            "Sube documentos base (convocatoria, bases, términos de referencia)",
            type=["txt", "md", "pdf", "docx", "xlsx"],
            accept_multiple_files=True
        )
        
        archivos_adicionales = st.file_uploader(
            "Sube documentos adicionales (CVs, proyectos previos, artículos)",
            type=["txt", "md", "pdf", "docx", "xlsx"],
            accept_multiple_files=True
        )
        
        instrucciones = st.text_area("Instrucciones específicas", height=150)
        
        submitted = st.form_submit_button("🚀 Iniciar Análisis Postdoctorado", type="primary")
        
        if submitted:
            if not titulo:
                st.error("❌ Ingresa un título")
            elif not archivos:
                st.error("❌ Sube al menos un documento base")
            else:
                progress = st.progress(0)
                status = st.empty()
                
                texto_completo = ""
                for a in archivos:
                    try:
                        texto_completo += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {a.name} ---\n[Contenido binario]"
                
                for a in archivos_adicionales:
                    try:
                        texto_completo += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {a.name} ---\n[Contenido binario]"
                
                progress.progress(1/6)
                
                status.info("📋 FASE 1/6: Extrayendo requisitos línea por línea (DeepSeek)...")
                st.session_state.requisitos_extraidos = extraer_requisitos_linea_por_linea(texto_completo)
                progress.progress(2/6)
                
                status.info("🔍 FASE 2/6: Realizando análisis crítico profundo (DeepSeek)...")
                analisis_profundo = analizar_profundidad(texto_completo, st.session_state.requisitos_extraidos)
                progress.progress(3/6)
                
                status.info("🌐 FASE 3/6: Buscando información en fuentes oficiales (Groq)...")
                busqueda = buscar_en_internet(titulo + " " + instrucciones)
                progress.progress(4/6)
                
                status.info("✍️ FASE 4/6: Generando propuesta completa (Groq)...")
                st.session_state.propuesta_actual = generar_propuesta(analisis_profundo, st.session_state.requisitos_extraidos, busqueda, formato_salida)
                progress.progress(5/6)
                
                status.info("✅ FASE 5/6: Verificando cumplimiento de requisitos (DeepSeek)...")
                st.session_state.evaluacion_actual = verificar_cumplimiento(st.session_state.propuesta_actual, st.session_state.requisitos_extraidos)
                progress.progress(6/6)
                
                status.success("✅ Análisis completado!")
                
                st.markdown("---")
                st.header("📊 RESULTADOS DEL ANÁLISIS")
                
                tabs = st.tabs(["📄 Propuesta Final", "📋 Requisitos Extraídos", "✅ Evaluación", "🔄 Mejoras Sugeridas"])
                
                with tabs[0]:
                    st.markdown(st.session_state.propuesta_actual)
                    st.download_button("📥 Descargar", st.session_state.propuesta_actual, file_name=f"{titulo}.md")
                
                with tabs[1]:
                    st.json(st.session_state.requisitos_extraidos)
                
                with tabs[2]:
                    st.markdown(st.session_state.evaluacion_actual)
                
                with tabs[3]:
                    sugerencias = sugerir_mejoras(st.session_state.propuesta_actual, st.session_state.evaluacion_actual)
                    st.markdown(sugerencias)
                
                guardar_analisis(titulo, instrucciones, formato_salida, estilo_citas, st.session_state.propuesta_actual, [a.name for a in archivos])

elif opcion == "🔄 Mejorar Propuesta":
    st.header("🔄 Mejorar Propuesta (Iterativo)")
    
    if not st.session_state.propuesta_actual:
        st.warning("⚠️ No hay una propuesta activa. Crea un nuevo análisis primero.")
    else:
        st.subheader("Propuesta Actual (resumen)")
        st.markdown(st.session_state.propuesta_actual[:1000] + "...")
        
        st.markdown("---")
        st.subheader("Evaluación Actual")
        st.markdown(st.session_state.evaluacion_actual[:1000] + "...")
        
        st.markdown("---")
        st.subheader("Nuevos documentos para mejorar")
        
        nuevos_archivos = st.file_uploader("Sube documentos adicionales", type=["txt", "md", "pdf", "docx", "xlsx"], accept_multiple_files=True)
        comentarios = st.text_area("Indica qué cambios específicos quieres hacer", height=100)
        
        if st.button("🔄 Mejorar Propuesta", type="primary"):
            if nuevos_archivos or comentarios:
                with st.spinner("Procesando mejoras..."):
                    nuevo_texto = ""
                    for a in nuevos_archivos:
                        try:
                            nuevo_texto += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                        except:
                            nuevo_texto += f"\n\n--- {a.name} ---\n[Contenido binario]"
                    
                    prompt_mejora = f"""
                    Mejora la siguiente propuesta basándote en:
                    
                    === COMENTARIOS ===
                    {comentarios}
                    
                    === NUEVOS DOCUMENTOS ===
                    {nuevo_texto[:3000]}
                    
                    === PROPUESTA ACTUAL ===
                    {st.session_state.propuesta_actual[:5000]}
                    """
                    
                    st.session_state.propuesta_actual = llamar_groq(prompt_mejora)
                    st.session_state.evaluacion_actual = verificar_cumplimiento(st.session_state.propuesta_actual, st.session_state.requisitos_extraidos)
                    
                    st.success("✅ Propuesta mejorada!")
                    st.markdown(st.session_state.propuesta_actual)
                    st.download_button("📥 Descargar", st.session_state.propuesta_actual, file_name="propuesta_mejorada.md")
            else:
                st.error("❌ Agrega comentarios o documentos")

else:
    st.header("📚 Historial de Análisis")
    lista = obtener_analisis()
    if not lista:
        st.info("No hay análisis previos")
    else:
        for item in lista:
            with st.expander(f"📌 {item.get('titulo', 'Sin título')} - {item.get('fecha', '')[:10]}"):
                st.write(f"**Formato:** {item.get('formato_salida', 'N/A')}")
                st.write(f"**Estilo:** {item.get('estilo_citas', 'N/A')}")
                with st.expander("Ver resultado"):
                    st.markdown(item.get('resultado', 'No disponible')[:3000])

st.markdown("---")
st.caption("🎓 CrewAI Postdoctorado | DeepSeek + Groq | Análisis crítico | Generación de propuestas | Verificación de cumplimiento")