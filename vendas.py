import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import os
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Maximos Pods", layout="wide", initial_sidebar_state="expanded")

# ====================== CONFIGURAÇÃO ======================
GITHUB_USER = "castorsevn"
REPO_NAME = "maximos-pods-vendas"

LOGO_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/logo.jfif"
BANNER_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/banner.jfif"

DB_FILE = "vendas_maximos_pods.db"

# ====================== BANCO DE DADOS ======================
def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Data TEXT,
            Cliente TEXT,
            WhatsApp TEXT,
            Produto TEXT,
            Valor_Bruto REAL,
            Custo REAL,
            Valor_Liquido REAL,
            Forma_Pagamento TEXT,
            Status TEXT,
            Observacao TEXT,
            Data_Criacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def salvar_venda(venda, venda_id=None):
    conn = get_connection()
    if venda_id:  # Edição
        conn.execute('''
            UPDATE vendas SET Data=?, Cliente=?, WhatsApp=?, Produto=?, Valor_Bruto=?,
            Custo=?, Valor_Liquido=?, Forma_Pagamento=?, Status=?, Observacao=?
            WHERE id=?
        ''', (venda['Data'], venda['Cliente'], venda['WhatsApp'], venda['Produto'],
              venda['Valor_Bruto'], venda['Custo'], venda['Valor_Liquido'],
              venda['Forma_Pagamento'], venda['Status'], venda['Observacao'], venda_id))
    else:
        conn.execute('''
            INSERT INTO vendas (Data, Cliente, WhatsApp, Produto, Valor_Bruto, Custo, 
            Valor_Liquido, Forma_Pagamento, Status, Observacao, Data_Criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (venda['Data'], venda['Cliente'], venda['WhatsApp'], venda['Produto'],
              venda['Valor_Bruto'], venda['Custo'], venda['Valor_Liquido'],
              venda['Forma_Pagamento'], venda['Status'], venda['Observacao'],
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def carregar_vendas():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM vendas ORDER BY Data DESC, id DESC", conn)
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
    conn.close()
    return df

def excluir_venda(venda_id):
    conn = get_connection()
    conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
    conn.commit()
    conn.close()

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
    st.image(BANNER_URL, use_container_width=True)   # ← Corrigido aqui
except:
    pass

st.markdown("---")

df = carregar_vendas()

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

# ====================== NOVA VENDA / EDIÇÃO ======================
if aba == "Nova Venda":
    st.subheader("📌 Nova Venda" if 'edit_id' not in st.session_state else "✏️ Editar Venda")

    edit_id = st.session_state.get('edit_id')
    edit_data = df[df['id'] == edit_id].iloc[0] if edit_id and not df.empty else None

    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", value=pd.to_datetime(edit_data['Data']) if edit_data is not None else datetime.today())
        cliente = st.text_input("Nome do Cliente *", value=edit_data['Cliente'] if edit_data is not None else "")
        whatsapp = st.text_input("WhatsApp", value=edit_data.get('WhatsApp', '') if edit_data is not None else "")
        produto = st.text_input("Produto / Serviço *", value=edit_data['Produto'] if edit_data is not None else "")
    
    with col2:
        valor_bruto = st.number_input("Valor Bruto (R$)", min_value=0.0, format="%.2f", 
                                     value=float(edit_data['Valor_Bruto']) if edit_data is not None else 0.0)
        custo = st.number_input("Custo (R$)", min_value=0.0, format="%.2f", 
                               value=float(edit_data['Custo']) if edit_data is not None else 0.0)
        forma = st.selectbox("Forma de Pagamento", ["Pix", "Cartão", "Boleto", "Dinheiro", "Outro"], 
                            index=0 if edit_data is None else ["Pix", "Cartão", "Boleto", "Dinheiro", "Outro"].index(edit_data['Forma_Pagamento']))
        status = st.selectbox("Status", ["Pago", "Pendente", "Reembolsado"], 
                             index=0 if edit_data is None else ["Pago", "Pendente", "Reembolsado"].index(edit_data['Status']))
    
    obs = st.text_area("Observação", value=edit_data.get('Observacao', '') if edit_data is not None else "")

    if st.button("💾 Salvar Venda" if not edit_id else "💾 Atualizar Venda", type="primary", use_container_width=True):
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
            salvar_venda(nova, edit_id)
            st.success("✅ Sucesso!" if not edit_id else "✅ Venda atualizada!")
            if edit_id:
                del st.session_state.edit_id
            st.rerun()

# ====================== DASHBOARD, CLIENTES, HISTÓRICO (mantido) ======================
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

elif aba == "Clientes":
    st.subheader("👥 Clientes")
    if not df_filtrado.empty:
        clientes = df_filtrado.groupby('Cliente').agg({'Valor_Liquido':'sum', 'Data':'count'}).reset_index()
        clientes.columns = ['Cliente', 'Total Gasto', 'Compras']
        st.dataframe(clientes.sort_values('Total Gasto', ascending=False), use_container_width=True)

else:  # Histórico
    st.subheader("📋 Histórico Completo")
    if not df_filtrado.empty:
        for _, row in df_filtrado.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 1.5, 1.5])
            with col1:
                st.write(f"**{row['Cliente']}** — {row['Produto']}")
                st.caption(f"{row['Data'].strftime('%d/%m/%Y')} | {row['Forma_Pagamento']}")
            with col2:
                st.metric("", f"R$ {row['Valor_Bruto']:,.2f}")
            with col3:
                if st.button("✏️ Editar", key=f"e{row['id']}"):
                    st.session_state.edit_id = row['id']
                    st.switch_page("vendas.py")
            with col4:
                if st.button("🗑️", key=f"d{row['id']}"):
                    excluir_venda(row['id'])
                    st.success("Venda excluída!")
                    st.rerun()
            st.divider()

# ====================== HORÁRIO ======================
st.markdown("---")
agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
st.markdown(f"""
    <div style='text-align: center; background-color: #1E1E2E; padding: 20px; border-radius: 12px;'>
        <p style='margin:0; color:#AAAAAA;'>🕒 Horário de Brasília</p>
        <p style='font-size: 2.8rem; font-weight: bold; color: #00FF88; margin:5px 0 0 0;'>
            {agora.strftime("%H:%M:%S")}
        </p>
    </div>
""", unsafe_allow_html=True)

st.caption("✅ Banco SQL + Edição/Exclusão | Maximos Pods © 2026")