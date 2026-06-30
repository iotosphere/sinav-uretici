import os
from supabase import create_client, Client
import streamlit as st

# Supabase istemcisini başlat (Singleton yapısı)
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        return None
        
    return create_client(url, key)

def login_user(email, password):
    """Kullanıcı girişi yapar."""
    supabase = init_supabase()
    if not supabase:
        return {"error": "Supabase yapılandırması eksik (.env dosyasını kontrol edin)."}
        
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {"user": response.user, "session": response.session}
    except Exception as e:
        return {"error": str(e)}

def signup_user(email, password):
    """Yeni kullanıcı kaydı oluşturur."""
    supabase = init_supabase()
    if not supabase:
        return {"error": "Supabase yapılandırması eksik."}
        
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return {"user": response.user, "session": response.session}
    except Exception as e:
        return {"error": str(e)}

def logout_user():
    """Çıkış yapar."""
    supabase = init_supabase()
    if supabase:
        supabase.auth.sign_out()
