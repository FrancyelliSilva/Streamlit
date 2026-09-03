# database.py
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa e mantém o cache do cliente Supabase."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        if "seu-projeto" in url or "sua-chave" in key:
            return None
            
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro na conexão com Supabase: {e}")
        return None

def buscar_dados_tabela(nome_tabela: str):
    """Lê todos os registros de uma tabela."""
    supabase = init_supabase()
    if not supabase:
        return []
    try:
        response = supabase.table(nome_tabela).select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao consultar '{nome_tabela}': {e}")
        return []

def inserir_registro(nome_tabela: str, dados: dict) -> bool:
    """Insere um novo dicionário de dados na tabela."""
    supabase = init_supabase()
    if not supabase:
        return False
    try:
        supabase.table(nome_tabela).insert(dados).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir registro: {e}")
        return False

def deletar_registro(nome_tabela: str, id_registro: int) -> bool:
    """Deleta um registro com base no seu ID."""
    supabase = init_supabase()
    if not supabase:
        return False
    try:
        supabase.table(nome_tabela).delete().eq("id", id_registro).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar registro: {e}")
        return False