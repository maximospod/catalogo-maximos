import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Maximos Pods", layout="wide")

# ====================== CONFIG ======================
GITHUB_USER = "castorsevn"
REPO_NAME = "maximos-pods-vendas"

LOGO_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/logo.jfif"
BANNER_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/banner.jfif"

DB_FILE = "vendas_maximos_pods.db"

# ====================== BANCO DE DADOS ======================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Data TEXT, Cliente TEXT, WhatsApp TEXT, Produto TEXT,
                    Valor_Bruto REAL, Custo REAL, Valor_Liquido REAL,
                    Forma_Pagamento TEXT, Status TEXT, Observacao TEXT)''')
    conn.commit()
    conn.close()

init_db()

def salvar_venda(venda):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""INSERT INTO vendas (Data, Cliente, WhatsApp, Produto, Valor_Bruto, Custo, 
                    Valor_Liquido, Forma_Pagamento, Status, Observacao) 
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                 (venda['Data'], venda['Cliente'], venda['WhatsApp'], venda['Produto'],
                  venda['Valor_Bruto'], venda['Custo'], venda['Valor_Liquido'],
                  venda['Forma_Pagamento'], venda['Status'], venda['Observacao']))
    conn.commit()
    conn.close()

def carregar_vendas():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC", conn)
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
    conn.close()
    return df

# ====================== INTERFACE ======================
col1, col2 = st.columns([1, 4])
with col1:
    try: st.image(LOGO_URL, width=120)
    except: pass
with col2:
    st.title("MAXIMOS PODS")

try: st.image(BANNER_URL, use_container_width=True)
except: pass

st.markdown("---")

df = carregar_vendas()

aba = st.sidebar.selectbox("Escolha a aba", ["Nova Venda", "Dashboard", "Clientes", "Histórico"])

st.sidebar.markdown("### 📅 Filtro")
data_inicio = st.sidebar.date_input("Data Inicial", datetime.today() - timedelta(days=30))
data_fim = st.sidebar.date_input("Data Final", datetime.today())

if not df.empty:
    mask = (df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)
    df_filtrado = df[mask].copy()
else:
    df_filtrado = pd.DataFrame()

# ====================== ABAS ======================
if aba == "Nova Venda":
    st.subheader("📌 Nova Venda")
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", datetime.today())
        cliente = st.text_input("Nome do Cliente *")
        whatsapp = st.text_input("WhatsApp")
        produto = st.text_input("Produto / Serviço *")
    with col2:
        valor = st.number_input("Valor Bruto (R$)", min_value=0.0, format="%.2f")
        custo = st.number_input("Custo (R$)", min_value=0.0, format="%.2f")
        forma = st.selectbox("Forma de Pagamento", ["Pix", "Cartão", "Boleto", "Dinheiro"])
        status = st.selectbox("Status", ["Pago", "Pendente", "Reembolsado"])
    
    obs = st.text_area("Observação")
    
    if st.button("💾 Salvar Venda", type="primary", use_container_width=True):
        if cliente and produto and valor > 0:
            nova = {
                'Data': data.strftime('%Y-%m-%d'),
                'Cliente': cliente,
                'WhatsApp': whatsapp,
                'Produto': produto,
                'Valor_Bruto': valor,
                'Custo': custo,
                'Valor_Liquido': round(valor - custo, 2),
                'Forma_Pagamento': forma,
                'Status': status,
                'Observacao': obs
            }
            salvar_venda(nova)
            st.success("✅ Venda salva com sucesso!")
            st.rerun()
        else:
            st.error("Preencha os campos obrigatórios")

elif aba == "Dashboard":
    st.subheader("📊 Dashboard")
    if not df_filtrado.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendas", len(df_filtrado))
        col2.metric("Faturamento", f"R$ {df_filtrado['Valor_Bruto'].sum():,.2f}")
        col3.metric("Lucro", f"R$ {df_filtrado['Valor_Liquido'].sum():,.2f}")
    else:
        st.info("Nenhuma venda no período")

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
            st.write(f"**{row['Cliente']}** - {row['Produto']} | R$ {row['Valor_Bruto']:.2f}")
            st.caption(f"{row['Data'].strftime('%d/%m/%Y')} | {row['Status']}")
            st.divider()
    else:
        st.info("Nenhuma venda encontrada")

st.caption("🕒 Horário de Brasília: " + datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M:%S"))