import streamlit as st
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
from database import guardar_analisis, obtener_analisis
import json

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None
groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

# ============================================
# FUNCIONES DE LLAMADAS A API
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
# AGENTE 1: EXTRACCIÓN DE REQUISITOS (DeepSeek)
# ============================================

def extraer_requisitos_postdoctorado(texto_completo):
    """Extrae requisitos a nivel postdoctoral"""
    prompt = f"""
    Eres un ANALISTA POSTDOCTORAL especializado en extracción de requisitos.
    
    === DOCUMENTO COMPLETO ===
    {texto_completo[:10000]}
    
    Extrae TODOS los requisitos del documento. Analiza línea por línea, párrafo por párrafo.
    
    Responde EXACTAMENTE con este formato JSON:
    
    {{
        "requisitos_generales": [
            {{"id": 1, "descripcion": "requisito general 1", "prioridad": "alta/media/baja"}},
            {{"id": 2, "descripcion": "requisito general 2", "prioridad": "alta/media/baja"}}
        ],
        "requisitos_tecnicos": [
            {{"id": 1, "descripcion": "requisito técnico 1", "especificacion": "detalle técnico"}}
        ],
        "requisitos_administrativos": [
            {{"id": 1, "descripcion": "requisito administrativo 1", "plazo": "fecha o plazo"}}
        ],
        "perfiles_necesarios": [
            {{"perfil": "nombre del perfil", "experiencia": "años y área", "habilidades": ["lista"]}}
        ],
        "fechas_clave": ["fecha1", "fecha2"],
        "presupuesto_referencia": "monto si existe",
        "evaluacion_criterios": ["criterio1", "criterio2"]
    }}
    
    Si un campo no tiene información, devuelve una lista vacía [].
    """
    
    respuesta = llamar_deepseek(prompt)
    try:
        # Intentar parsear JSON
        return json.loads(respuesta)
    except:
        # Si falla, devolver estructura básica con el texto
        return {
            "requisitos_generales": [{"id": 1, "descripcion": respuesta[:500], "prioridad": "alta"}],
            "requisitos_tecnicos": [],
            "requisitos_administrativos": [],
            "perfiles_necesarios": [],
            "fechas_clave": [],
            "presupuesto_referencia": "No especificado",
            "evaluacion_criterios": []
        }

# ============================================
# AGENTE 2: BÚSQUEDA EN INTERNET (Groq)
# ============================================

def buscar_informacion_postdoctoral(tema, requisitos):
    """Busca información en fuentes oficiales"""
    prompt = f"""
    Eres un INVESTIGADOR POSTDOCTORAL. Busca información actualizada y de fuentes oficiales sobre:
    
    === TEMA PRINCIPAL ===
    {tema}
    
    === REQUISITOS DEL PROYECTO ===
    {json.dumps(requisitos, indent=2)[:3000]}
    
    Proporciona:
    1. FUENTES OFICIALES (gobierno, universidades, organismos internacionales) con URLs
    2. ARTÍCULOS ACADÉMICOS RELEVANTES (autores, año, título, resumen)
    3. DATOS ESTADÍSTICOS ACTUALIZADOS
    4. REFERENCIAS BIBLIOGRÁFICAS COMPLETAS (formato APA)
    5. TENDENCIAS Y AVANCES RECIENTES
    
    Organiza la información de manera estructurada y profesional.
    """
    return llamar_groq(prompt)

# ============================================
# AGENTE 3: ANÁLISIS CRÍTICO (DeepSeek)
# ============================================

def analisis_critico_postdoctoral(texto, requisitos):
    """Realiza análisis crítico a nivel postdoctoral"""
    prompt = f"""
    Eres un EVALUADOR POSTDOCTORAL. Realiza un análisis crítico del siguiente contenido.
    
    === CONTENIDO A ANALIZAR ===
    {texto[:6000]}
    
    === REQUISITOS IDENTIFICADOS ===
    {json.dumps(requisitos, indent=2)[:2000]}
    
    Tu análisis debe incluir:
    
    1. EVALUACIÓN CIENTÍFICA:
       - Rigor metodológico (puntuación 1-10)
       - Validez de las afirmaciones
       - Uso adecuado de referencias
       - Profundidad del análisis
    
    2. BRECHAS Y DEBILIDADES:
       - Qué falta en el contenido
       - Inconsistencias encontradas
       - Áreas que requieren mejora
    
    3. FORTALEZAS:
       - Aspectos destacables
       - Buenas prácticas identificadas
    
    4. RECOMENDACIONES ESPECÍFICAS:
       - Cómo mejorar cada brecha identificada
       - Acciones concretas a tomar
    
    5. CALIFICACIÓN GENERAL (0-100%)
    """
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 4: GENERACIÓN DE PROPUESTA (Groq)
# ============================================

def generar_propuesta_postdoctoral(requisitos, analisis, busqueda, instrucciones, formato):
    """Genera propuesta completa a nivel postdoctoral"""
    prompt = f"""
    Eres un GENERADOR DE PROPUESTAS POSTDOCTORALES. Crea una propuesta profesional COMPLETA.
    
    === REQUISITOS DEL PROYECTO ===
    {json.dumps(requisitos, indent=2)[:3000]}
    
    === ANÁLISIS CRÍTICO ===
    {analisis[:2000]}
    
    === INFORMACIÓN DE FUENTES EXTERNAS ===
    {busqueda[:2000]}
    
    === INSTRUCCIONES ESPECÍFICAS ===
    {instrucciones}
    
    === FORMATO SOLICITADO ===
    {formato}
    
    La propuesta debe contener EXACTAMENTE estas secciones:
    
    # PROPUESTA TÉCNICA Y ECONÓMICA
    
    ## 1. PORTADA
    - Título del proyecto
    - Institución/Organización
    - Fecha de presentación
    - Autores/Investigadores principales
    
    ## 2. RESUMEN EJECUTIVO (máximo 500 palabras)
    - Problema a resolver
    - Objetivo principal
    - Metodología resumida
    - Resultados esperados
    - Presupuesto total
    
    ## 3. INTRODUCCIÓN Y JUSTIFICACIÓN
    - Contexto del problema
    - Estado del arte (con citas)
    - Justificación científica y social
    - Marco teórico-conceptual
    
    ## 4. OBJETIVOS
    - Objetivo general
    - Objetivos específicos (mínimo 5)
    - Indicadores de logro
    
    ## 5. METODOLOGÍA
    - Enfoque y tipo de investigación
    - Población y muestra
    - Técnicas e instrumentos de recolección
    - Procedimiento detallado (fases)
    - Plan de análisis de datos
    - Consideraciones éticas
    
    ## 6. CRONOGRAMA DE ACTIVIDADES
    | Actividad | Mes 1 | Mes 2 | Mes 3 | Mes 4 | Mes 5 | Mes 6 |
    |-----------|-------|-------|-------|-------|-------|-------|
    | Actividad 1 | X | X | | | | |
    
    ## 7. PRESUPUESTO DETALLADO
    | Rubro | Cantidad | Unitario | Total |
    |-------|----------|----------|-------|
    | Personal | | | |
    | Equipos | | | |
    | Materiales | | | |
    | Viajes | | | |
    | Gastos generales | | | |
    | **TOTAL** | | | |
    
    ## 8. EQUIPO DE TRABAJO
    | Rol | Perfil | Dedicación | Responsabilidades |
    |-----|--------|------------|-------------------|
    
    ## 9. RESULTADOS ESPERADOS E IMPACTO
    - Resultados científicos
    - Resultados tecnológicos
    - Impacto social/económico
    - Transferencia de conocimientos
    
    ## 10. REFERENCIAS BIBLIOGRÁFICAS (formato APA)
    
    ## 11. ANEXOS (si aplica)
    
    El documento debe ser profesional, riguroso y estar listo para ser presentado a una convocatoria postdoctoral.
    """
    return llamar_groq(prompt)

# ============================================
# AGENTE 5: VERIFICACIÓN DE CUMPLIMIENTO (DeepSeek)
# ============================================

def verificar_cumplimiento_postdoctoral(propuesta, requisitos):
    """Verifica punto por punto el cumplimiento de requisitos"""
    prompt = f"""
    Eres un AUDITOR POSTDOCTORAL. Verifica si la propuesta cumple con TODOS los requisitos.
    
    === PROPUESTA GENERADA ===
    {propuesta[:6000]}
    
    === REQUISITOS ORIGINALES ===
    {json.dumps(requisitos, indent=2)[:3000]}
    
    Responde con:
    
    ## TABLA DE VERIFICACIÓN
    
    | # | Requisito | Cumple | Observación |
    |---|-----------|--------|-------------|
    | 1 | ... | ✅/❌ | ... |
    
    ## REQUISITOS NO CUMPLIDOS
    Lista detallada de lo que falta
    
    ## CALIFICACIÓN GENERAL
    X/100 (XX%)
    
    ## RECOMENDACIONES FINALES
    Acciones concretas para cumplir los requisitos faltantes
    """
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 6: MEJORAS ITERATIVAS (Groq)
# ============================================

def sugerir_mejoras_postdoctorales(propuesta, verificacion, comentarios_usuario):
    """Sugiere mejoras basadas en la verificación y comentarios"""
    prompt = f"""
    Eres un ASESOR POSTDOCTORAL. Sugiere mejoras específicas para la propuesta.
    
    === PROPUESTA ACTUAL ===
    {propuesta[:4000]}
    
    === VERIFICACIÓN ===
    {verificacion[:2000]}
    
    === COMENTARIOS DEL USUARIO ===
    {comentarios_usuario}
    
    Responde con:
    
    1. CAMBIOS PRIORITARIOS (urgentes)
    2. MEJORAS RECOMENDADAS (importantes)
    3. OPTIMIZACIONES (deseables)
    4. TEXTO SUGERIDO para secciones débiles
    5. ELEMENTOS A AGREGAR
    """
    return llamar_groq(prompt)

# ============================================
# INTERFAZ DE STREAMLIT
# ============================================

st.set_page_config(page_title="CrewAI - Sistema Postdoctoral", page_icon="🎓", layout="wide")

st.title("🎓 CrewAI - Sistema de Análisis y Generación Postdoctoral")
st.markdown("---")

# Inicializar estado de sesión
if "propuesta_actual" not in st.session_state:
    st.session_state.propuesta_actual = None
if "verificacion_actual" not in st.session_state:
    st.session_state.verificacion_actual = None
if "requisitos_actuales" not in st.session_state:
    st.session_state.requisitos_actuales = None
if "analisis_actual" not in st.session_state:
    st.session_state.analisis_actual = None
if "busqueda_actual" not in st.session_state:
    st.session_state.busqueda_actual = None

with st.sidebar:
    st.header("📋 Menú")
    opcion = st.radio("Ir a:", ["📝 Nuevo Análisis Postdoctoral", "🔄 Mejorar Propuesta", "📚 Historial", "⚙️ Estado APIs"])
    
    st.markdown("---")
    st.markdown("### 🎓 Agentes Postdoctorales")
    st.markdown("""
    | Agente | IA | Función |
    |--------|-----|---------|
    | Extractor | DeepSeek | Extrae requisitos línea por línea |
    | Buscador | Groq | Búsqueda en fuentes oficiales |
    | Analizador | DeepSeek | Análisis crítico profundo |
    | Generador | Groq | Propuesta completa |
    | Verificador | DeepSeek | Verificación de cumplimiento |
    | Mejorador | Groq | Sugerencias iterativas |
    """)

if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2 = st.columns(2)
    with col1:
        if DEEPSEEK_API_KEY:
            st.success("✅ DeepSeek API: Conectado")
        else:
            st.error("❌ DeepSeek API: No configurada")
    with col2:
        if GROQ_API_KEY:
            st.success("✅ Groq API: Conectado")
        else:
            st.error("❌ Groq API: No configurada")

elif opcion == "📝 Nuevo Análisis Postdoctoral":
    st.header("🎓 Análisis Postdoctoral de Documentos")
    
    with st.form("form_postdoctoral"):
        titulo = st.text_input("Título del proyecto / convocatoria")
        
        col1, col2 = st.columns(2)
        with col1:
            formato_salida = st.selectbox("Formato de salida", ["Markdown (.md)", "Word (.docx)", "PDF (.pdf)"])
        with col2:
            estilo_citas = st.selectbox("Estilo de citación", ["APA 7ª edición", "Vancouver", "MLA", "Chicago"])
        
        archivos_base = st.file_uploader(
            "📄 Documentos base (convocatoria, bases, términos de referencia)",
            type=["txt", "md", "pdf", "docx", "xlsx"],
            accept_multiple_files=True,
            help="Sube los documentos que contienen los requisitos del proyecto"
        )
        
        archivos_adicionales = st.file_uploader(
            "📎 Documentos adicionales (CVs, proyectos previos, artículos, datos)",
            type=["txt", "md", "pdf", "docx", "xlsx", "csv"],
            accept_multiple_files=True,
            help="Opcional: sube perfiles de personal, proyectos anteriores, artículos académicos"
        )
        
        instrucciones = st.text_area(
            "📝 Instrucciones específicas",
            height=150,
            placeholder="""Ejemplo:
            - El proyecto debe enfocarse en energías renovables
            - Se requiere un equipo mínimo de 5 investigadores
            - El presupuesto no debe superar los $500,000
            - Incluir análisis estadístico de datos históricos
            - La metodología debe incluir trabajo de campo
            - Priorizar fuentes de los últimos 3 años
            - Incluir plan de transferencia de resultados
            """
        )
        
        submitted = st.form_submit_button("🚀 INICIAR ANÁLISIS POSTDOCTORAL", type="primary")
        
        if submitted:
            if not titulo:
                st.error("❌ Ingresa un título para el proyecto")
            elif not archivos_base:
                st.error("❌ Sube al menos un documento base")
            else:
                # Crear barras de progreso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Extraer texto de todos los archivos
                texto_completo = ""
                for a in archivos_base:
                    try:
                        texto_completo += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {a.name} ---\n[Contenido binario - requiere procesamiento especial]"
                
                for a in archivos_adicionales:
                    try:
                        texto_completo += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {a.name} ---\n[Contenido binario]"
                
                # FASE 1: Extraer requisitos
                status_text.info("🎓 FASE 1/6: Extrayendo requisitos línea por línea (DeepSeek)...")
                st.session_state.requisitos_actuales = extraer_requisitos_postdoctorado(texto_completo)
                progress_bar.progress(1/6)
                
                # FASE 2: Búsqueda en internet
                status_text.info("🌐 FASE 2/6: Buscando información en fuentes oficiales (Groq)...")
                st.session_state.busqueda_actual = buscar_informacion_postdoctoral(titulo, st.session_state.requisitos_actuales)
                progress_bar.progress(2/6)
                
                # FASE 3: Análisis crítico
                status_text.info("🔬 FASE 3/6: Realizando análisis crítico postdoctoral (DeepSeek)...")
                st.session_state.analisis_actual = analisis_critico_postdoctoral(texto_completo, st.session_state.requisitos_actuales)
                progress_bar.progress(3/6)
                
                # FASE 4: Generar propuesta
                status_text.info("✍️ FASE 4/6: Generando propuesta completa (Groq)...")
                st.session_state.propuesta_actual = generar_propuesta_postdoctoral(
                    st.session_state.requisitos_actuales,
                    st.session_state.analisis_actual,
                    st.session_state.busqueda_actual,
                    instrucciones,
                    formato_salida
                )
                progress_bar.progress(4/6)
                
                # FASE 5: Verificar cumplimiento
                status_text.info("✅ FASE 5/6: Verificando cumplimiento de requisitos (DeepSeek)...")
                st.session_state.verificacion_actual = verificar_cumplimiento_postdoctoral(
                    st.session_state.propuesta_actual,
                    st.session_state.requisitos_actuales
                )
                progress_bar.progress(5/6)
                
                # FASE 6: Guardar
                status_text.info("💾 FASE 6/6: Guardando análisis en base de datos...")
                guardar_analisis(
                    titulo, 
                    instrucciones, 
                    formato_salida, 
                    estilo_citas, 
                    st.session_state.propuesta_actual, 
                    [a.name for a in archivos_base]
                )
                progress_bar.progress(6/6)
                
                status_text.success("✅ ¡ANÁLISIS POSTDOCTORAL COMPLETADO!")
                
                # Mostrar resultados
                st.markdown("---")
                st.header("📊 RESULTADOS DEL ANÁLISIS")
                
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📄 PROPUESTA FINAL", 
                    "📋 REQUISITOS EXTRAÍDOS", 
                    "🔬 ANÁLISIS CRÍTICO",
                    "🌐 BÚSQUEDA INTERNET",
                    "✅ VERIFICACIÓN"
                ])
                
                with tab1:
                    st.markdown(st.session_state.propuesta_actual)
                    st.download_button(
                        "📥 DESCARGAR PROPUESTA",
                        st.session_state.propuesta_actual,
                        file_name=f"propuesta_{titulo.replace(' ', '_')}.md",
                        mime="text/markdown"
                    )
                
                with tab2:
                    st.json(st.session_state.requisitos_actuales)
                
                with tab3:
                    st.markdown(st.session_state.analisis_actual)
                
                with tab4:
                    st.markdown(st.session_state.busqueda_actual)
                
                with tab5:
                    st.markdown(st.session_state.verificacion_actual)

elif opcion == "🔄 Mejorar Propuesta":
    st.header("🔄 Mejora Iterativa de Propuesta")
    
    if not st.session_state.propuesta_actual:
        st.warning("⚠️ No hay una propuesta activa. Crea un nuevo análisis postdoctoral primero.")
    else:
        st.subheader("📄 Propuesta Actual (resumen)")
        st.markdown(st.session_state.propuesta_actual[:1500] + "...")
        
        st.markdown("---")
        st.subheader("✅ Verificación Actual")
        st.markdown(st.session_state.verificacion_actual[:1000] + "...")
        
        st.markdown("---")
        st.subheader("📎 Documentos adicionales para mejorar")
        
        nuevos_archivos = st.file_uploader(
            "Sube documentos adicionales (CVs, artículos, datos, etc.)",
            type=["txt", "md", "pdf", "docx", "xlsx", "csv"],
            accept_multiple_files=True
        )
        
        comentarios = st.text_area(
            "💬 Indica qué cambios específicos quieres hacer",
            height=100,
            placeholder="Ejemplo: Añadir más detalle en la metodología, incluir análisis estadístico, ajustar el presupuesto, mejorar las referencias..."
        )
        
        if st.button("🔄 MEJORAR PROPUESTA", type="primary"):
            if nuevos_archivos or comentarios:
                with st.spinner("Procesando mejoras..."):
                    # Extraer texto de nuevos archivos
                    nuevo_texto = ""
                    for a in nuevos_archivos:
                        try:
                            nuevo_texto += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                        except:
                            nuevo_texto += f"\n\n--- {a.name} ---\n[Contenido binario]"
                    
                    # Generar mejoras
                    mejoras = sugerir_mejoras_postdoctorales(
                        st.session_state.propuesta_actual,
                        st.session_state.verificacion_actual,
                        f"{comentarios}\n\nNuevos documentos: {nuevo_texto[:2000]}"
                    )
                    
                    # Generar nueva propuesta mejorada
                    prompt_mejora = f"""
                    Mejora la siguiente propuesta postdoctoral basándote en:
                    
                    === SUGERENCIAS DE MEJORA ===
                    {mejoras}
                    
                    === PROPUESTA ACTUAL ===
                    {st.session_state.propuesta_actual[:5000]}
                    
                    Genera la VERSIÓN MEJORADA Y COMPLETA de la propuesta.
                    """
                    
                    st.session_state.propuesta_actual = llamar_groq(prompt_mejora)
                    
                    # Re-verificar
                    st.session_state.verificacion_actual = verificar_cumplimiento_postdoctoral(
                        st.session_state.propuesta_actual,
                        st.session_state.requisitos_actuales
                    )
                    
                    st.success("✅ ¡PROPUESTA MEJORADA!")
                    
                    st.markdown("---")
                    st.subheader("📄 NUEVA VERSIÓN")
                    st.markdown(st.session_state.propuesta_actual)
                    
                    st.download_button(
                        "📥 DESCARGAR PROPUESTA MEJORADA",
                        st.session_state.propuesta_actual,
                        file_name="propuesta_mejorada.md",
                        mime="text/markdown"
                    )
            else:
                st.error("❌ Agrega comentarios o documentos para mejorar la propuesta")

else:
    st.header("📚 Historial de Análisis Postdoctorales")
    
    lista = obtener_analisis()
    
    if not lista:
        st.info("No hay análisis previos. Crea uno nuevo en 'Nuevo Análisis Postdoctoral'")
    else:
        for item in lista:
            with st.expander(f"🎓 {item.get('titulo', 'Sin título')} - {item.get('fecha', '')[:10]}"):
                st.write(f"**Formato:** {item.get('formato_salida', 'N/A')}")
                st.write(f"**Estilo citas:** {item.get('estilo_citas', 'N/A')}")
                st.write(f"**Archivos:** {item.get('archivos', 'N/A')}")
                with st.expander("Ver propuesta completa"):
                    st.markdown(item.get('resultado', 'No disponible')[:3000])

st.markdown("---")
st.caption("🎓 CrewAI Postdoctoral | DeepSeek + Groq | 6 Agentes Especializados | Análisis crítico | Búsqueda en fuentes oficiales | Generación de propuestas | Verificación de cumplimiento")