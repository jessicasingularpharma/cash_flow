INSERT INTO cashflow_financeiro.dim_fornecedor (FornecedorID, Nome_Fornec)
SELECT "Fornecedor" , "Nome Fornece"
FROM apagar
ON CONFLICT (FornecedorID) DO NOTHING;

INSERT INTO cashflow_financeiro.dim_cliente (ClienteID, Nome_Cliente)
SELECT CAST("Cliente" AS BIGINT), "Nome Cliente"
FROM areceber
ON CONFLICT (ClienteID) DO NOTHING;

--delete do WWFTJ1	1	MB DISTRIBUIDORA
DELETE FROM areceber
WHERE "Cliente" !~ '^[0-9]+$';

-- Inserindo dados de loja 
INSERT INTO cashflow_financeiro.dim_loja (lojaid, descricao)
SELECT CAST("Loja" AS BIGINT), 'Descrição Padrão'
FROM areceber
ON CONFLICT (lojaid) DO NOTHING;
---insert natureza----
INSERT INTO cashflow_financeiro.dim_natureza (naturezaid, descricao)
SELECT CAST("Natureza" AS BIGINT), 'Descrição Padrão'
FROM areceber
ON CONFLICT (naturezaid) DO NOTHING;

---insert tabela de fato_apagar---
INSERT INTO cashflow_financeiro.fato_apagar (no_titulo, parcela, tipo, fornecedoriD, valor, data_emissao, data_vencimento, data_vencimento_real)
SELECT 
  "No. Titulo", 
  "Parcela", 
  "Tipo", 
  "Fornecedor", 
  CAST(REPLACE(REPLACE("Vlr.Titulo", '.', ''), ',', '.') AS DOUBLE PRECISION), 
  TO_DATE("DT Emissao", 'DD-MM-YYYY'), 
  TO_DATE("Vencimento", 'DD-MM-YYYY'), 
  TO_DATE("Vencto Real", 'DD-MM-YYYY')
FROM apagar;

---- permitindo que a coluan parcela tenha valores nulo---
ALTER TABLE cashflow_financeiro.fato_apagar
ALTER COLUMN parcela DROP NOT NULL;
---removendo chave primaria de parcela---
ALTER TABLE cashflow_financeiro.fato_apagar
DROP CONSTRAINT fato_apagar_pkey;

---adicionando outras chaves primarias---
ALTER TABLE cashflow_financeiro.fato_apagar
ADD PRIMARY KEY (no_titulo, fornecedoriD, data_vencimento_real);

---- inserir dados na tabela fato_areceber----
INSERT INTO cashflow_financeiro.fato_areceber (no_titulo, parcela, tipo, naturezaid, clienteid, lojaid, valor, data_emissao, data_vencimento, data_vencimento_real)
SELECT 
  "No. Titulo", 
  "Parcela", 
  "Tipo", 
  "Natureza", 
  CAST("Cliente" AS BIGINT), 
  NULL, 
  CAST(REPLACE(REPLACE("Vlr.Titulo", '.', ''), ',', '.') AS DOUBLE PRECISION), 
  TO_DATE("DT Emissao", 'DD-MM-YYYY'), 
  TO_DATE("Vencimento", 'DD-MM-YYYY'), 
  TO_DATE("Vencto real", 'DD-MM-YYYY')
FROM public."areceber"
ON CONFLICT (no_titulo, parcela) DO NOTHING;
-- inserindo restricao de unicidade--
ALTER TABLE cashflow_financeiro.fato_areceber
ADD CONSTRAINT fato_areceber_unique UNIQUE (no_titulo, parcela);

--permitir valores nulo na coluna parcelas--
ALTER TABLE cashflow_financeiro.fato_areceber
ALTER COLUMN parcela DROP NOT NULL;
---remover chave primaria da coluna parcela---
ALTER TABLE cashflow_financeiro.fato_areceber
DROP CONSTRAINT fato_areceber_pkey;
--remover restricoes de nao-nulo--
ALTER TABLE cashflow_financeiro.fato_areceber
ALTER COLUMN parcela DROP NOT NULL;


INSERT INTO cashflow_financeiro.dim_cliente (ClienteID, Nome_Cliente)
SELECT CAST("Cliente" AS BIGINT), "Nome Cliente"
FROM areceber
ON CONFLICT (ClienteID) DO NOTHING;

