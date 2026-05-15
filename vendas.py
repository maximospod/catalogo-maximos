import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os
from zoneinfo import ZoneInfo   # ← Esta linha estava faltando

st.set_page_config(page_title="Maximos Pods", layout="wide", initial_sidebar_state="expanded")

# ====================== GITHUB ======================
GITHUB_USER = "castorsevn"
REPO_NAME = "maximos-pods-vendas"

LOGO_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/logo.jfif"
BANNER_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/banner.jfif"

# ====================== CABEÇALHO ======================
col_logo, col_titulo = st.columns([1.2, 5])

with col_logo:
    try:
        st.image(LOGO_URL, width=130)
    except:
        st.markdown("**MAXIMOS**")

with col_titulo:
    st.markdown("""
        <h1 style='margin: 0; color: #FF4B4B;'>MAXIMOS PODS</h1>
        <p style='color: #AAAAAA; margin-top: 5px;'>Sistema Profissional de Vendas</p>
    """, unsafe_allow_html=True)

try:
    st.image(BANNER_URL, use_column_width=True)
except:
    pass

st.markdown("---")

# ====================== DADOS ======================
ARQUIVO = "vendas_maximos_pods.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO):
        df = pd.read_csv(ARQUIVO)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    else:
        df = pd.DataFrame(columns=['Data', 'Cliente', 'WhatsApp', 'Produto', 'Valor_Bruto', 
                                 'Custo', 'Valor_Liquido', 'Forma_Pagamento', 'Status', 'Observacao'])
        df.to_csv(ARQUIVO, index=False)
        return df

def salvar_dados(df):
    df_copy = df.copy()
    df_copy['Data'] = df_copy['Data'].dt.strftime('%Y-%m-%d')
    df_copy.to_csv(ARQUIVO, index=False)

df = carregar_dados()

# Filtro
st.sidebar.markdown("### 📅 Filtro por Período")
data_inicio = st.sidebar.date_input("Data Inicial", datetime.today() - timedelta(days=30))
data_fim = st.sidebar.date_input("Data Final", datetime.today())

if not df.empty:
    mask = (df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)
    df_filtrado = df[mask].copy()
else:
    df_filtrado = df

aba = st.sidebar.selectbox("Menu", ["Nova Venda", "Dashboard", "Clientes", "Histórico Completo"])

# ====================== PÁGINAS ======================
if aba == "Nova Venda":
    st.subheader("📌 Nova Venda")
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", datetime.today())
        cliente = st.text_input("Nome do Cliente *")
        whatsapp = st.text_input("WhatsApp")
        produto = st.text_input("Produto / Serviço *")
    
    with col2:
        valor_bruto = st.number_input("Valor Bruto (R$)", min_value=0.0, format="%.2f")
        custo = st.number_input("Custo (R$)", min_value=0.0, format="%.2f")
        forma = st.selectbox("Forma de Pagamento", ["Pix", "Cartão", "Boleto", "Dinheiro", "Outro"])
        status = st.selectbox("Status", ["Pago", "Pendente", "Reembolsado"])
    
    obs = st.text_area("Observação")
    
    if st.button("💾 Salvar Venda", type="primary", use_container_width=True):
        if cliente and produto and valor_bruto > 0:
            nova = {
                'Data': data.strftime('%Y-%m-%d'),
                'Cliente': cliente,
                'WhatsApp': whatsapp,
                'Produto': produto,
                'Valor_Bruto': valor_bruto,
                'Custo': custo,
                'Valor_Liquido': round(valor_bruto - custo, 2),
                'Forma_Pagamento': forma,
                'Status': status,
                'Observacao': obs
            }
            df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
            salvar_dados(df)
            st.success("✅ Venda salva com sucesso!")
            st.rerun()
        else:
            st.error("Preencha os campos obrigatórios")

elif aba == "Dashboard":
    st.subheader("📊 Dashboard")
    if not df_filtrado.empty:
        fat = df_filtrado['Valor_Bruto'].sum()
        lucro = df_filtrado['Valor_Liquido'].sum()
        qtd = len(df_filtrado)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Vendas", f"{qtd}")
        col2.metric("Faturamento", f"R$ {fat:,.2f}")
        col3.metric("Lucro", f"R$ {lucro:,.2f}")
        
        st.bar_chart(df_filtrado.groupby(df_filtrado['Data'].dt.date)['Valor_Liquido'].sum())
    else:
        st.info("Nenhuma venda no período.")

elif aba == "Clientes":
    st.subheader("👥 Clientes")
    if not df_filtrado.empty:
        clientes = df_filtrado.groupby('Cliente').agg({'Valor_Liquido':'sum', 'Data':'count'}).reset_index()
        clientes.columns = ['Cliente', 'Total Gasto', 'Compras']
        st.dataframe(clientes.sort_values('Total Gasto', ascending=False), use_container_width=True)

else:
    st.subheader("📋 Histórico Completo")
    if not df_filtrado.empty:
        st.dataframe(df_filtrado.sort_values('Data', ascending=False), use_container_width=True)

# ====================== HORÁRIO DE BRASÍLIA ======================
st.markdown("---")

clock_placeholder = st.empty()

# Atualiza o relógio
agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
hora_brasilia = agora.strftime("%H:%M:%S")

clock_placeholder.markdown(f"""
    <div style='text-align: center; background-color: #1E1E2E; padding: 20px; border-radius: 12px; margin: 10px 0;'>
        <p style='margin:0; color:#AAAAAA; font-size: 1.1rem;'>🕒 Horário Atual de Brasília</p>
        <p style='font-size: 2.8rem; font-weight: bold; color: #00FF88; margin: 8px 0 0 0; font-family: Courier New;'>
            {hora_brasilia}
        </p>
    </div>
""", unsafe_allow_html=True)

st.caption("✅ Dados salvos automaticamente em tempo real | Maximos Pods © 2026")