--- Qual a previsao de pagamentos para Novembro?--
SELECT SUM(valor) AS Total_Pagar_Novembro
FROM cashflow_financeiro.fato_apagar
WHERE EXTRACT(MONTH FROM data_vencimento) = 11
AND EXTRACT(YEAR FROM data_vencimento) = EXTRACT(YEAR FROM CURRENT_DATE);

--- Qual o total a receber em Outubro?---
SELECT SUM(valor) AS Total_Receber_Outubro
FROM cashflow_financeiro.fato_areceber
WHERE EXTRACT(MONTH FROM data_vencimento) = 10
AND EXTRACT(YEAR FROM data_vencimento) = EXTRACT(YEAR FROM CURRENT_DATE);
---Quanto pagamos para cada fornecedor?---
SELECT f.nome_fornec, SUM(fa.valor) AS Total_Pago
FROM cashflow_financeiro.fato_apagar fa
JOIN cashflow_financeiro.dim_fornecedor f ON fa.fornecedorID = f.fornecedorID
GROUP BY f.nome_fornec;
---Quanto recebemos de cada cliente?---
SELECT c.nome_cliente, SUM(fr.valor) AS Total_Recebido
FROM cashflow_financeiro.fato_areceber fr
JOIN cashflow_financeiro.dim_cliente c ON fr.clienteID = c.clienteID
GROUP BY c.nome_cliente;
--