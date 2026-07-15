-- =====================================================================================
-- scoring.sql — Modelo de scoring 0-100 para priorizacion de brands x-sell BNPL -> Marketplace
-- Dialecto: Spark SQL (Databricks). Equivalente exacto de la logica en analysis/scoring_model.ipynb
-- (ahi ejecutada en DuckDB sobre pandas; aqui sobre tablas Delta/catalogo).
--
-- Supuestos declarados:
--   - Ticket compatible BNPL retail: COP 200,000 - 5,000,000 (supuesto de negocio, no viene del dataset).
--   - Cohorte de categoria prioritaria (BPI < 12%): Vehiculos y autopartes, Hogar, Moda
--     (decision ya tomada en CLAUDE.md "Decisiones ya tomadas", primera cohorte del corte S1->S2).
--   - Grandes Superficies (3 megacuentas) excluidas: van a deal manual, no a la motion automatizada.
-- =====================================================================================

WITH base AS (
    -- Universo elegible: oportunidad canonica (BNPL activo, fuera de Marketplace) menos Grandes Superficies
    SELECT
        brand_id,
        category,
        cluster,
        gmv_cop_millions_12m,
        n_unique_clients_12m,
        avg_ticket_cop,
        gmv_cop_millions_90d,
        days_since_last_orig,
        -- momentum: gmv 90d anualizado (x4) sobre gmv 12m; 0 si no hay gmv_12m (evita division por cero)
        CASE WHEN gmv_cop_millions_12m > 0
             THEN gmv_cop_millions_90d * 4.0 / gmv_cop_millions_12m
             ELSE 0 END AS momentum_ratio,
        -- compatibilidad de ticket con el rango tipico BNPL retail (supuesto declarado arriba)
        CASE
            WHEN avg_ticket_cop BETWEEN 200000 AND 5000000 THEN 1.0
            WHEN avg_ticket_cop < 200000 THEN GREATEST(0.0, avg_ticket_cop / 200000.0)
            ELSE GREATEST(0.0, 1 - (avg_ticket_cop - 5000000.0) / 5000000.0)
        END AS ticket_compat
    FROM universo_potencial
    WHERE is_marketplace_today = 0
      AND is_active_90d = 1
      AND category NOT LIKE 'Grandes Superficies%'
),

pct AS (
    -- percentiles via window functions (PERCENT_RANK) -- identico en Spark SQL y DuckDB
    SELECT
        base.*,
        PERCENT_RANK() OVER (ORDER BY gmv_cop_millions_12m)        AS pct_gmv,
        PERCENT_RANK() OVER (ORDER BY n_unique_clients_12m)        AS pct_clients,
        PERCENT_RANK() OVER (ORDER BY momentum_ratio)              AS pct_momentum,
        PERCENT_RANK() OVER (ORDER BY days_since_last_orig DESC)   AS pct_recency  -- menos dias = mejor
    FROM base
),

cat_bpi AS (
    -- BPI por categoria, sobre TODO el universo (no solo el elegible) -- define el bono de categoria
    SELECT category, 100.0 * SUM(is_marketplace_today) / COUNT(*) AS bpi_pct
    FROM universo_potencial
    GROUP BY category
),

scored AS (
    SELECT
        p.brand_id,
        p.category,
        p.cluster,
        c.bpi_pct AS category_bpi_pct,
        -- factor de bono de categoria: 1.0 si es cohorte prioritaria (BPI<12%), 0.5 si BPI<19% (target), 0 si ya paso el target
        CASE
            WHEN p.category LIKE 'Veh%' OR p.category = 'Hogar' OR p.category = 'Moda' THEN 1.0
            WHEN c.bpi_pct < 19 THEN 0.5
            ELSE 0.0
        END AS category_bonus_factor,
        ROUND(45.0 * (0.5 * p.pct_gmv + 0.3 * p.pct_clients + 0.2 * p.ticket_compat), 2) AS fit_score,
        ROUND(25.0 * p.pct_momentum, 2) AS momentum_score,
        ROUND(15.0 * p.pct_recency, 2) AS recency_score
    FROM pct p
    JOIN cat_bpi c ON p.category = c.category
)

SELECT
    brand_id,
    category,
    cluster,
    fit_score,
    momentum_score,
    recency_score,
    ROUND(15.0 * category_bonus_factor, 2) AS category_score,
    ROUND(fit_score + momentum_score + recency_score + 15.0 * category_bonus_factor, 2) AS total_score,
    -- ranking dentro del universo elegible, usado para cortar TOP 50 / TOP 200
    RANK() OVER (ORDER BY fit_score + momentum_score + recency_score + 15.0 * category_bonus_factor DESC) AS rnk
FROM scored
ORDER BY total_score DESC
-- LIMIT 50  -- descomentar para materializar solo el TOP 50 en produccion
;
