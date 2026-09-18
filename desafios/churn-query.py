from reading_sql.config import SNAPSHOTS_PATH
from reading_sql.config import PROJECT_ID
from reading_sql.config import GOOGLE_APPLICATION_CREDENTIALS_PATH
import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)

client = bigquery.Client(project=PROJECT_ID)

query = """
WITH dados_por_pedido AS (
    SELECT 
        order_items.order_id AS order_id,
        SUM(order_items.sale_price) as receita_total,
        COUNTIF(order_items.status = "Returned") as itens_devolvidos
    FROM `bigquery-public-data.thelook_ecommerce.order_items` order_items
    WHERE order_items.created_at < "2024-01-01"
    AND NOT order_items.status = "Cancelled"
    GROUP BY order_items.order_id
),
dados_pedidos_por_usuario AS (
    SELECT 
        orders.user_id AS user_id,
        COUNT(DISTINCT dados_por_pedido.order_id) AS total_pedidos,
        SUM(dados_por_pedido.receita_total) AS receita_total,
        AVG(dados_por_pedido.receita_total) AS ticket_medio,
        MIN(orders.created_at) AS data_primeira_compra,
        MAX(orders.created_at) AS data_ultima_compra,
        SUM(dados_por_pedido.itens_devolvidos) AS itens_devolvidos
    FROM `bigquery-public-data.thelook_ecommerce.orders` orders
    LEFT JOIN dados_por_pedido ON dados_por_pedido.order_id = orders.order_id
    WHERE orders.created_at < "2024-01-01"
    AND NOT orders.status = "Cancelled"
    GROUP BY orders.user_id
)
SELECT 
    id AS user_id,
    age AS idade,
    gender AS genero,
    country AS pais,
    traffic_source AS canal_aquisicao,
    dados_pedidos_por_usuario.total_pedidos AS total_pedidos,
    ROUND(dados_pedidos_por_usuario.receita_total, 2) AS receita_total,
    ROUND(dados_pedidos_por_usuario.ticket_medio, 2) AS ticket_medio,
    IFNULL(dados_pedidos_por_usuario.itens_devolvidos, 0) AS itens_devolvidos,
    DATE_DIFF(
        DATE '2024-01-01', 
        DATE(dados_pedidos_por_usuario.data_ultima_compra), 
        DAY
    ) as recencia_dias,
    DATE_DIFF(
        DATE(dados_pedidos_por_usuario.data_ultima_compra), 
        DATE(dados_pedidos_por_usuario.data_primeira_compra), 
        DAY
    ) as tempo_relacionamento_dias,
    CASE WHEN dados_pedidos_por_usuario.total_pedidos = 1 THEN 1 ELSE 0 END AS churn
FROM `bigquery-public-data.thelook_ecommerce.users` users
TABLESAMPLE SYSTEM (0.1 PERCENT)
INNER JOIN dados_pedidos_por_usuario ON dados_pedidos_por_usuario.user_id = users.id;
"""

dataframe = client.query(query).to_dataframe()

dataframe.to_parquet(SNAPSHOTS_PATH / "churn-query.parquet")