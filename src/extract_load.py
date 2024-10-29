import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

class FluxoDeCaixa:
    def __init__(self):
        self.saldo_inicial = 0.0
        self.df_pagar = pd.DataFrame()
        self.df_receber = pd.DataFrame()

    @staticmethod
    def converter_para_float(valor):
        try:
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".")
            return float(valor)
        except (ValueError, AttributeError):
            return None

    def gerar_graficos(self, start_date, end_date):
        self.df_pagar['Categoria'] = 'A Pagar'
        self.df_receber['Categoria'] = 'A Receber'
        df_combined = pd.concat([self.df_pagar, self.df_receber], ignore_index=True)
        
        # Filtrar dados pelo intervalo de datas
        df_combined = df_combined[(df_combined['DT Emissao'] >= start_date) & (df_combined['DT Emissao'] <= end_date)]
        df_combined['DT Emissao'] = pd.to_datetime(df_combined['DT Emissao'], errors='coerce')
        df_combined = df_combined.dropna(subset=['DT Emissao'])

        # Agrupar por semana para gráfico
        df_combined['Semana'] = df_combined['DT Emissao'].dt.to_period('W').apply(lambda r: r.start_time)
        df_grouped = df_combined.groupby(['Semana', 'Categoria']).agg({'Vlr.Titulo': 'sum'}).reset_index()

        # Gráfico de barras
        fig = px.bar(
            df_grouped,
            x='Semana',
            y='Vlr.Titulo',
            color='Categoria',
            barmode='group',
            title="Valores a Receber e a Pagar por Semana",
            labels={'Vlr.Titulo': 'Valor (R$)', 'Semana': 'Semana', 'Categoria': 'Categoria'},
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    def calcular_fluxo(self):
        # Configuração do saldo diário e merge de data
        self.df_pagar['DT Emissao'] = pd.to_datetime(self.df_pagar['DT Emissao']).dt.date
        self.df_receber['DT Emissao'] = pd.to_datetime(self.df_receber['DT Emissao']).dt.date

    def mostrar_dados(self):
        total_receber = self.df_receber['Vlr.Titulo'].sum()
        total_pagar = self.df_pagar['Vlr.Titulo'].sum()
        saldo_final = self.saldo_inicial + total_receber - total_pagar

        col1, col2, col3 = st.columns(3)
        col1.metric("Total a Receber", f"R$ {total_receber:,.2f}")
        col2.metric("Total a Pagar", f"R$ {total_pagar:,.2f}")
        col3.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    def preparar_dados(self, saldo_inicial):
        self.saldo_inicial = saldo_inicial

        dados_pagar = [
            (26947, None, 'NF', '201006', '120', 'MARC ETIQUETAS', 525, '08/10/2024', '05/11/2024', '05/11/2024'),
            (26967, None, 'NF', '201006', '120', 'MARC ETIQUETAS', 973.9, '16/10/2024', '14/11/2024', '14/11/2024'),
        ]
        dados_receber = [
            (13246, None, 'NF', '101001', '5057', '1', 'SINGULAR PHARMA FEIR', 1089.27, '25/09/2024', '25/10/2024', '25/10/2024'),
            (13252, None, 'NF', '101001', '6186', '1', 'FIOLASER SSA SHOPING', 237.3, '30/09/2024', '28/10/2024', '28/10/2024'),
        ]

        self.df_pagar = pd.DataFrame(dados_pagar, columns=[
            'No. Titulo', 'Parcela', 'Tipo', 'Natureza', 'Fornecedor', 'Nome Fornece', 'Vlr.Titulo', 'DT Emissao', 'Vencimento', 'Vencto Real'
        ])
        self.df_receber = pd.DataFrame(dados_receber, columns=[
            'No. Titulo', 'Parcela', 'Tipo', 'Natureza', 'Cliente', 'Loja', 'Nome Cliente', 'Vlr.Titulo', 'DT Emissao', 'Vencimento', 'Vencto Real'
        ])
        
        # Converter para datetime
        self.df_pagar['DT Emissao'] = pd.to_datetime(self.df_pagar['DT Emissao'], dayfirst=True)
        self.df_receber['DT Emissao'] = pd.to_datetime(self.df_receber['DT Emissao'], dayfirst=True)

def main():
    st.set_page_config(page_title="Dashboard de Fluxo de Caixa", layout="wide")
    st.title("Dashboard de Fluxo de Caixa 📊")

    fluxo_caixa = FluxoDeCaixa()
    
    st.sidebar.header("Configurações do Fluxo de Caixa")
    saldo_inicial_input = st.sidebar.text_input("Saldo inicial em conta bancária (ex: R$ 195.584,85):")
    saldo_inicial = fluxo_caixa.converter_para_float(saldo_inicial_input)
    
    # Condição para exibir o filtro de datas somente após o saldo inicial
    if saldo_inicial is not None:
        fluxo_caixa.preparar_dados(saldo_inicial)
        st.sidebar.markdown("Selecione o intervalo de datas para análise:")

        # Exibir data inicial e final juntas
        start_date, end_date = st.sidebar.date_input(
            "Intervalo de Data", 
            value=(date(2024, 9, 1), date(2024, 10, 31))
        )

        # Exibir dados e gráficos somente após o intervalo de datas ser selecionado
        with st.container():
            st.markdown("## Visão Geral")
            fluxo_caixa.mostrar_dados()

        st.markdown("---")

        with st.container():
            st.markdown("## Análises Visuais")
            fluxo_caixa.calcular_fluxo()
            fluxo_caixa.gerar_graficos(start_date, end_date)

if __name__ == "__main__":
    main()