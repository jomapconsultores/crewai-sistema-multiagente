from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

def guardar_analisis(titulo, instrucciones, formato, estilo, resultado, archivos):
    supabase = get_supabase()
    if not supabase:
        print("⚠️ Supabase no configurado")
        return None
    
    data = {
        "titulo": titulo,
        "instrucciones": instrucciones,
        "formato_salida": formato,
        "estilo_citas": estilo,
        "resultado": resultado[:10000],
        "archivos": ", ".join(archivos),
        "fecha": datetime.now().isoformat()
    }
    
    try:
        result = supabase.table("sesiones").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error guardando: {e}")
        return None

def obtener_analisis():
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        result = supabase.table("sesiones").select("*").order("fecha", desc=True).execute()
        return result.data
    except Exception as e:
        print(f"Error obteniendo: {e}")
        return []