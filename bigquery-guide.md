# 🎯 Guia Prático de BigQuery para Estágio em Ciência de Dados

> **Foco:** O essencial que você realmente precisa saber no dia a dia para conectar, puxar dados para o Pandas com segurança de custo e salvar resultados de modelos.

---

## 📑 O que você realmente vai usar:

1. [Como Conectar no Python](#1-como-conectar-no-python)
2. [Como Rodar Queries sem Estourar a Cota (Regras de Ouro)](#2-como-rodar-queries-sem-estourar-a-cota-regras-de-ouro)
3. [Como Puxar os Dados para o Pandas](#3-como-puxar-os-dados-para-o-pandas)
4. [E se a base for pesada demais para a RAM? (BigFrames)](#4-e-se-a-base-for-pesada-demais-para-a-ram-bigframes)
5. [Como Salvar as Predições do Modelo no BigQuery](#5-como-salvar-as-predições-do-modelo-no-bigquery)
6. [Script Modelo Pronto para Uso](#6-script-modelo-pronto-para-uso)

---

## 1. Como Conectar no Python

Para o estágio, tudo o que você precisa é apontar para a sua chave `.json` e inicializar o cliente:

```python
import os
from google.cloud import bigquery
from reading_sql.config import PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS_PATH

# 1. Informa onde está a chave baixada
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)

# 2. Inicializa o cliente apontando para o seu projeto
client = bigquery.Client(project=PROJECT_ID)
```

---

## 2. Como Rodar Queries sem Estourar a Cota (Regras de Ouro)

No BigQuery você paga pelo **volume lido do disco**, e não pelas linhas na tela. Para nunca passar vergonha com custo:

### Regra 1: Para testar no Pandas, use `TABLESAMPLE` (não use `LIMIT`)

O `LIMIT 10` lê a tabela inteira e só corta no final. O `TABLESAMPLE` lê apenas uma fatia física do disco e cobra só por ela:

```sql
-- Lê e cobra apenas 1% dos dados para você testar seu código:
SELECT id, age, gender, country
FROM `bigquery-public-data.thelook_ecommerce.users`
TABLESAMPLE SYSTEM (1 PERCENT);
```

### Regra 2: Nunca faça `SELECT *`

Em banco colunar, cada coluna é um arquivo no disco. Se você só precisa de 4 colunas, chame apenas as 4 colunas. Isso corta 80% a 90% da cobrança.

### Regra 3: Veja quanto vai gastar ANTES de rodar (`Dry Run`)

O BigQuery permite calcular o consumo em Megabytes sem rodar a query e sem gastar 1 centavo:

```python
def checar_tamanho_query(client: bigquery.Client, query: str):
    job_config = bigquery.QueryJobConfig(dry_run=True)
    job = client.query(query, job_config=job_config)
    mb = job.total_bytes_processed / (1024 ** 2)
    print(f"📊 Essa query vai escanear: {mb:.2f} MB")
```

---

## 3. Como Puxar os Dados para o Pandas

Evite usar f-strings para colocar variáveis dentro do SQL. Use parâmetros formais (`@parametro`):

```python
# 1. Configura parâmetros de filtro
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("pais_alvo", "STRING", "Brasil"),
        bigquery.ScalarQueryParameter("idade_minima", "INT64", 18),
    ]
)

# 2. Escreve a query com os @parâmetros
query = """
    SELECT id, age, gender, country, traffic_source
    FROM `bigquery-public-data.thelook_ecommerce.users`
    WHERE country = @pais_alvo
      AND age >= @idade_minima
"""

# 3. Executa e converte direto para Pandas!
df = client.query(query, job_config=job_config).to_dataframe()
print(df.head())
```

---

## 4. E se a base for pesada demais para a RAM? (BigFrames)

Se você precisar analisar uma tabela de 10 milhões de linhas que travaria a memória do seu computador, use o **BigFrames** (`bigframes.pandas`).

Ele tem os mesmos comandos do Pandas, mas roda **dentro do BigQuery**:

```python
import bigframes.pandas as bpd

# Conecta na nuvem
bpd.options.bigquery.project = "sandbox-508815"

# Carrega a tabela virtualmente (NÃO consome a RAM do seu PC!)
df = bpd.read_gbq("bigquery-public-data.thelook_ecommerce.users")

# Filtra direto no BigQuery
df_brasil = df[df["country"] == "Brasil"]

# Pega só o resultado final pequeno para a sua máquina
amostra = df_brasil.head(100).to_pandas()
```

---

## 5. Como Salvar as Predições do Modelo no BigQuery

Depois de treinar seu modelo no Scikit-Learn e gerar predições, você precisa salvar a tabela com os resultados no BigQuery da empresa:

```python
def salvar_no_bigquery(client: bigquery.Client, df: pd.DataFrame, tabela_destino: str):
    """
    Exemplo de tabela_destino: "sandbox-508815.meu_dataset.predicoes_churn"
    """
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE", # Sobrescreve se a tabela já existir
        autodetect=True                     # Detecta os tipos das colunas sozinho
    )

    job = client.load_table_from_dataframe(df, tabela_destino, job_config=job_config)
    job.result() # Aguarda terminar
    print(f"✅ {len(df)} linhas salvas com sucesso em '{tabela_destino}'!")
```

---

## 6. Script Modelo Pronto para Uso

Aqui está a estrutura limpa e direta para usar no seu projeto (`src/reading_sql/data.py`):

```python
import os
import pandas as pd
from google.cloud import bigquery
from reading_sql.config import PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS_PATH

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)
client = bigquery.Client(project=PROJECT_ID)

def extrair_dados(pais: str = "Brasil") -> pd.DataFrame:
    query = """
        SELECT 
            id AS user_id,
            age,
            gender,
            country,
            traffic_source,
            created_at
        FROM `bigquery-public-data.thelook_ecommerce.users`
        WHERE country = @pais
    """
  
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("pais", "STRING", pais)
        ]
    )

    print(f"Buscando usuários de {pais} no BigQuery...")
    return client.query(query, job_config=job_config).to_dataframe()

if __name__ == "__main__":
    df = extrair_dados("Brasil")
    print(f"Dimensões: {df.shape}")
    print(df.head())
```
