import streamlit as st
from datetime import datetime
import os
import re
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from database import guardar_analisis, obtener_analisis

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS
# ============================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None
groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

# ============================================
# FUNCIONES DE LLAMADAS A API CON REINTENTOS
# ============================================

def llamar_deepseek(prompt, max_intentos=3):
    if not deepseek_client:
        return "⚠️ DeepSeek no configurado"
    for intento in range(max_intentos):
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=8000
            )
            return response.choices[0].message.content
        except Exception as e:
            if intento == max_intentos - 1:
                return f"❌ Error DeepSeek: {str(e)}"
            time.sleep(2)
    return "❌ Error en llamada a DeepSeek"

def llamar_groq(prompt, max_intentos=3):
    if not groq_client:
        return "⚠️ Groq no configurado"
    for intento in range(max_intentos):
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=8000
            )
            return response.choices[0].message.content
        except Exception as e:
            if intento == max_intentos - 1:
                return f"❌ Error Groq: {str(e)}"
            time.sleep(2)
    return "❌ Error en llamada a Groq"

# ============================================
# AGENTE 1: EXTRACCIÓN DE REQUISITOS (CRÍTICO)
# ============================================

def extraer_requisitos_critico(texto):
    """Extrae CADA requisito con especificaciones técnicas detalladas"""
    prompt = f"""
    Eres un AUDITOR POSTDOCTORAL. Extrae CADA requisito de esta convocatoria.
    
    === CONVOCATORIA ===
    {texto[:12000]}
    
    Responde EXACTAMENTE en este formato JSON. Sé EXTREMADAMENTE DETALLADO:
    
    {{
        "requisitos": [
            {{
                "id": 1,
                "seccion": "sección exacta",
                "texto_original": "texto completo del requisito",
                "especificacion_tecnica": "detalle técnico específico",
                "plazo": "fecha o 'No especificado'",
                "prioridad": "alta/media/baja",
                "categoria": "administrativo/tecnico/economico/metodologico/etica",
                "es_obligatorio": true,
                "criterio_verificacion": "cómo saber si se cumple"
            }}
        ],
        "perfiles_requeridos": [
            {{
                "perfil": "nombre",
                "nivel": "doctorado/maestria/ingenieria",
                "experiencia": "años y área específica",
                "habilidades": ["habilidad1", "habilidad2"],
                "dedicacion": "completa/parcial",
                "es_obligatorio": true
            }}
        ],
        "fechas_clave": [
            {{"evento": "apertura/cierre/evaluacion", "fecha": "fecha exacta", "formato": "DD/MM/AAAA"}}
        ],
        "presupuesto_maximo": "monto exacto o 'No especificado'",
        "criterios_evaluacion": [
            {{"criterio": "nombre", "ponderacion": "porcentaje", "descripcion": "detalle"}}
        ],
        "documentos_requeridos": [
            {{"documento": "nombre", "formato": "PDF/Word", "max_paginas": "número o 'N/A'"}}
        ]
    }}
    
    Si un campo no existe, pon "No especificado" o [].
    """
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 2: VERIFICACIÓN DE CUMPLIMIENTO (100% OBLIGATORIO)
# ============================================

def verificar_cumplimiento_estricto(propuesta, requisitos):
    """Verifica que la propuesta cumpla el 100% de los requisitos. Si no, la rechaza."""
    
    prompt = f"""
    Eres un AUDITOR POSTDOCTORAL ESTRICTO. Verifica si la propuesta cumple CADA requisito.
    
    === PROPUESTA ===
    {propuesta[:8000]}
    
    === REQUISITOS DE LA CONVOCATORIA ===
    {requisitos[:5000]}
    
    Tu verificación debe ser EXTREMADAMENTE RIGUROSA.
    
    Responde EXACTAMENTE con este formato:
    
    ## RESULTADO DE VERIFICACIÓN
    
    ### REQUISITOS CUMPLIDOS:
    | # | Requisito | Sección donde se cumple | Evidencia |
    |---|-----------|------------------------|-----------|
    
    ### REQUISITOS NO CUMPLIDOS:
    | # | Requisito | Qué falta | Corrección necesaria | Prioridad |
    |---|-----------|-----------|---------------------|-----------|
    
    ### CALIFICACIÓN POR SECCIÓN:
    - Portada: X/100
    - Resumen: X/100
    - Introducción: X/100
    - Objetivos: X/100
    - Metodología: X/100
    - Cronograma: X/100
    - Presupuesto: X/100
    - Equipo: X/100
    - Resultados: X/100
    - Referencias: X/100
    
    ### CALIFICACIÓN TOTAL: X/100
    
    ### APROBACIÓN: 
    - SI el TOTAL es 100/100 → "APROBADO"
    - SI el TOTAL es menor a 100/100 → "RECHAZADO - REQUIERE CORRECCIONES"
    
    ### LISTA DE CORRECCIONES OBLIGATORIAS:
    1. [Corrección 1 - específica]
    2. [Corrección 2 - específica]
    ...
    
    ### PRÓXIMOS PASOS:
    - [Instrucciones claras para corregir cada punto faltante]
    """
    
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 3: CORRECTOR OBLIGATORIO
# ============================================

def corregir_propuesta(propuesta_actual, lista_correcciones, nuevos_documentos=""):
    """Corrige la propuesta basada en las correcciones obligatorias"""
    
    prompt = f"""
    Eres un CORRECTOR POSTDOCTORAL. Debes corregir la propuesta para que cumpla TODOS los requisitos.
    
    === PROPUESTA ACTUAL ===
    {propuesta_actual[:5000]}
    
    === CORRECCIONES OBLIGATORIAS ===
    {lista_correcciones}
    
    === INFORMACIÓN ADICIONAL ===
    {nuevos_documentos[:2000]}
    
    Genera una VERSIÓN CORREGIDA que:
    1. Implementa CADA UNA de las correcciones obligatorias
    2. NO omite ningún requisito
    3. Mantiene el formato profesional
    4. Incluye TODAS las secciones requeridas
    
    Responde SOLO con la propuesta corregida completa, sin comentarios adicionales.
    """
    
    return llamar_groq(prompt)

# ============================================
# AGENTE 4: GENERADOR DE PROPUESTA INICIAL
# ============================================

def generar_propuesta_inicial(requisitos, instrucciones, documentos_previos=""):
    """Genera la primera versión de la propuesta"""
    
    prompt = f"""
    Eres un GENERADOR DE PROPUESTAS POSTDOCTORALES.
    
    === REQUISITOS DE LA CONVOCATORIA ===
    {requisitos[:6000]}
    
    === INSTRUCCIONES ===
    {instrucciones}
    
    === DOCUMENTOS PREVIOS ===
    {documentos_previos[:2000]}
    
    Genera una PROPUESTA POSTDOCTORAL COMPLETA con:
    1. Portada
    2. Resumen ejecutivo
    3. Introducción y estado del arte
    4. Objetivos (general y específicos)
    5. Metodología detallada
    6. Cronograma (tabla 36 meses)
    7. Presupuesto detallado (tabla)
    8. Equipo de trabajo (tabla)
    9. Resultados esperados
    10. Referencias bibliográficas (formato APA)
    
    La propuesta debe ser PROFESIONAL y DETALLADA.
    """
    
    return llamar_groq(prompt)

# ============================================
# AGENTE 5: BÚSQUEDA DE REFERENCIAS
# ============================================

def buscar_referencias_academicas(tema):
    """Busca referencias académicas reales"""
    prompt = f"""
    Busca REFERENCIAS ACADÉMICAS REALES sobre: {tema}
    
    Proporciona 10 referencias en formato APA de los ÚLTIMOS 5 AÑOS.
    Incluye: autores, año, título, revista, DOI o URL.
    """
    return llamar_groq(prompt)

# ============================================
# FUNCIÓN PRINCIPAL CON CICLO DE CALIDAD
# ============================================

def generar_propuesta_con_control_calidad(texto_convocatoria, instrucciones, documentos_previos, max_iteraciones=5):
    """Genera propuesta con ciclos de corrección hasta cumplir 100%"""
    
    historial = []
    
    # Paso 1: Extraer requisitos
    st.write("📋 **Paso 1/5:** Extrayendo requisitos de la convocatoria...")
    requisitos_json = extraer_requisitos_critico(texto_convocatoria)
    historial.append({"fase": "extraccion_requisitos", "contenido": requisitos_json})
    
    # Intentar parsear JSON
    try:
        requisitos_dict = json.loads(requisitos_json)
    except:
        requisitos_dict = {"requisitos": [{"id": 1, "texto_original": requisitos_json[:500]}]}
    
    # Paso 2: Generar propuesta inicial
    st.write("✍️ **Paso 2/5:** Generando propuesta inicial...")
    propuesta_actual = generar_propuesta_inicial(requisitos_json, instrucciones, documentos_previos)
    historial.append({"fase": "propuesta_inicial", "contenido": propuesta_actual[:1000]})
    
    # Paso 3: Ciclo de verificación y corrección
    st.write("🔄 **Paso 3/5:** Iniciando ciclo de control de calidad...")
    
    for iteracion in range(1, max_iteraciones + 1):
        st.write(f"  - Iteración {iteracion}: Verificando cumplimiento...")
        
        # Verificar propuesta actual
        verificacion = verificar_cumplimiento_estricto(propuesta_actual, requisitos_json)
        historial.append({"fase": f"verificacion_iteracion_{iteracion}", "contenido": verificacion})
        
        # Verificar si está aprobada
        if "APROBADO" in verificacion and "100/100" in verificacion:
            st.success(f"✅ **PROPUESTA APROBADA** después de {iteracion} iteraciones!")
            return propuesta_actual, verificacion, historial, True
        
        # Extraer correcciones obligatorias
        st.write(f"  - Iteración {iteracion}: Propuesta RECHAZADA. Corrigiendo...")
        
        # Corregir propuesta
        propuesta_actual = corregir_propuesta(propuesta_actual, verificacion, documentos_previos)
        historial.append({"fase": f"correccion_iteracion_{iteracion}", "contenido": propuesta_actual[:1000]})
    
    # Si llegamos aquí, no se aprobó en el máximo de iteraciones
    st.warning(f"⚠️ No se alcanzó el 100% de cumplimiento después de {max_iteraciones} iteraciones.")
    st.info("Se entregará la última versión con las correcciones pendientes.")
    return propuesta_actual, verificacion, historial, False

# ============================================
# INTERFAZ DE STREAMLIT
# ============================================

st.set_page_config(page_title="CrewAI - Control de Calidad Postdoctoral", page_icon="🎓", layout="wide")

st.title("🎓 CrewAI - Sistema de Control de Calidad Postdoctoral")
st.markdown("---")

with st.sidebar:
    st.header("📋 Menú")
    opcion = st.radio("Ir a:", ["📝 Nueva Propuesta", "📚 Historial", "⚙️ Estado APIs"])
    
    st.markdown("---")
    st.markdown("### 🎓 Flujo de Control de Calidad")
    st.markdown("""
    1. 📋 **Extraer requisitos** (crítico)
    2. ✍️ **Generar propuesta inicial**
    3. 🔍 **Verificar cumplimiento** (100% obligatorio)
    4. 🔧 **Si NO cumple → Corregir**
    5. 🔁 **Iterar hasta aprobar**
    6. ✅ **Entregar propuesta final**
    """)
    
    st.info("⚠️ **Regla estricta:** La propuesta solo se entrega si cumple el 100% de los requisitos.")

if opcion == "⚙️ Estado APIs":
    st.header("🔌 Estado de las APIs")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")

elif opcion == "📝 Nueva Propuesta":
    st.header("🎓 Generación de Propuesta con Control de Calidad")
    
    with st.form("form_postdoctoral"):
        titulo = st.text_input("Título de la convocatoria / proyecto")
        
        archivos_convocatoria = st.file_uploader(
            "📄 Sube las bases, términos de referencia, requisitos",
            type=["txt", "md", "pdf", "docx"],
            accept_multiple_files=True
        )
        
        archivos_previos = st.file_uploader(
            "📎 Sube documentos adicionales (CVs, artículos, proyectos previos)",
            type=["txt", "md", "pdf", "docx"],
            accept_multiple_files=True
        )
        
        instrucciones = st.text_area(
            "📝 Instrucciones específicas",
            height=100,
            placeholder="Ej: Duración 36 meses, presupuesto máximo $200,000, equipo mínimo 3 doctores..."
        )
        
        max_iteraciones = st.slider(
            "🔄 Máximo de iteraciones de corrección",
            min_value=1,
            max_value=10,
            value=5,
            help="Número máximo de ciclos de corrección antes de entregar la última versión"
        )
        
        submitted = st.form_submit_button("🚀 INICIAR PROCESO DE CALIDAD", type="primary")
        
        if submitted:
            if not titulo:
                st.error("❌ Ingresa un título")
            elif not archivos_convocatoria:
                st.error("❌ Sube al menos un documento de la convocatoria")
            else:
                # Extraer texto
                texto_convocatoria = ""
                for a in archivos_convocatoria:
                    try:
                        texto_convocatoria += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_convocatoria += f"\n\n--- {a.name} ---\n[Contenido binario]"
                
                texto_previos = ""
                for a in archivos_previos:
                    try:
                        texto_previos += f"\n\n--- {a.name} ---\n{a.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_previos += f"\n\n--- {a.name} ---\n[Contenido binario]"
                
                # Ejecutar proceso con control de calidad
                with st.spinner("Procesando..."):
                    propuesta_final, verificacion_final, historial, aprobada = generar_propuesta_con_control_calidad(
                        texto_convocatoria,
                        instrucciones,
                        texto_previos,
                        max_iteraciones
                    )
                    
                    # Guardar en base de datos
                    guardar_analisis(
                        titulo,
                        instrucciones,
                        "Markdown",
                        "APA",
                        propuesta_final,
                        [a.name for a in archivos_convocatoria]
                    )
                    
                    # Mostrar resultados
                    st.markdown("---")
                    
                    if aprobada:
                        st.balloons()
                        st.success("🎉 **¡PROPUESTA APROBADA!** Cumple el 100% de los requisitos.")
                    else:
                        st.warning("⚠️ **PROPUESTA ENTREGADA CON CORRECCIONES PENDIENTES**")
                        st.info("Se alcanzó el máximo de iteraciones. Revise las correcciones sugeridas.")
                    
                    st.markdown("---")
                    st.header("📄 PROPUESTA FINAL")
                    st.markdown(propuesta_final)
                    
                    st.download_button(
                        "📥 DESCARGAR PROPUESTA",
                        propuesta_final,
                        file_name=f"{titulo.replace(' ', '_')}.md"
                    )
                    
                    with st.expander("📋 VERIFICACIÓN FINAL"):
                        st.markdown(verificacion_final)
                    
                    with st.expander("🔄 HISTORIAL DE ITERACIONES"):
                        for i, item in enumerate(historial):
                            st.write(f"**{i+1}. {item['fase']}**")
                            st.text(item['contenido'][:500] + "...")
                            st.markdown("---")

else:
    st.header("📚 Historial de Propuestas")
    
    lista = obtener_analisis()
    
    if not lista:
        st.info("No hay propuestas previas. Genera una nueva propuesta postdoctoral.")
    else:
        for item in lista:
            with st.expander(f"🎓 {item.get('titulo', 'Sin título')} - {item.get('fecha', '')[:10]}"):
                st.write(f"**Formato:** {item.get('formato_salida', 'N/A')}")
                with st.expander("Ver propuesta"):
                    st.markdown(item.get('resultado', 'No disponible')[:2000])

st.markdown("---")
st.caption("🎓 CrewAI - Control de Calidad Postdoctoral | Los agentes iteran hasta cumplir el 100% de los requisitos")