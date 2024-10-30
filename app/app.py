import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Carregar variáveis do arquivo .env
load_dotenv()

# Variáveis de ambiente
usuario = os.getenv("DB_USER")
senha = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
porta = os.getenv("DB_PORT")
db = os.getenv("DB_NAME")

# Criação da engine de conexão
engine = create_engine(f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{db}', connect_args={"options": "-c client_encoding=utf8"})

# Carregar o arquivo de configuração
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Inicializar o autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Autenticação
st.title("Sistema de Autenticação")
result = authenticator.login(location="main")

# Verificar o resultado da autenticação
if result is not None:
    name, authentication_status, username = result
    if authentication_status:
        st.success(f"Bem-vindo, {name}!")
        
        # Classe FluxoDeCaixa
        class FluxoDeCaixa:
            def __init__(self, engine):
                self.saldo_inicial = 0.0
                self.df_pagar = pd.DataFrame()
                self.df_receber = pd.DataFrame()
                self.engine = engine

            @staticmethod
            def converter_para_float(valor):
                try:
                    valor = valor.replace("R$", "").replace(".", "").replace(",", ".")
                    return float(valor)
                except (ValueError, AttributeError):
                    return None

            def carregar_dados(self, start_date, end_date):
                query_template = """
                SELECT 
                    f.no_titulo AS "No_Titulo", 
                    f.parcela AS "Parcela", 
                    f.tipo AS "Tipo", 
                    {entidade} AS "Entidade",
                    f.valor AS "Vlr_Titulo", 
                    f.data_emissao::date AS "Data_Emissao", 
                    f.data_vencimento AS "Data_Vencimento", 
                    f.data_vencimento_real AS "Data_Vencimento_Real"
                FROM 
                    {tabela} AS f
                LEFT JOIN 
                    {dimensao} AS d ON f.{dim_id} = d.{dim_id}
                WHERE 
                    f.data_emissao BETWEEN '{start_date}' AND '{end_date}'
                """
                query_pagar = query_template.format(
                    entidade="d.nome_fornec AS 'Fornecedor'",
                    tabela="cashflow_financeiro.fato_apagar",
                    dimensao="cashflow_financeiro.dim_fornecedor",
                    dim_id="fornecedorID",
                    start_date=start_date,
                    end_date=end_date
                )
                query_receber = query_template.format(
                    entidade="c.nome_cliente AS 'Cliente'",
                    tabela="cashflow_financeiro.fato_areceber",
                    dimensao="cashflow_financeiro.dim_cliente",
                    dim_id="clienteID",
                    start_date=start_date,
                    end_date=end_date
                )
                # Carregar dados com uma conexão reutilizável
                with self.engine.connect() as conn:
                    self.df_pagar = pd.read_sql(query_pagar, conn)
                    self.df_receber = pd.read_sql(query_receber, conn)

                # Convertendo colunas de data
                self.df_pagar['Data_Emissao'] = pd.to_datetime(self.df_pagar['Data_Emissao'], errors='coerce')
                self.df_receber['Data_Emissao'] = pd.to_datetime(self.df_receber['Data_Emissao'], errors='coerce')

            def mostrar_dados(self):
                total_receber = self.df_receber['Vlr_Titulo'].sum()
                total_pagar = self.df_pagar['Vlr_Titulo'].sum()
                saldo_final = self.saldo_inicial + total_receber - total_pagar
                col1, col2, col3 = st.columns(3)
                col1.metric("Total a Receber", f"R$ {total_receber:,.2f}")
                col2.metric("Total a Pagar", f"R$ {total_pagar:,.2f}")
                col3.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
                st.write("### Dados de Contas a Pagar")
                st.dataframe(self.df_pagar)
                st.write("### Dados de Contas a Receber")
                st.dataframe(self.df_receber)

            def gerar_graficos(self, start_date, end_date):
                self.df_pagar['Categoria'] = 'A Pagar'
                self.df_receber['Categoria'] = 'A Receber'
                df_combined = pd.concat([self.df_pagar, self.df_receber], ignore_index=True)
                df_combined['Data_Emissao'] = pd.to_datetime(df_combined['Data_Emissao'])
                df_filtered = df_combined[(df_combined['Data_Emissao'] >= start_date) & (df_combined['Data_Emissao'] <= end_date)]
                df_grouped = df_filtered.groupby([df_filtered['Data_Emissao'].dt.to_period('W').apply(lambda r: r.start_time), 'Categoria']).agg({'Vlr_Titulo': 'sum'}).reset_index()
                fig_barras = px.bar(df_grouped, x='Data_Emissao', y='Vlr_Titulo', color='Categoria', barmode='group', template='plotly_white')
                fig_pizza = px.pie(df_combined, names='Categoria', values='Vlr_Titulo', template='plotly_white')
                st.plotly_chart(fig_barras, use_container_width=True)
                st.plotly_chart(fig_pizza, use_container_width=True)

        # Função principal
        def main():
            st.set_page_config(page_title="Dashboard de Fluxo de Caixa", layout="wide")
            st.title("Dashboard de Fluxo de Caixa")
            fluxo_caixa = FluxoDeCaixa(engine)
            
            # Input do saldo inicial
            saldo_inicial_input = st.sidebar.text_input("Saldo inicial em conta bancária (ex: R$ 195.584,85):")
            saldo_inicial = fluxo_caixa.converter_para_float(saldo_inicial_input)
            
            if saldo_inicial is not None:
                fluxo_caixa.saldo_inicial = saldo_inicial
                
                # Intervalo de datas
                start_date, end_date = st.sidebar.date_input("Intervalo de Data", (date(2024, 9, 1), date(2024, 10, 31)), key="intervalo")
                fluxo_caixa.carregar_dados(start_date, end_date)
                
                # Mostrando dados
                st.markdown("## Visão Geral")
                fluxo_caixa.mostrar_dados()
                st.markdown("---")
                st.markdown("## Análises Visuais")
                fluxo_caixa.gerar_graficos(start_date, end_date)

        main()

    else:
        st.error("Usuário ou senha incorretos")
else:
    st.warning("Por favor, insira seu nome de usuário e senha")
