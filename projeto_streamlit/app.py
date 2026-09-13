import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit_authenticator as stauth

from database import buscar_dataframe, TABELAS_GOLD

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Analítico Olist",
    page_icon="📊",
    layout="wide"
)

# ==============================================================================
# FUNÇÕES AUXILIARES DE RENDERIZAÇÃO
# ==============================================================================

def primeira_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Retorna o primeiro nome de coluna existente no DataFrame, dentre os candidatos."""
    for nome in candidatos:
        if nome in df.columns:
            return nome
    return None

def formatar_valor(valor, tipo: str = "numero") -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    if tipo == "moeda":
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if tipo == "percentual":
        return f"{float(valor):.2f}%"
    if isinstance(valor, (int, float)):
        return f"{valor:,.0f}".replace(",", ".")
    return str(valor)

def aviso_tabela_ausente(nome_tabela: str, colunas_sugeridas: list[str]) -> None:
    st.warning(
        f"Nenhum dado encontrado na tabela/view **`{nome_tabela}`** no Supabase.\n\n"
        f"Crie essa tabela/view com colunas como: `{'`, `'.join(colunas_sugeridas)}`."
    )

# ==============================================================================
# 2. AUTENTICAÇÃO E SEGURANÇA (stauth + st.secrets)
# ==============================================================================
auth_config = st.secrets["auth"].to_dict()

authenticator = stauth.Authenticate(
    credentials=auth_config["credentials"],
    cookie_name=str(auth_config["cookie"]["name"]),
    cookie_key=str(auth_config["cookie"]["key"]),
    cookie_expiry_days=int(auth_config["cookie"]["expiry_days"])
)

authenticator.login()

# ==============================================================================
# 3. CONTROLE DE ACESSO E CONTEÚDO PROTEGIDO
# ==============================================================================
if st.session_state.get("authentication_status") is False:
    st.error("Usuário ou senha incorretos.")

elif st.session_state.get("authentication_status") is None:
    st.info("Por favor, insira suas credenciais na barra lateral/tela para acessar o painel.")

elif st.session_state.get("authentication_status"):

    username = st.session_state.get("username")
    user_data = auth_config["credentials"]["usernames"].get(username, {})
    user_name = user_data.get("name", username)
    user_role = user_data.get("role", "Viewer")

    st.sidebar.markdown(f"### 👤 {user_name}")
    st.sidebar.caption(f"Perfil: **{user_role}**")

    authenticator.logout("Sair do Sistema", location="sidebar")

    st.title("📊 Painel Analítico Olist")
    st.markdown("---")

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

        df_vg = buscar_dataframe(TABELAS_GOLD["visao_geral"])

        if df_vg.empty:
            aviso_tabela_ausente(
                TABELAS_GOLD["visao_geral"],
                ["total_pedidos", "receita_total", "ticket_medio", "taxa_recompra"]
            )
        else:
            linha = df_vg.iloc[0]
            col_pedidos = primeira_coluna(df_vg, ["total_pedidos", "qtd_pedidos", "pedidos"])
            col_receita = primeira_coluna(df_vg, ["receita_total", "faturamento_total", "valor_total"])
            col_ticket = primeira_coluna(df_vg, ["ticket_medio", "valor_medio_pedido"])
            col_recompra = primeira_coluna(df_vg, ["taxa_recompra", "taxa_retencao", "churn"])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total de Pedidos", formatar_valor(linha.get(col_pedidos)) if col_pedidos else "—")
            m2.metric("Receita Total", formatar_valor(linha.get(col_receita), "moeda") if col_receita else "—")
            m3.metric("Ticket Médio", formatar_valor(linha.get(col_ticket), "moeda") if col_ticket else "—")
            m4.metric("Taxa de Recompra", formatar_valor(linha.get(col_recompra), "percentual") if col_recompra else "—")

            if not all([col_pedidos, col_receita, col_ticket, col_recompra]):
                st.caption(
                    f"Algumas colunas esperadas não foram encontradas em `{TABELAS_GOLD['visao_geral']}`. "
                    "Ajuste os nomes em `TABELAS_GOLD`/`primeira_coluna()` no app.py conforme seu schema."
                )

    # --------------------------------------------------------------------------
    # ABA 2: EVOLUÇÃO TEMPORAL & HORÁRIOS
    # --------------------------------------------------------------------------
    with tab_evolucao:
        st.subheader("📈 Evolução Temporal e Horários de Consumo")

        df_tempo = buscar_dataframe(TABELAS_GOLD["evolucao_temporal"])

        if df_tempo.empty:
            aviso_tabela_ausente(
                TABELAS_GOLD["evolucao_temporal"],
                ["mes", "faturamento", "pedidos"]
            )
        else:
            col_data = primeira_coluna(df_tempo, ["mes", "data", "periodo", "ano_mes", "mes_referencia"])
            col_receita = primeira_coluna(df_tempo, ["faturamento", "receita", "valor_total"])
            col_pedidos = primeira_coluna(df_tempo, ["pedidos", "qtd_pedidos", "total_pedidos"])

            if col_data:
                df_tempo[col_data] = pd.to_datetime(df_tempo[col_data], errors="coerce")
                df_tempo = df_tempo.sort_values(col_data)

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                if col_data and col_receita:
                    fig_fat = px.line(df_tempo, x=col_data, y=col_receita, title="<b>Evolução do Faturamento Mensal</b>", markers=True)
                    st.plotly_chart(fig_fat, use_container_width=True)
                else:
                    st.caption("Coluna de faturamento não encontrada.")
            with col_t2:
                if col_data and col_pedidos:
                    fig_ped = px.bar(df_tempo, x=col_data, y=col_pedidos, title="<b>Volume de Pedidos Mensais</b>")
                    st.plotly_chart(fig_ped, use_container_width=True)
                else:
                    st.caption("Coluna de pedidos não encontrada.")

            if not (col_data and (col_receita or col_pedidos)):
                st.dataframe(df_tempo, use_container_width=True)

    # --------------------------------------------------------------------------
    # ABA 3: LOGÍSTICA & ENTREGAS
    # --------------------------------------------------------------------------
    with tab_logistica:
        st.subheader("🚚 Análise de Logística e SLA de Entregas")

        df_log = buscar_dataframe(TABELAS_GOLD["logistica"])

        if df_log.empty:
            aviso_tabela_ausente(
                TABELAS_GOLD["logistica"],
                ["prazo_medio_entrega", "taxa_atraso", "estado", "frete_medio"]
            )
        else:
            col_prazo = primeira_coluna(df_log, ["prazo_medio_entrega", "tempo_medio_entrega", "lead_time_medio"])
            col_atraso = primeira_coluna(df_log, ["taxa_atraso", "pct_atraso", "taxa_entregas_atraso"])
            col_estado = primeira_coluna(df_log, ["estado", "uf", "customer_state"])
            col_frete = primeira_coluna(df_log, ["frete_medio", "valor_frete_medio", "freight_value_medio"])

            col_l1, col_l2 = st.columns(2)
            with col_l1:
                linha = df_log.iloc[0]
                st.metric("Prazo Médio de Entrega (dias)", formatar_valor(linha.get(col_prazo)) if col_prazo else "—")
                st.metric("Taxa de Entregas com Atraso", formatar_valor(linha.get(col_atraso), "percentual") if col_atraso else "—")
            with col_l2:
                if col_estado and col_frete:
                    fig_frete = px.bar(df_log, x=col_estado, y=col_frete, title="Frete Médio por Estado")
                    st.plotly_chart(fig_frete, use_container_width=True)
                else:
                    st.dataframe(df_log, use_container_width=True)

    # --------------------------------------------------------------------------
    # ABA 4: RECEITA POR CATEGORIA
    # --------------------------------------------------------------------------
    with tab_categorias:
        st.subheader("🏷️ Receita e Volume por Categoria de Produto")

        df_cat = buscar_dataframe(TABELAS_GOLD["categorias"])

        if df_cat.empty:
            aviso_tabela_ausente(
                TABELAS_GOLD["categorias"],
                ["categoria", "receita", "quantidade"]
            )
        else:
            col_categoria = primeira_coluna(df_cat, ["categoria", "nome_categoria", "product_category_name"])
            col_receita = primeira_coluna(df_cat, ["receita", "faturamento", "valor_total"])
            col_qtd = primeira_coluna(df_cat, ["quantidade", "qtd_vendida", "volume"])

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if col_categoria and col_receita:
                    top_receita = df_cat.sort_values(col_receita, ascending=False).head(10)
                    fig = px.bar(top_receita, x=col_receita, y=col_categoria, orientation="h", title="Top 10 Categorias por Receita")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Colunas de categoria/receita não encontradas.")
            with col_c2:
                if col_categoria and col_qtd:
                    top_qtd = df_cat.sort_values(col_qtd, ascending=False).head(10)
                    fig = px.bar(top_qtd, x=col_qtd, y=col_categoria, orientation="h", title="Top 10 Categorias por Volume")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(df_cat, use_container_width=True)

    # --------------------------------------------------------------------------
    # ABA 5: FORMAS DE PAGAMENTO
    # --------------------------------------------------------------------------
    with tab_pagamentos:
        st.subheader("💳 Meios de Pagamento e Parcelamento")

        df_pag = buscar_dataframe(TABELAS_GOLD["pagamentos"])

        if df_pag.empty:
            aviso_tabela_ausente(
                TABELAS_GOLD["pagamentos"],
                ["forma_pagamento", "valor", "parcelas"]
            )
        else:
            col_forma = primeira_coluna(df_pag, ["forma_pagamento", "payment_type", "tipo_pagamento"])
            col_valor = primeira_coluna(df_pag, ["valor", "valor_total", "receita"])
            col_parcelas = primeira_coluna(df_pag, ["parcelas", "payment_installments", "qtd_parcelas"])

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if col_forma and col_valor:
                    fig = px.pie(df_pag, names=col_forma, values=col_valor, title="Distribuição por Forma de Pagamento")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Colunas de forma de pagamento/valor não encontradas.")
            with col_p2:
                if col_parcelas:
                    fig = px.histogram(df_pag, x=col_parcelas, title="Distribuição de Parcelamento")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(df_pag, use_container_width=True)

    # --------------------------------------------------------------------------
    # ABA 6: CLUSTERIZAÇÃO & ML
    # --------------------------------------------------------------------------
    with tab_clusterizacao:
        st.subheader("🤖 Segmentação de Clientes via Machine Learning")

        if user_role in ["Admin", "Editor"]:
            df_clu = buscar_dataframe(TABELAS_GOLD["clusterizacao"])

            if df_clu.empty:
                aviso_tabela_ausente(
                    TABELAS_GOLD["clusterizacao"],
                    ["cluster", "recencia", "frequencia", "valor"]
                )
            else:
                col_cluster = primeira_coluna(df_clu, ["cluster", "segmento", "grupo_rfm"])
                if col_cluster:
                    contagem = df_clu[col_cluster].value_counts().reset_index()
                    contagem.columns = [col_cluster, "clientes"]
                    fig = px.bar(contagem, x=col_cluster, y="clientes", title="Clientes por Cluster")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(df_clu, use_container_width=True)
        else:
            st.warning("Seu perfil (Viewer) tem acesso limitado aos insights pré-calculados dos clusters.")

    # --------------------------------------------------------------------------
    # ABA 7: DADOS BRUTOS & FILTROS
    # --------------------------------------------------------------------------
    with tab_dados_brutos:
        st.subheader("📋 Consulta de Dados Brutos & Filtros Avançados")

        df_geral = buscar_dataframe(TABELAS_GOLD["dados_brutos"])

        if not df_geral.empty:
            st.dataframe(df_geral, use_container_width=True)
        else:
            aviso_tabela_ausente(TABELAS_GOLD["dados_brutos"], ["(qualquer coluna da sua tabela gold)"])
