import streamlit as st
from supabase import create_client
from datetime import datetime
import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import base64
from PIL import Image
import io

load_dotenv()

# ============================================
# CONFIGURACIÓN DE APIS REALES
# ============================================

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Gemini (con soporte multimodal para imágenes)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_vision_model = None

# ============================================
# FUNCIONES PARA PROCESAR IMÁGENES
# ============================================

def imagen_a_base64(imagen_bytes):
    """Convierte imagen a base64 para enviar a API"""
    return base64.b64encode(imagen_bytes).decode('utf-8')

def analizar_imagen_con_gemini(imagen_bytes, prompt):
    """Analiza una imagen usando Gemini (multimodal)"""
    if not gemini_vision_model:
        return "⚠️ Gemini no configurado. Agrega GEMINI_API_KEY en .env"
    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(imagen_bytes))
        response = gemini_vision_model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"❌ Error analizando imagen: {str(e)}"

def extraer_texto_imagen(imagen_bytes):
    """Extrae texto de una imagen usando OCR con Gemini"""
    prompt = """Extrae TODO el texto que aparece en esta imagen. 
    Si hay gráficos, tablas o diagramas, descríbelos en detalle.
    Si hay números o datos, extráelos con precisión.
    """
    return analizar_imagen_con_gemini(imagen_bytes, prompt)

def analizar_diagrama(imagen_bytes):
    """Analiza un diagrama o gráfico"""
    prompt = """Analiza este diagrama/gráfico en detalle:
    1. ¿Qué tipo de gráfico/diagrama es?
    2. ¿Qué datos o información muestra?
    3. ¿Cuál es la conclusión principal?
    4. ¿Hay algún error o inconsistencia visual?
    """
    return analizar_imagen_con_gemini(imagen_bytes, prompt)

def verificar_grafico(imagen_bytes):
    """Verifica formato y calidad de gráficos"""
    prompt = """Verifica este gráfico/imagen:
    1. Calidad de imagen (resolución, nitidez)
    2. Claridad de etiquetas y leyendas
    3. Si las escalas son apropiadas
    4. Si cumple con estándares académicos
    """
    return analizar_imagen_con_gemini(imagen_bytes, prompt)

# ============================================
# FUNCIONES PARA PROCESAR DOCUMENTOS
# ============================================

def procesar_archivo(archivo):
    """Procesa cualquier tipo de archivo (texto, imagen, documento)"""
    nombre = archivo.name
    extension = nombre.split('.')[-1].lower() if '.' in nombre else ''
    
    contenido = {
        "nombre": nombre,
        "tipo": extension,
        "texto_extraido": "",
        "analisis_imagen": None,
        "es_imagen": False
    }
    
    try:
        bytes_data = archivo.getvalue()
        
        # Imágenes
        if extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff']:
            contenido["es_imagen"] = True
            contenido["texto_extraido"] = extraer_texto_imagen(bytes_data)
            contenido["analisis_diagrama"] = analizar_diagrama(bytes_data)
            contenido["verificacion_grafico"] = verificar_grafico(bytes_data)
            
            # Guardar miniatura para mostrar
            try:
                img = Image.open(io.BytesIO(bytes_data))
                contenido["dimensiones"] = f"{img.width}x{img.height}"
            except:
                contenido["dimensiones"] = "desconocido"
        
        # Documentos de texto
        elif extension in ['txt', 'md', 'py', 'json', 'csv']:
            contenido["texto_extraido"] = bytes_data.decode('utf-8', errors='ignore')
        
        # PDF, Word, Excel (extracción básica)
        else:
            contenido["texto_extraido"] = f"[Archivo {extension.upper()} - {len(bytes_data)} bytes]"
            
    except Exception as e:
        contenido["texto_extraido"] = f"Error al leer archivo: {str(e)}"
    
    return contenido

# ============================================
# FUNCIONES DE LOS AGENTES
# ============================================

def llamar_deepseek(prompt):
    if not DEEPSEEK_API_KEY:
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
    if not GROQ_API_KEY:
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

def llamar_gemini(prompt):
    if not gemini_vision_model:
        return "⚠️ Gemini no configurado"
    try:
        response = gemini_vision_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error Gemini: {str(e)}"

# ============================================
# AGENTE 1: Análisis de Contenido (DeepSeek)
# ============================================

def agente_contenido(texto_completo, analisis_imagenes, instrucciones):
    prompt = f"""
    Eres un Analista de Contenido Científico. Analiza TODO el material proporcionado.
    
    === INSTRUCCIONES ===
    {instrucciones}
    
    === TEXTO EXTRAÍDO ===
    {texto_completo[:8000]}
    
    === ANÁLISIS DE IMÁGENES ===
    {analisis_imagenes[:3000]}
    
    Tu tarea:
    1. Sintetiza la información de texto e imágenes
    2. Verifica coherencia entre lo que dicen los textos y lo que muestran las imágenes
    3. Identifica inconsistencias
    4. Evalúa la calidad científica global
    
    Responde con:
    - RESUMEN INTEGRADO (texto + imágenes)
    - COHERENCIA TEXTO-IMAGEN
    - INCONSISTENCIAS ENCONTRADAS
    - CALIFICACIÓN (X/10)
    """
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 2: Análisis de Imágenes (Gemini)
# ============================================

def agente_analisis_imagenes(imagenes_data):
    if not imagenes_data:
        return "No se encontraron imágenes para analizar"
    
    resultados = []
    for img in imagenes_data:
        resultados.append(f"""
### 📷 {img['nombre']} ({img.get('dimensiones', 'desconocido')})

**Texto extraído:**
{img['texto_extraido'][:500]}

**Análisis del diagrama/gráfico:**
{img.get('analisis_diagrama', 'No disponible')[:500]}

**Verificación de formato:**
{img.get('verificacion_grafico', 'No disponible')[:300]}
""")
    return "\n\n".join(resultados)

# ============================================
# AGENTE 3: Revisor de Formato (Gemini)
# ============================================

def agente_formato(texto, estilo_citas, imagenes_info):
    prompt = f"""
    Eres un Revisor de Formato Académico.
    
    === TEXTO ===
    {texto[:5000]}
    
    === IMÁGENES ===
    {imagenes_info[:2000]}
    
    === ESTILO DE CITAS ===
    {estilo_citas}
    
    Verifica:
    1. Formato de texto (fuente, márgenes, títulos)
    2. Formato de imágenes (resolución, etiquetas, referencias)
    3. Estilo de citas
    4. Coherencia entre referencias a imágenes y su ubicación
    
    Responde con VEREDICTO y CORRECCIONES necesarias.
    """
    return llamar_gemini(prompt)

# ============================================
# AGENTE 4: Verificador de Citas (Groq)
# ============================================

def agente_citas(texto, estilo_citas):
    prompt = f"""
    Verifica TODAS las citas en el documento.
    
    === TEXTO ===
    {texto[:8000]}
    
    === ESTILO ===
    {estilo_citas.upper()}
    
    Responde con:
    - TOTAL DE CITAS ENCONTRADAS
    - TOTAL DE REFERENCIAS
    - ERRORES (lista)
    - VEREDICTO FINAL
    """
    return llamar_groq(prompt)

# ============================================
# AGENTE 5: Corrector Ortográfico (Groq)
# ============================================

def agente_ortografia(texto):
    prompt = f"""
    Corrige ortografía y gramática del siguiente texto:
    
    {texto[:8000]}
    
    Responde con:
    - ERRORES ENCONTRADOS (cantidad y lista)
    - CORRECCIONES SUGERIDAS
    - CALIFICACIÓN (1-10)
    """
    return llamar_groq(prompt)

# ============================================
# AGENTE 6: Evaluador de Cumplimiento (DeepSeek)
# ============================================

def agente_evaluador(requisitos, resultados):
    prompt = f"""
    Evalúa si el documento cumple con TODOS los requisitos.
    
    === REQUISITOS ===
    {requisitos}
    
    === RESULTADOS ===
    Contenido: {resultados.get('contenido', '')[:800]}
    Formato: {resultados.get('formato', '')[:500]}
    Citas: {resultados.get('citas', '')[:500]}
    Ortografía: {resultados.get('ortografia', '')[:500]}
    Imágenes: {resultados.get('imagenes', '')[:500]}
    
    Responde con:
    - LISTA DE VERIFICACIÓN (✅ o ❌)
    - SI NO CUMPLE: qué falta
    - SI CUMPLE: APROBACIÓN
    """
    return llamar_deepseek(prompt)

# ============================================
# AGENTE 7: Generador Final (Gemini)
# ============================================

def agente_generador(texto, formato, estilo_citas, resultados, imagenes_info):
    prompt = f"""
    Genera el documento FINAL integrando texto e imágenes.
    
    === CONTENIDO ORIGINAL ===
    {texto[:5000]}
    
    === ANÁLISIS DE IMÁGENES ===
    {imagenes_info[:2000]}
    
    === RESULTADOS DE AGENTES ===
    {resultados}
    
    === FORMATO ===
    {formato}
    
    === ESTILO CITAS ===
    {estilo_citas}
    
    Genera un documento profesional con:
    1. PORTADA
    2. RESUMEN EJECUTIVO (integrando hallazgos de texto e imágenes)
    3. ANÁLISIS DETALLADO
    4. TABLA DE VERIFICACIÓN DE REQUISITOS
    5. CONCLUSIONES
    6. BIBLIOGRAFÍA (formato {estilo_citas})
    """
    return llamar_gemini(prompt)

# ============================================
# INTERFAZ DE STREAMLIT
# ============================================

st.set_page_config(page_title="CrewAI - Sistema Multiagente", page_icon="🤖", layout="wide")

st.title("🤖 CrewAI - Sistema Multiagente con Análisis de Imágenes")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📋 Navegación")
    opcion = st.radio("Ir a:", ["📝 Nuevo Análisis", "📚 Historial", "⚙️ Estado de APIs"])
    
    st.markdown("---")
    st.markdown("### 🎨 Formatos soportados")
    st.markdown("""
    **Documentos:** Word, Excel, PDF, TXT, MD  
    **Imágenes:** PNG, JPG, JPEG, GIF, BMP, WEBP, TIFF
    """)

if opcion == "⚙️ Estado de APIs":
    st.header("🔌 Estado de APIs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
    with col2:
        st.success("✅ Groq") if GROQ_API_KEY else st.error("❌ Groq")
    with col3:
        st.success("✅ Gemini (multimodal)") if GEMINI_API_KEY else st.error("❌ Gemini")

elif opcion == "📝 Nuevo Análisis":
    st.header("📝 Nuevo Análisis con soporte para IMÁGENES")
    
    with st.form("form_analisis"):
        col1, col2 = st.columns(2)
        
        with col1:
            titulo = st.text_input("Título del análisis")
            formato = st.selectbox("Formato de salida", ["Word", "PDF", "Excel", "Markdown"])
        
        with col2:
            estilo_citas = st.selectbox("Estilo de citación", ["APA", "Vancouver", "MLA", "Chicago"])
            nivel_rigor = st.select_slider("Nivel de rigor", ["Básico", "Estándar", "Alto", "Máximo"])
        
        st.subheader("📎 Subir archivos (documentos e imágenes)")
        archivos = st.file_uploader(
            "Acepta: Word, Excel, PDF, TXT, PNG, JPG, GIF, BMP, WEBP, TIFF",
            type=["txt", "md", "pdf", "docx", "xlsx", "png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"],
            accept_multiple_files=True
        )
        
        instrucciones = st.text_area(
            "Instrucciones específicas",
            placeholder="Ej: Analiza los diagramas, verifica las citas, corrige errores...",
            height=150
        )
        
        submitted = st.form_submit_button("🚀 Iniciar Análisis Multiagente", type="primary")
        
        if submitted:
            if not titulo or not archivos or not instrucciones:
                st.error("❌ Completa todos los campos")
            else:
                progress = st.progress(0)
                status = st.empty()
                
                # Procesar archivos (separando imágenes del resto)
                documentos = []
                imagenes = []
                
                for archivo in archivos:
                    ext = archivo.name.split('.')[-1].lower()
                    if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff']:
                        imagenes.append(archivo)
                    else:
                        documentos.append(archivo)
                
                status.info(f"📄 Procesando {len(documentos)} documento(s) y {len(imagenes)} imagen(es)...")
                
                # Extraer texto de documentos
                texto_completo = ""
                for doc in documentos:
                    try:
                        texto_completo += f"\n\n--- {doc.name} ---\n{doc.getvalue().decode('utf-8', errors='ignore')}"
                    except:
                        texto_completo += f"\n\n--- {doc.name} ---\n[Contenido binario]"
                
                progress.progress(1/7)
                
                # Procesar imágenes con Gemini (Agente especializado)
                status.info("📷 Agente de Imágenes: Analizando fotos y diagramas (Gemini)...")
                imagenes_procesadas = []
                for img in imagenes:
                    img_bytes = img.getvalue()
                    analisis = {
                        "nombre": img.name,
                        "texto_extraido": extraer_texto_imagen(img_bytes),
                        "analisis_diagrama": analizar_diagrama(img_bytes),
                        "verificacion_grafico": verificar_grafico(img_bytes),
                        "dimensiones": "desconocido"
                    }
                    try:
                        from PIL import Image
                        import io
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        analisis["dimensiones"] = f"{pil_img.width}x{pil_img.height}"
                    except:
                        pass
                    imagenes_procesadas.append(analisis)
                
                analisis_imagenes_texto = agente_analisis_imagenes(imagenes_procesadas)
                progress.progress(2/7)
                
                resultados = {}
                
                # Agente 1: Contenido (DeepSeek)
                status.info("🤖 Agente 1/7: Analizando contenido (DeepSeek)...")
                resultados["contenido"] = agente_contenido(texto_completo, analisis_imagenes_texto, instrucciones)
                progress.progress(3/7)
                
                # Agente 2: Formato (Gemini)
                status.info("📐 Agente 2/7: Revisando formato (Gemini)...")
                resultados["formato"] = agente_formato(texto_completo, estilo_citas, analisis_imagenes_texto)
                progress.progress(4/7)
                
                # Agente 3: Citas (Groq)
                status.info("📚 Agente 3/7: Verificando citas (Groq)...")
                resultados["citas"] = agente_citas(texto_completo, estilo_citas)
                progress.progress(5/7)
                
                # Agente 4: Ortografía (Groq)
                status.info("✍️ Agente 4/7: Corrigiendo ortografía (Groq)...")
                resultados["ortografia"] = agente_ortografia(texto_completo)
                progress.progress(6/7)
                
                # Agente 5: Evaluador (DeepSeek)
                status.info("✅ Agente 5/7: Evaluando cumplimiento (DeepSeek)...")
                resultados["evaluacion"] = agente_evaluador(instrucciones, resultados)
                progress.progress(6.5/7)
                
                # Agente 6: Generador Final (Gemini)
                status.info("📄 Agente 6/7: Generando documento final (Gemini)...")
                documento_final = agente_generador(
                    texto_completo, formato, estilo_citas, 
                    resultados, analisis_imagenes_texto
                )
                progress.progress(7/7)
                
                status.success(f"✅ Análisis completado! {len(documentos)} documentos + {len(imagenes)} imágenes procesadas")
                
                # Mostrar resultados
                st.markdown("---")
                st.header("📊 Resultados del Análisis")
                
                # Vista previa de imágenes
                if imagenes:
                    st.subheader("📷 Imágenes analizadas")
                    cols = st.columns(min(len(imagenes), 4))
                    for i, img in enumerate(imagenes):
                        with cols[i % 4]:
                            st.image(img, caption=img.name, use_container_width=True)
                
                tabs = st.tabs(["📄 Documento Final", "🔍 Agentes", "🖼️ Análisis de Imágenes", "✅ Verificación"])
                
                with tabs[0]:
                    st.markdown(documento_final)
                    st.download_button("📥 Descargar", documento_final, file_name=f"{titulo}.md")
                
                with tabs[1]:
                    for nombre, resultado in resultados.items():
                        with st.expander(f"🤖 {nombre.upper()}"):
                            st.markdown(resultado)
                
                with tabs[2]:
                    st.markdown(analisis_imagenes_texto)
                
                with tabs[3]:
                    st.markdown(resultados.get("evaluacion", "No disponible"))

else:
    st.header("📚 Historial de Análisis")
    st.info("Los análisis se guardan aquí automáticamente.")