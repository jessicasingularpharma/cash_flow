import pandas as pd
from sqlalchemy import create_engine

def extract_data(apagar_path, areceber_path):
    """
    Extrai os dados de arquivos CSV para DataFrames.
    """
    df_apagar = pd.read_csv(apagar_path, delimiter=';', decimal=',')
    df_areceber = pd.read_csv(areceber_path, delimiter=';', decimal=',')
    return df_apagar, df_areceber

def load_to_database(df, table_name, db_engine):
    """
    Carrega os dados transformados em uma tabela do banco de dados.
    """
    try:
        df.to_sql(table_name, db_engine, if_exists='replace', index=False)
        print(f"Dados carregados com sucesso na tabela '{table_name}'")
    except Exception as e:
        print(f"Erro ao carregar os dados na tabela '{table_name}': {e}")

def run_etl(apagar_path, areceber_path, db_url):
    """
    Executa o pipeline ETL completo com carregamento em duas tabelas.
    """
    # Extração
    df_apagar, df_areceber = extract_data(apagar_path, areceber_path)
    
    # Conexão com o banco de dados
    db_engine = create_engine(db_url)
    
    # Carga dos dados em tabelas separadas
    load_to_database(df_apagar, 'apagar', db_engine)
    load_to_database(df_areceber, 'areceber', db_engine)

# Parâmetros do script
apagar_path = r'C:\Users\Oem\flow_cash_martinsbrasil\dados\apagar.csv'
areceber_path = r'C:\Users\Oem\flow_cash_martinsbrasil\dados\areceber.csv'
db_url = 'postgresql://postgres:1234@localhost:5432/cash_flow'

# Executa o ETL
run_etl(apagar_path, areceber_path, db_url)
