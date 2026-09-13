# database.py
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Nomes das tabelas/views no Supabase que alimentam cada aba do painel.
# Ajuste aqui quando confirmar o schema real do seu projeto (ex: se forem
# views geradas por dbt no padrão "gold_<relatorio>").
TABELAS_GOLD = {
    "visao_geral": "gold_visao_geral",
    "evolucao_temporal": "gold_evolucao_temporal",
    "logistica": "gold_logistica",
    "categorias": "gold_categorias",
    "pagamentos": "gold_pagamentos",
    "clusterizacao": "gold_clusterizacao",
    "dados_brutos": "fii_gold_metrics",
}

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

@st.cache_data(ttl=600)
def buscar_dataframe(nome_tabela: str) -> pd.DataFrame:
    """Lê uma tabela/view do Supabase já como DataFrame, pronta para os relatórios."""
    return pd.DataFrame(buscar_dados_tabela(nome_tabela))

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