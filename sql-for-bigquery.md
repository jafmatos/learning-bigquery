# 📊 Guia Completo: SQL para BigQuery focado em Ciência de Dados

> **Objetivo:** Dominar o GoogleSQL (dialeto do BigQuery) desde a modelagem de features até funções avançadas de janela e otimização de custos.

---

## 📑 Sumário

1. [O Dialeto GoogleSQL &amp; Notação de Tabelas](#1-o-dialeto-googlesql--notação-de-tabelas)
2. [Fundamentos &amp; Boas Práticas Inegociáveis](#2-fundamentos--boas-práticas-inegociáveis)
3. [Tratamento de Nulos &amp; Lógica Condicional](#3-tratamento-de-nulos--lógica-condicional)
4. [Agregações &amp; Agrupamentos](#4-agregações--agrupamentos)
5. [JOINs e Relacionamentos no BigQuery](#5-joins-e-relacionamentos-no-bigquery)
6. [CTEs (Common Table Expressions): O Padrão para Pipelines](#6-ctes-common-table-expressions-o-padrão-para-pipelines)
7. [Window Functions (Funções de Janela) - O Diferencial em Entrevistas](#7-window-functions-funções-de-janela---o-diferencial-em-entrevistas)
8. [Manipulação de Datas e Séries Temporais](#8-manipulação-de-datas-e-séries-temporais)
9. [Arrays, Structs e o Operador UNNEST()](#9-arrays-structs-e-o-operador-unnest)
10. [Otimização de Consultas &amp; Redução de Custos](#10-otimização-de-consultas--redução-de-custos)
11. [Projeto Prático Completo: Feature Store de E-commerce](#11-projeto-prático-completo-feature-store-de-e-commerce)

---

## 1. O Dialeto GoogleSQL & Notação de Tabelas

No BigQuery, a referência completa de qualquer tabela segue a convenção de três partes envolvida em **backticks** (crases):

$$
\text{`nome-do-projeto.nome_do_dataset.nome_da_tabela`}
$$

Exemplo:

```sql
SELECT id, age, gender 
FROM `bigquery-public-data.thelook_ecommerce.users`
LIMIT 10;
```

---

## 2. Fundamentos & Boas Práticas Inegociáveis

### ❌ O Pecado do `SELECT *`

O BigQuery é um banco de dados **colunar**. Se uma tabela tem 50 colunas e 100 milhões de linhas, e você só precisa de 3 colunas, fazer `SELECT *` obriga o BigQuery a ler as 50 colunas inteiras do disco, multiplicando o custo da consulta por mais de 15 vezes!

> ⚠️ **Mito comum:** "Se eu colocar `LIMIT 10`, a query fica mais barata?". **NÃO!** O `LIMIT` apenas corta a exibição no final; o BigQuery ainda escaneia todas as colunas solicitadas da tabela inteira. Para baratear de verdade uma exploração rápida, use **`TABLESAMPLE`** ou **filtros de partição** (detalhados na Seção 10).

```sql
-- ❌ Ruim (escaneia todas as colunas da tabela inteira):
SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders`;

--  Excelente (escaneia apenas os bytes das colunas selecionadas):
SELECT order_id, user_id, status, created_at 
FROM `bigquery-public-data.thelook_ecommerce.orders`;
```

---

## 3. Tratamento de Nulos & Lógica Condicional

Dados do mundo real vêm com campos vazios (`NULL`). Para modelos de Machine Learning, é essencial tratar nulos e criar variáveis binárias (*dummies/flags*) direto no SQL:

### 3.1. Tratamento com `COALESCE` e `IFNULL`

Substitui o valor nulo por um valor padrão:

```sql
SELECT 
    id,
    -- Se o estado for nulo, preenche com 'Nao Informado'
    COALESCE(state, 'Nao Informado') AS estado_tratado,
    -- Se o total for nulo, substitui por 0.0
    IFNULL(num_of_item, 0) AS total_itens
FROM `bigquery-public-data.thelook_ecommerce.orders`;
```

### 3.2. Lógica com `CASE WHEN`

Cria faixas etárias, categorias agregadas ou variáveis alvo (*target*):

```sql
SELECT 
    id,
    age,
    CASE 
        WHEN age < 25 THEN 'Jovem'
        WHEN age BETWEEN 25 AND 50 THEN 'Adulto'
        ELSE 'Senior'
    END AS faixa_etaria,
    CASE 
        WHEN status = 'Returned' THEN 1 
        ELSE 0 
    END AS flag_devolveu_pedido
FROM `bigquery-public-data.thelook_ecommerce.order_items`;
```

---

## 4. Agregações & Agrupamentos

São fundamentais para resumir o comportamento transacional de um usuário (ex: quantas compras ele fez, valor total, etc.).

```sql
SELECT 
    user_id,
    COUNT(order_id) AS total_transacoes,
    COUNT(DISTINCT order_id) AS total_pedidos_unicos,
    ROUND(SUM(sale_price), 2) AS receita_total_gasta,
    ROUND(AVG(sale_price), 2) AS ticket_medio,
    ROUND(MAX(sale_price), 2) AS maior_compra
FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE status NOT IN ('Cancelled')
GROUP BY user_id
HAVING total_pedidos_unicos >= 2 -- Filtra apenas clientes recorrentes
ORDER BY receita_total_gasta DESC;
```

> **Diferença:** `WHERE` filtra as linhas **antes** de agrupar. `HAVING` filtra os grupos **depois** do cálculo agregado.

---

## 5. JOINs e Relacionamentos no BigQuery

No BigQuery, quase sempre usamos `LEFT JOIN` ou `INNER JOIN`:

```sql
SELECT 
    u.id AS usuario_id,
    u.gender,
    u.country,
    o.order_id,
    o.status AS status_pedido,
    o.created_at AS data_pedido
FROM `bigquery-public-data.thelook_ecommerce.users` u
LEFT JOIN `bigquery-public-data.thelook_ecommerce.orders` o
    ON u.id = o.user_id;
```

> 💡 **Dica de Performance do BigQuery:** Em operações de `JOIN`, coloque a **maior tabela à esquerda** e a **menor tabela à direita**. O BigQuery transmitirá a tabela menor para os nós onde a tabela maior está armazenada (*broadcast join*), tornando a execução muito mais rápida.

---

## 6. CTEs (Common Table Expressions): O Padrão para Pipelines

Esqueça subconsultas confusas e aninhadas cheias de parênteses. Cientistas de Dados profissionais organizam o raciocínio com blocos `WITH ... AS`:

```sql
WITH pedidos_validos AS (
    -- Etapa 1: Filtrar apenas pedidos concluídos
    SELECT user_id, order_id, created_at, num_of_item
    FROM `bigquery-public-data.thelook_ecommerce.orders`
    WHERE status = 'Complete'
),

metricas_cliente AS (
    -- Etapa 2: Agregar por cliente
    SELECT 
        user_id,
        COUNT(order_id) AS qtd_compras_completas,
        SUM(num_of_item) AS total_itens_comprados
    FROM pedidos_validos
    GROUP BY user_id
)

-- Etapa 3: Cruzar com o cadastro dos usuários
SELECT 
    u.id,
    u.age,
    u.country,
    COALESCE(m.qtd_compras_completas, 0) AS total_compras,
    COALESCE(m.total_itens_comprados, 0) AS total_itens
FROM `bigquery-public-data.thelook_ecommerce.users` u
LEFT JOIN metricas_cliente m ON u.id = m.user_id;
```

---

## 7. Window Functions (Funções de Janela) - O Diferencial em Entrevistas

As funções de janela realizam cálculos em um conjunto de linhas relacionadas sem colapsar as linhas como faz o `GROUP BY`.

### 7.1. `ROW_NUMBER()`: Extrair o Último Evento ou Compra de Cada Usuário

```sql
WITH pedidos_ordenados AS (
    SELECT 
        user_id,
        order_id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY user_id 
            ORDER BY created_at DESC
        ) AS rank_recente
    FROM `bigquery-public-data.thelook_ecommerce.orders`
)
-- Pega exclusivamente o último pedido de cada cliente (rank = 1)
SELECT user_id, order_id, created_at AS data_ultimo_pedido
FROM pedidos_ordenados
WHERE rank_recente = 1;
```

### 7.2. `LAG()` e `LEAD()`: Intervalo Entre Compras Consecutivas

```sql
SELECT 
    user_id,
    order_id,
    created_at AS data_pedido_atual,
    -- Pega a data da compra anterior do mesmo cliente
    LAG(created_at) OVER (
        PARTITION BY user_id 
        ORDER BY created_at ASC
    ) AS data_pedido_anterior,
    -- Calcula a diferença de dias entre uma compra e a anterior
    DATE_DIFF(
        DATE(created_at),
        DATE(LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at ASC)),
        DAY
    ) AS dias_desde_a_compra_anterior
FROM `bigquery-public-data.thelook_ecommerce.orders`;
```

---

## 8. Manipulação de Datas e Séries Temporais

Problemas de Machine Learning (como previsão de Churn e LTV) exigem cálculo de recência e janelas temporais:

```sql
SELECT 
    created_at,
    -- Extrai partes da data
    EXTRACT(YEAR FROM created_at) AS ano,
    EXTRACT(MONTH FROM created_at) AS mes,
    EXTRACT(DAYOFWEEK FROM created_at) AS dia_da_semana, -- 1 = Domingo, 7 = Sábado
  
    -- Trunca para o primeiro dia do mês (excelente para agregar por mês)
    DATE_TRUNC(DATE(created_at), MONTH) AS mes_ano,
  
    -- Calcula a diferença em dias até hoje
    DATE_DIFF(CURRENT_DATE(), DATE(created_at), DAY) AS dias_ate_hoje,
  
    -- Adiciona ou subtrai tempo
    DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AS limite_30_dias_atras
FROM `bigquery-public-data.thelook_ecommerce.orders`
LIMIT 10;
```

---

## 9. Arrays, Structs e o Operador UNNEST()

O BigQuery permite colunas do tipo `ARRAY` (listas) e `STRUCT` (objetos/dicionários). Muito comum ao trabalhar com Google Analytics 4 (GA4) ou logs de eventos.

Para transformar uma lista em linhas individuais e poder filtrar ou cruzar, usamos `UNNEST()`:

```sql
-- Exemplo: Filtrando usuários que vieram de uma lista de canais específicos
SELECT id, email, traffic_source
FROM `bigquery-public-data.thelook_ecommerce.users`
WHERE traffic_source IN UNNEST(['Search', 'Organic', 'Facebook'])
LIMIT 10;
```

---

## 10. Otimização de Consultas & Redução de Custos (O que usar no lugar do LIMIT)

O BigQuery cobra pelo **volume de dados lido do disco**, e não pelas linhas enviadas para a sua tela. O `LIMIT 10` obriga o BigQuery a ler as colunas da tabela inteira para só no final pegar 10 linhas e descartar o resto.

Para **realmente baratear** a consulta e cortar o volume de bytes escaneados, use estas ferramentas:

### 10.1. `TABLESAMPLE SYSTEM (X PERCENT)` — O verdadeiro substituto do LIMIT para testes
O BigQuery possui uma funcionalidade nativa de **amostragem pseudoaleatória**. Diferente do `LIMIT`, o `TABLESAMPLE` lê fisicamente apenas uma porcentagem dos blocos de dados do disco e **COBRA APENAS POR ESSA PORCENTAGEM**:

```sql
-- Lê e cobra apenas 1% dos dados físicos da tabela inteira!
SELECT 
    id, age, gender, country
FROM `bigquery-public-data.thelook_ecommerce.users` 
TABLESAMPLE SYSTEM (1 PERCENT);
```
> 💡 **Dica de ouro:** Se uma tabela corporativa tem 100 GB, usar `TABLESAMPLE SYSTEM (1 PERCENT)` fará você processar e pagar apenas por **1 GB**, obtendo uma amostra estatisticamente representativa para fazer sua Análise Exploratória (EDA) no Pandas sem estourar o orçamento!

### 10.2. Filtrar pela Coluna de Partição (`WHERE data >= ...`)
Em ambientes corporativos, tabelas com milhões ou bilhões de linhas são **particionadas por data** (cada dia de dados fica guardado em uma pasta/bloco separado).

Quando você filtra pela coluna particionada, o BigQuery **ignora fisicamente** todo o restante da tabela:

```sql
-- O BigQuery só lê os blocos de dados a partir de 2023-12-01 e pula anos anteriores:
SELECT 
    order_id, user_id, sale_price, created_at
FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= '2023-12-01';
```

### 10.3. Filtrar por Colunas de Clusterização (`CLUSTER BY`)
Tabelas clusterizadas organizam os dados internamente ordenados por colunas frequentemente consultadas (ex: `country` ou `status`). 

```sql
-- Se a tabela estiver clusterizada por country, o BigQuery pula blocos que não batem:
SELECT id, age, country 
FROM `bigquery-public-data.thelook_ecommerce.users`
WHERE country = 'Brasil';
```

### 10.4. Tabela Resumo: O que realmente reduz custos no BigQuery?

| Recurso | Reduz linhas exibidas? | **Reduz o custo / bytes faturados?** | Quando usar? |
| :--- | :---: | :---: | :--- |
| `LIMIT 10` |  Sim | ❌ **NÃO** | Apenas para inspecionar o formato visual final. |
| `SELECT col1, col2` (Column Pruning) | ➖ Não |  **SIM (Muito)** | **Sempre!** Nunca use `SELECT *`. |
| `TABLESAMPLE SYSTEM (1 PERCENT)` |  Sim |  **SIM (Proporcional)** | Para EDA, testes locais e protótipos de pipeline. |
| `WHERE data >= '2024-01-01'` (Partição) |  Sim |  **SIM (Dramático)** | Filtros temporais em tabelas históricas. |
| `WHERE status = 'Complete'` (Cluster) |  Sim |  **SIM** | Filtros de categorias e status em tabelas clusterizadas. |

---

## 11. Projeto Prático Completo: Feature Store de E-commerce

Aqui está uma query pronta que você pode rodar agora no BigQuery para gerar a base de treino do seu modelo de **Classificação de Churn**:

```sql
-- FEATURE STORE: Previsão de Churn / Recompra de Clientes
WITH base_compras AS (
    SELECT 
        user_id,
        COUNT(DISTINCT order_id) AS frequencia_pedidos,
        ROUND(SUM(sale_price), 2) AS valor_monetario_total,
        ROUND(AVG(sale_price), 2) AS ticket_medio,
        MAX(created_at) AS data_ultima_compra,
        MIN(created_at) AS data_primeira_compra
    FROM `bigquery-public-data.thelook_ecommerce.order_items`
    WHERE status NOT IN ('Cancelled')
    GROUP BY user_id
),

devolucoes AS (
    SELECT 
        user_id,
        COUNT(id) AS qtd_itens_devolvidos
    FROM `bigquery-public-data.thelook_ecommerce.order_items`
    WHERE status = 'Returned'
    GROUP BY user_id
)

SELECT 
    u.id AS cliente_id,
    u.age AS idade,
    u.gender AS genero,
    u.country AS pais,
    u.traffic_source AS canal_aquisicao,
  
    -- Features Transacionais (RFM)
    COALESCE(c.frequencia_pedidos, 0) AS total_pedidos,
    COALESCE(c.valor_monetario_total, 0.0) AS receita_gerada,
    COALESCE(c.ticket_medio, 0.0) AS ticket_medio,
  
    -- Recência (dias desde a última compra até uma data de corte de referência)
    DATE_DIFF(DATE '2024-01-01', DATE(c.data_ultima_compra), DAY) AS recencia_dias,
  
    -- Tempo de relacionamento do cliente (tempo entre 1ª e última compra)
    DATE_DIFF(DATE(c.data_ultima_compra), DATE(c.data_primeira_compra), DAY) AS dias_como_cliente,
  
    -- Taxa de devolução
    COALESCE(d.qtd_itens_devolvidos, 0) AS itens_devolvidos,
  
    -- TARGET: Cliente comprou apenas 1 vez e nunca mais voltou (Churn = 1, Ativo = 0)
    CASE 
        WHEN COALESCE(c.frequencia_pedidos, 0) <= 1 THEN 1 
        ELSE 0 
    END AS flag_churn

FROM `bigquery-public-data.thelook_ecommerce.users` u
INNER JOIN base_compras c ON u.id = c.user_id
LEFT JOIN devolucoes d ON u.id = d.user_id
WHERE u.created_at <= '2023-12-31' -- Corte temporal para evitar Data Leakage
LIMIT 2000;
```
