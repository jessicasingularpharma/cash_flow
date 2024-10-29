import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Obtenha as variáveis de ambiente
usuario = os.getenv("DB_USER")
senha = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
porta = os.getenv("DB_PORT")
db = os.getenv("DB_NAME")

# Crie a engine de conexão usando as variáveis de ambiente
engine = create_engine(f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{db}', connect_args={"options": "-c client_encoding=utf8"})

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
        query_pagar = f"""
        SELECT 
            f.no_titulo AS "No_Titulo", 
            f.parcela AS "Parcela", 
            f.tipo AS "Tipo", 
            d.nome_fornec AS "Fornecedor", 
            f.valor AS "Vlr_Titulo", 
            f.data_emissao::date AS "Data_Emissao", 
            f.data_vencimento AS "Data_Vencimento", 
            f.data_vencimento_real AS "Data_Vencimento_Real"
        FROM 
            cashflow_financeiro.fato_apagar AS f
        LEFT JOIN 
            cashflow_financeiro.dim_fornecedor AS d 
        ON 
            f.fornecedorID = d.fornecedorID
        WHERE 
            f.data_emissao BETWEEN '{start_date}' AND '{end_date}'
        """
        query_receber = f"""
        SELECT 
            f.no_titulo AS "No_Titulo", 
            f.parcela AS "Parcela", 
            f.tipo AS "Tipo", 
            c.nome_cliente AS "Cliente", 
            l.descricao AS "Loja", 
            n.descricao AS "Natureza", 
            f.valor AS "Vlr_Titulo", 
            f.data_emissao::date AS "Data_Emissao", 
            f.data_vencimento AS "Data_Vencimento", 
            f.data_vencimento_real AS "Data_Vencimento_Real"
        FROM 
            cashflow_financeiro.fato_areceber AS f
        LEFT JOIN 
            cashflow_financeiro.dim_cliente AS c 
        ON 
            f.clienteID = c.clienteID
        LEFT JOIN 
            cashflow_financeiro.dim_loja AS l 
        ON 
            f.lojaid = l.lojaid
        LEFT JOIN 
            cashflow_financeiro.dim_natureza AS n 
        ON 
            f.naturezaID = n.naturezaID
        WHERE 
            f.data_emissao BETWEEN '{start_date}' AND '{end_date}'
        """
        self.df_pagar = pd.read_sql(query_pagar, self.engine)
        self.df_receber = pd.read_sql(query_receber, self.engine)

        # Garantir que as colunas de data são datetime
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
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        self.df_pagar['Categoria'] = 'A Pagar'
        self.df_receber['Categoria'] = 'A Receber'
        df_combined = pd.concat([self.df_pagar, self.df_receber], ignore_index=True)

        df_combined = df_combined[(df_combined['Data_Emissao'] >= start_date) & (df_combined['Data_Emissao'] <= end_date)]
        df_combined = df_combined.dropna(subset=['Data_Emissao'])

        df_combined['Semana'] = df_combined['Data_Emissao'].dt.to_period('W').apply(lambda r: r.start_time)
        df_grouped = df_combined.groupby(['Semana', 'Categoria']).agg({'Vlr_Titulo': 'sum'}).reset_index()

        fig_barras = px.bar(
            df_grouped,
            x='Semana',
            y='Vlr_Titulo',
            color='Categoria',
            barmode='group',
            title="Valores a Receber e a Pagar por Semana",
            labels={'Vlr_Titulo': 'Valor (R$)', 'Semana': 'Semana', 'Categoria': 'Categoria'},
            template='plotly_white'
        )

        fig_linhas = px.line(
            df_combined,
            x='Data_Emissao',
            y='Vlr_Titulo',
            color='Categoria',
            title="Fluxo Cumulativo de Caixa por Data de Emissão",
            labels={'Vlr_Titulo': 'Valor (R$)', 'Data_Emissao': 'Data de Emissão'},
            template='plotly_white'
        )

        fig_pizza = px.pie(
            df_combined,
            names='Categoria',
            values='Vlr_Titulo',
            title="Distribuição de Valores a Receber e a Pagar",
            template='plotly_white'
        )

        # Gráfico de faixas: diferença acumulada entre contas a pagar e a receber
        df_combined['Saldo Acumulado'] = df_combined.apply(
            lambda row: row['Vlr_Titulo'] if row['Categoria'] == 'A Receber' else -row['Vlr_Titulo'], axis=1
        ).cumsum()

        fig_faixa = px.area(
            df_combined,
            x='Data_Emissao',
            y='Saldo Acumulado',
            title="Evolução do Saldo Acumulado ao Longo do Tempo",
            labels={'Saldo Acumulado': 'Saldo Acumulado (R$)', 'Data_Emissao': 'Data de Emissão'},
            template='plotly_white'
        )

        st.plotly_chart(fig_barras, use_container_width=True)
        st.plotly_chart(fig_linhas, use_container_width=True)
        st.plotly_chart(fig_pizza, use_container_width=True)
        st.plotly_chart(fig_faixa, use_container_width=True)

def main():
    st.set_page_config(page_title="Dashboard de Fluxo de Caixa", layout="wide")
    st.title("Dashboard de Fluxo de Caixa")

    fluxo_caixa = FluxoDeCaixa(engine)

    try:
        with engine.connect() as conn:
            st.success("Conexão bem-sucedida")
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")

    st.sidebar.header("Configurações do Fluxo de Caixa")
    saldo_inicial_input = st.sidebar.text_input("Saldo inicial em conta bancária (ex: R$ 195.584,85):")
    saldo_inicial = fluxo_caixa.converter_para_float(saldo_inicial_input)

    if saldo_inicial is not None:
        fluxo_caixa.saldo_inicial = saldo_inicial
        st.sidebar.markdown("Selecione o intervalo de datas para análise:")
        start_date, end_date = st.sidebar.date_input(
            "Intervalo de Data",
            value=(date(2024, 9, 1), date(2024, 10, 31)),
            key="intervalo"
        )

        fluxo_caixa.carregar_dados(start_date, end_date)

        with st.container():
            st.markdown("## Visão Geral")
            fluxo_caixa.mostrar_dados()

        st.markdown("---")

        with st.container():
            st.markdown("## Análises Visuais")
            fluxo_caixa.gerar_graficos(start_date, end_date)

if __name__ == "__main__":
    main()