import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit_authenticator as stauth

# Importando o módulo que você criou corretamente com @st.cache_resource!
from database import buscar_dados_tabela

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Analítico Olist",
    page_icon="📊",
    layout="wide"
)

# ==============================================================================
# 2. AUTENTICAÇÃO E SEGURANÇA (stauth + st.secrets)
# ==============================================================================
auth_config = st.secrets["auth"].to_dict()

# Instanciando o autenticador no padrão estável
authenticator = stauth.Authenticate(
    credentials=auth_config["credentials"],
    cookie_name=str(auth_config["cookie"]["name"]),
    cookie_key=str(auth_config["cookie"]["key"]),
    cookie_expiry_days=int(auth_config["cookie"]["expiry_days"])
)

# Renderiza a tela de login
authenticator.login()

# ==============================================================================
# 3. CONTROLE DE ACESSO E CONTEÚDO PROTEGIDO
# ==============================================================================
if st.session_state.get("authentication_status") is False:
    st.error("Usuário ou senha incorretos.")

elif st.session_state.get("authentication_status") is None:
    st.info("Por favor, insira suas credenciais na barra lateral/tela para acessar o painel.")

elif st.session_state.get("authentication_status"):

    # Sidebar com Boas-Vindas, Perfil (RBAC) e Logout
    username = st.session_state.get("username")
    
    # Recuperando o nome e o papel (role) de forma segura do dict de credentials
    user_data = auth_config["credentials"]["usernames"].get(username, {})
    user_name = user_data.get("name", username)
    user_role = user_data.get("role", "Viewer")

    st.sidebar.markdown(f"### 👤 {user_name}")
    st.sidebar.caption(f"Perfil: **{user_role}**")
    
    # Botão de Logout
    authenticator.logout("Sair do Sistema", location="sidebar")

    st.title("📊 Painel Analítico Olist")
    st.markdown("---")

    # BUSCA DE DADOS NO SUPABASE (Usando a função cached de database.py)
    dados_supabase = buscar_dados_tabela("fii_gold_metrics")
    df_geral = pd.DataFrame(dados_supabase) if dados_supabase else pd.DataFrame()

    # DEFINIÇÃO DAS 7 ABAS
    (
        tab_visao_geral, 
        tab_evolucao, 
        tab_logistica, 
        tab_categorias, 
        tab_pagamentos, 
        tab_clusterizacao, 
        tab_dados_brutos
    ) = st.tabs([
        "📌 Visão Geral & Retenção",
        "📈 Evolução Temporal & Horários",
        "🚚 Logística & Entregas",
        "🏷️ Receita por Categoria",
        "💳 Formas de Pagamento",
        "🤖 Clusterização & ML",
        "📋 Dados Brutos & Filtros"
    ])

    # --------------------------------------------------------------------------
    # ABA 1: VISÃO GERAL & RETENÇÃO
    # --------------------------------------------------------------------------
    with tab_visao_geral:
        st.subheader("📌 Visão Geral do Negócio & Taxa de Retenção")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Pedidos", "99,441")
        m2.metric("Receita Total", "R$ 13.59M")
        m3.metric("Ticket Médio", "R$ 136.68")
        m4.metric("Taxa de Recompra (Churn)", "3.12%")

        st.info("💡 **Insight de Retenção:** Apenas uma pequena fatia da base realiza novas compras. Foco recomendado em estratégias de fidelização e análise do perfil VIP.")

    # --------------------------------------------------------------------------
    # ABA 2: EVOLUÇÃO TEMPORAL & HORÁRIOS
    # --------------------------------------------------------------------------
    with tab_evolucao:
        st.subheader("📈 Evolução Temporal e Horários de Consumo")
        
        # Corrigido freq="M" para compatibilidade universal no Pandas
        datas = pd.date_range(start="2017-01-01", periods=24, freq="M")
        df_tempo = pd.DataFrame({
            "mes": datas,
            "faturamento": [15000 * (i + 1) for i in range(24)],
            "pedidos": [100 + (i * 15) for i in range(24)]
        })

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_fat = px.line(df_tempo, x="mes", y="faturamento", title="<b>Evolução do Faturamento Mensal</b>", markers=True)
            st.plotly_chart(fig_fat, use_container_width=True)
        
        with col_t2:
            fig_ped = px.bar(df_tempo, x="mes", y="pedidos", title="<b>Volume de Pedidos Mensais</b>")
            st.plotly_chart(fig_ped, use_container_width=True)

    # --------------------------------------------------------------------------
    # ABA 3: LOGÍSTICA & ENTREGAS
    # --------------------------------------------------------------------------
    with tab_logistica:
        st.subheader("🚚 Análise de Logística e SLA de Entregas")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.metric("Prazo Médio de Entrega", "12.5 dias")
            st.metric("Taxa de Entregas com Atraso", "7.8%")
        with col_l2:
            st.write("Métricas de frete por estado e performance das transportadoras...")

    # --------------------------------------------------------------------------
    # ABA 4: RECEITA POR CATEGORIA
    # --------------------------------------------------------------------------
    with tab_categorias:
        st.subheader("🏷️ Receita e Volume por Categoria de Produto")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.info("Análise de curva ABC das categorias mais rentáveis (ex: Cama, Mesa e Banho, Beleza & Saúde).")
        with col_c2:
            st.write("Gráficos comparativos de categorias...")

    # --------------------------------------------------------------------------
    # ABA 5: FORMAS DE PAGAMENTO
    # --------------------------------------------------------------------------
    with tab_pagamentos:
        st.subheader("💳 Meios de Pagamento e Parcelamento")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write("Distribuição entre Cartão de Crédito, Boleto, Voucher e PIX.")
        with col_p2:
            st.write("Análise da distribuição de parcelamento (1x até 12x).")

    # --------------------------------------------------------------------------
    # ABA 6: CLUSTERIZAÇÃO & ML
    # --------------------------------------------------------------------------
    with tab_clusterizacao:
        st.subheader("🤖 Segmentação de Clientes via Machine Learning")
        
        # Exibição condicional com base no perfil RBAC
        if user_role in ["Admin", "Editor"]:
            st.success("Perfil autorizado para visualização e execução de rotinas de ML.")
            st.write("Agrupamento de clientes via modelo RFM (Recência, Frequência, Valor).")
        else:
            st.warning("Seu perfil (Viewer) tem acesso limitado aos insights pré-calculados dos clusters.")

    # --------------------------------------------------------------------------
    # ABA 7: DADOS BRUTOS & FILTROS
    # --------------------------------------------------------------------------
    with tab_dados_brutos:
        st.subheader("📋 Consulta de Dados Brutos & Filtros Avançados")
        
        if not df_geral.empty:
            st.dataframe(df_geral, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado no Supabase para exibição imediata na tabela.")