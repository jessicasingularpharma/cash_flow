import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, date

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

    def gerar_graficos(self):
        # Combinar dados para visualização geral
        self.df_pagar['Categoria'] = 'A Pagar'
        self.df_receber['Categoria'] = 'A Receber'
        df_combined = pd.concat([self.df_pagar, self.df_receber], ignore_index=True)

        # Gráfico de barras combinado
        fig = px.bar(
            df_combined,
            x='DT Emissao',
            y='Vlr.Titulo',
            color='Categoria',
            barmode='group',
            title="Valores a Receber e a Pagar",
            labels={'Vlr.Titulo': 'Valor (R$)', 'DT Emissao': 'Data', 'Categoria': 'Categoria'},
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    def calcular_fluxo(self):
        # Cálculo do saldo diário com base em A Pagar e A Receber
        self.df_pagar['Vlr.Titulo'] = self.df_pagar['Vlr.Titulo'].astype(float)
        self.df_receber['Vlr.Titulo'] = self.df_receber['Vlr.Titulo'].astype(float)

        total_pagar = self.df_pagar['Vlr.Titulo'].sum()
        total_receber = self.df_receber['Vlr.Titulo'].sum()

        # Criação de um DataFrame para saldos
        datas = pd.date_range(start=self.df_pagar['Vencimento'].min(), end=self.df_receber['Vencimento'].max())
        df_saldo = pd.DataFrame(datas, columns=['Data'])
        df_saldo['Saldo'] = self.saldo_inicial + total_receber - total_pagar

        # Certificar que ambas as colunas para o merge são do tipo datetime.date
        self.df_pagar['DT Emissao'] = pd.to_datetime(self.df_pagar['DT Emissao']).dt.date
        self.df_receber['DT Emissao'] = pd.to_datetime(self.df_receber['DT Emissao']).dt.date
        df_saldo['Data'] = df_saldo['Data'].dt.date

        # Fazer o merge usando apenas a data
        self.df_pagar = self.df_pagar.merge(df_saldo, how='right', left_on='DT Emissao', right_on='Data', suffixes=('', '_saldo'))
        self.df_receber = self.df_receber.merge(df_saldo, how='right', left_on='DT Emissao', right_on='Data', suffixes=('', '_saldo'))

    def mostrar_dados(self):
        # Exibir total a pagar, a receber e saldo final
        total_receber = self.df_receber['Vlr.Titulo'].sum()
        total_pagar = self.df_pagar['Vlr.Titulo'].sum()
        saldo_final = self.saldo_inicial + total_receber - total_pagar

        col1, col2, col3 = st.columns(3)
        col1.metric("Total a Receber", f"R$ {total_receber:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Total a Pagar", f"R$ {total_pagar:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Saldo Final", f"R$ {saldo_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("### Detalhamento das Contas a Pagar")
        st.dataframe(self.df_pagar[['No. Titulo', 'Parcela', 'Tipo', 'Natureza', 'Fornecedor', 'Nome Fornece', 'Vlr.Titulo', 'DT Emissao', 'Vencimento', 'Vencto Real']])

        st.markdown("### Detalhamento das Contas a Receber")
        st.dataframe(self.df_receber[['No. Titulo', 'Parcela', 'Tipo', 'Natureza', 'Cliente', 'Loja', 'Nome Cliente', 'Vlr.Titulo', 'DT Emissao', 'Vencimento', 'Vencto Real']])

    def preparar_dados(self, saldo_inicial):
        self.saldo_inicial = saldo_inicial

        dados_pagar = [
            (26947, None, 'NF', '201006', '120', 'MARC ETIQUETAS', 525, '08/10/2024', '05/11/2024', '05/11/2024'),
            (26967, None, 'NF', '201006', '120', 'MARC ETIQUETAS', 973.9, '16/10/2024', '14/11/2024', '14/11/2024'),
            (1707550, None, 'NF', '203023', '6017', 'MODULAR TRANSPORTES', 865.86, '02/10/2024', '28/10/2024', '28/10/2024'),
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

        # Converter colunas para datetime
        self.df_pagar['DT Emissao'] = pd.to_datetime(self.df_pagar['DT Emissao'], dayfirst=True)
        self.df_pagar['Vencimento'] = pd.to_datetime(self.df_pagar['Vencimento'], dayfirst=True)
        self.df_pagar['Vencto Real'] = pd.to_datetime(self.df_pagar['Vencto Real'], dayfirst=True)

        self.df_receber['DT Emissao'] = pd.to_datetime(self.df_receber['DT Emissao'], dayfirst=True)
        self.df_receber['Vencimento'] = pd.to_datetime(self.df_receber['Vencimento'], dayfirst=True)
        self.df_receber['Vencto Real'] = pd.to_datetime(self.df_receber['Vencto Real'], dayfirst=True)

def main():
    st.set_page_config(page_title="Dashboard de Fluxo de Caixa", layout="wide")
    st.title("Dashboard de Fluxo de Caixa 📊")
    st.markdown("Acompanhamento de entradas e saídas financeiras.")

    fluxo_caixa = FluxoDeCaixa()

    st.sidebar.header("Configurações do Fluxo de Caixa")
    saldo_inicial_input = st.sidebar.text_input("Saldo inicial em conta bancária (ex: R$ 195.584,85):")
    saldo_inicial = fluxo_caixa.converter_para_float(saldo_inicial_input)

    if saldo_inicial is None:
        st.sidebar.error("Por favor, insira um valor válido para o saldo inicial. Ex: R$ 195.584,85")
    else:
        fluxo_caixa.preparar_dados(saldo_inicial)

        with st.container():
            st.markdown("## Visão Geral")
            fluxo_caixa.mostrar_dados()

        st.markdown("---")

        with st.container():
            st.markdown("## Análises Visuais")
            fluxo_caixa.calcular_fluxo()
            fluxo_caixa.gerar_graficos()

if __name__ == "__main__":
    main()