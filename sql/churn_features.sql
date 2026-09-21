WITH dados_por_pedido AS (
    SELECT 
        order_items.user_id AS user_id,
        SUM(order_items.sale_price) AS receita_total,
        COALESCE(COUNT(DISTINCT order_items.order_id), 0) AS total_pedidos,        
        COUNTIF(order_items.status = "Returned") AS itens_devolvidos,
        DATE(MAX(order_items.created_at)) AS data_pedido_mais_recente,
        CASE WHEN
            COUNT(DISTINCT order_items.order_id) = 1
            THEN 0
            ELSE DATE_DIFF(MAX(order_items.created_at), MIN(order_items.created_at), DAY)
            END
            AS tempo_relacionamento_dias,
        DATE_DIFF(DATE(@reference_date), DATE(MAX(order_items.created_at)), DAY) AS recencia_dias
    FROM `bigquery-public-data.thelook_ecommerce.order_items` order_items
    WHERE order_items.created_at < TIMESTAMP(@reference_date)
    AND NOT order_items.status = "Cancelled"
    GROUP BY order_items.user_id
),
dados_futuros_churn AS (
    SELECT
        order_items.user_id AS user_id,
        IFNULL(COUNT(DISTINCT order_items.order_id), 0) AS total_pedidos
    FROM `bigquery-public-data.thelook_ecommerce.order_items` order_items
    WHERE order_items.created_at >= TIMESTAMP(@reference_date) AND DATE(order_items.created_at) < DATE_ADD(DATE(@reference_date), INTERVAL 6 MONTH)
    AND NOT order_items.status = "Cancelled"
    GROUP BY order_items.user_id
)
SELECT 
    id AS user_id,
    age AS idade,
    gender AS genero,
    country AS pais,
    traffic_source AS canal_aquisicao,
    dados_por_pedido.total_pedidos AS total_pedidos,
    ROUND(dados_por_pedido.receita_total, 2) AS receita_total,
    ROUND(dados_por_pedido.receita_total / dados_por_pedido.total_pedidos, 2) AS ticket_medio,
    IFNULL(dados_por_pedido.itens_devolvidos, 0) AS itens_devolvidos,
    dados_por_pedido.tempo_relacionamento_dias AS tempo_relacionamento_dias,
    dados_por_pedido.recencia_dias AS recencia_dias,
    CASE 
        WHEN dados_futuros_churn.total_pedidos IS NULL
        THEN 1
        ELSE 0
        END
        AS churn
FROM `bigquery-public-data.thelook_ecommerce.users` users
TABLESAMPLE SYSTEM (0.1 PERCENT)
INNER JOIN dados_por_pedido ON dados_por_pedido.user_id = users.id
LEFT JOIN dados_futuros_churn ON dados_futuros_churn.user_id = users.id
WHERE dados_por_pedido.data_pedido_mais_recente >= DATE_SUB(DATE(@reference_date), INTERVAL 6 MONTH)