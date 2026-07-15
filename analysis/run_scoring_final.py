#!/usr/bin/env python3
"""Scoring Model v2 - Especificacion exacta del PO"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path('C:/Users/ASUS/Documents/GitHub/addi_technical_challenge/data')
ANALYSIS_PATH = Path('C:/Users/ASUS/Documents/GitHub/addi_technical_challenge/analysis')

print("=" * 80)
print("PASO 1-10: Scoring Model v2 (Especificacion exacta del PO)")
print("=" * 80)

# ========== PASO 1 ==========
print("\nPASO 1: Filtro base")
universo = pd.read_excel(DATA_PATH / 'GTM-Engineer-BC-Dataset.xlsx', sheet_name='universo_potencial')

opp = universo[
    (universo.is_marketplace_today == 0) &
    (universo.is_active_90d == 1) &
    (universo.category != 'Grandes Superficies')
].copy()

print(f"  len(opp) = {len(opp)} (esperado 4172)")
print(f"  GMV total = {opp.gmv_cop_millions_12m.sum():,.0f} MM (esperado ~3,031,263 MM)")

# ========== PASO 2 ==========
print("\nPASO 2: Tier A (top 15 por GMV puro)")
tier_a = opp.nlargest(15, 'gmv_cop_millions_12m').copy()
tier_a['tier'] = 'A'

print(f"  len(tier_a) = {len(tier_a)}")
print(f"  GMV total = {tier_a.gmv_cop_millions_12m.sum():,.0f} MM (esperado ~739,707 MM)")
print(f"  Brands: {', '.join(tier_a.brand_id.tolist())}")

assert (tier_a.category == 'Grandes Superficies').sum() == 0, "ERROR: GS en Tier A"
assert len(tier_a) == 15, f"ERROR: {len(tier_a)} en lugar de 15"
print("  [OK] Asserts pasados")

# ========== PASO 3 ==========
print("\nPASO 3: Tier B pool")
tier_b_pool = opp[~opp.brand_id.isin(tier_a.brand_id)].copy()
tier_b_pool['gmv_90d_to_12m_ratio'] = (
    tier_b_pool.gmv_cop_millions_90d * 4 / tier_b_pool.gmv_cop_millions_12m
)
print(f"  len(tier_b_pool) = {len(tier_b_pool)}")

# ========== PASO 4 ==========
print("\nPASO 4: fit_score")
tier_b_pool['gmv_pctl'] = tier_b_pool.gmv_cop_millions_12m.rank(pct=True, ascending=True) * 100
tier_b_pool['clients_pctl'] = tier_b_pool.n_unique_clients_12m.rank(pct=True, ascending=True) * 100

ticket_target_mid = 275000
tier_b_pool['ticket_dist'] = (tier_b_pool.avg_ticket_cop - ticket_target_mid).abs()
tier_b_pool['ticket_pctl'] = 100 - tier_b_pool.ticket_dist.rank(pct=True, ascending=True) * 100

tier_b_pool['fit_score'] = (
    tier_b_pool.gmv_pctl * (30/55) +
    tier_b_pool.clients_pctl * (15/55) +
    tier_b_pool.ticket_pctl * (10/55)
)

corr_fit = tier_b_pool[['fit_score','gmv_cop_millions_12m']].corr().iloc[0,1]
print(f"  Corr fit vs GMV: {corr_fit:.3f} (esperado > 0.3)")
assert corr_fit > 0.3, f"ERROR: {corr_fit}"
print("  [OK] Assert pasado")

# ========== PASO 5 ==========
print("\nPASO 5: momentum_score")
tier_b_pool['ratio_wins'] = tier_b_pool.gmv_90d_to_12m_ratio.clip(upper=2.0)
tier_b_pool['momentum_score'] = (tier_b_pool.ratio_wins / 2.0) * 100

corr_mom = tier_b_pool[['momentum_score','gmv_90d_to_12m_ratio']].corr().iloc[0,1]
print(f"  Corr momentum vs ratio: {corr_mom:.3f} (esperado > 0.5)")
assert corr_mom > 0.5, f"ERROR: {corr_mom}"
print("  [OK] Assert pasado")

# ========== PASO 6 ==========
print("\nPASO 6: recency_score")
tier_b_pool['recency_score'] = np.exp(-tier_b_pool.days_since_last_orig / 30) * 100
print(f"  Mean: {tier_b_pool.recency_score.mean():.1f}")

# ========== PASO 7 ==========
print("\nPASO 7: category_bonus")
bpi_por_cat = universo.groupby('category').apply(
    lambda x: (x.is_marketplace_today.sum() / len(x) * 100) if len(x) > 0 else 0
)

def get_bonus(cat):
    if cat not in bpi_por_cat.index:
        return 0
    bpi = bpi_por_cat[cat]
    if bpi < 12:
        return 10
    elif bpi < 19:
        return 5
    else:
        return 0

tier_b_pool['category_bonus'] = tier_b_pool.category.apply(get_bonus)

# Excluir categorias
categorias_excluidas = ['Educacion','Viajes y experiencias','Salud','Musica y audio']
print(f"  Antes exclusion: {len(tier_b_pool)}")
tier_b_pool = tier_b_pool[~tier_b_pool.category.isin(categorias_excluidas)]
print(f"  Despues exclusion: {len(tier_b_pool)}")

# ========== PASO 8 ==========
print("\nPASO 8: final_score y seleccion Tier B")
tier_b_pool['final_score'] = (
    tier_b_pool.fit_score * 0.55 +
    tier_b_pool.momentum_score * 0.25 +
    tier_b_pool.recency_score * 0.05 +
    tier_b_pool.category_bonus
)

def seleccionar_top_35_con_cap_categoria(pool, n=35, cap_pct=0.40):
    pool_sorted = pool.sort_values('final_score', ascending=False).reset_index(drop=True)
    cap_per_cat = int(np.ceil(n * cap_pct))

    selected = []
    cat_count = {}

    for _, row in pool_sorted.iterrows():
        cat = row.category
        if cat_count.get(cat, 0) < cap_per_cat:
            selected.append(row)
            cat_count[cat] = cat_count.get(cat, 0) + 1
        if len(selected) == n:
            break

    return pd.DataFrame(selected).reset_index(drop=True)

tier_b = seleccionar_top_35_con_cap_categoria(tier_b_pool, n=35, cap_pct=0.40)
tier_b['tier'] = 'B'

print(f"  Tier B seleccionado: {len(tier_b)}")
print(f"  Distribucion:")
print(tier_b.category.value_counts().to_string())

# ========== PASO 9 ==========
print("\nPASO 9: Verificacion final (6 asserts)")

top50 = pd.concat([
    tier_a[['brand_id', 'tier', 'category', 'gmv_cop_millions_12m']],
    tier_b[['brand_id', 'tier', 'category', 'gmv_cop_millions_12m']]
], ignore_index=True)

asserts_ok = 0

# 1
if (top50.category == 'Grandes Superficies').sum() == 0:
    print("  [OK] Assert 1: Sin Grandes Superficies")
    asserts_ok += 1
else:
    print(f"  [FAIL] Assert 1: {(top50.category == 'Grandes Superficies').sum()} GS")

# 2
top15_exacto = opp.nlargest(15, 'gmv_cop_millions_12m')
if set(tier_a.brand_id) == set(top15_exacto.brand_id):
    print("  [OK] Assert 2: Tier A == top 15 exacto")
    asserts_ok += 1
else:
    print("  [FAIL] Assert 2: Tier A no coincide")

# 3
if corr_fit > 0.3:
    print(f"  [OK] Assert 3: fit_score corr positivo ({corr_fit:.3f})")
    asserts_ok += 1
else:
    print(f"  [FAIL] Assert 3: corr {corr_fit}")

# 4
if corr_mom > 0.5:
    print(f"  [OK] Assert 4: momentum_score corr positivo ({corr_mom:.3f})")
    asserts_ok += 1
else:
    print(f"  [FAIL] Assert 4: corr {corr_mom}")

# 5
if tier_b.groupby('category').size().max() / 35 <= 0.40:
    print("  [OK] Assert 5: Cap categoria <= 40%")
    asserts_ok += 1
else:
    max_pct = tier_b.groupby('category').size().max() / 35
    print(f"  [FAIL] Assert 5: {max_pct*100:.1f}%")

# 6
if top50.brand_id.duplicated().sum() == 0:
    print("  [OK] Assert 6: Sin duplicados")
    asserts_ok += 1
else:
    print(f"  [FAIL] Assert 6: {top50.brand_id.duplicated().sum()} duplicados")

print(f"\n  TOTAL: {asserts_ok}/6 asserts pasados")

# ========== PASO 10 ==========
print("\nPASO 10: Numeros finales")

gmv_tier_a = tier_a.gmv_cop_millions_12m.sum()
gmv_tier_b = tier_b.gmv_cop_millions_12m.sum()
gmv_total = gmv_tier_a + gmv_tier_b
gmv_opp = opp.gmv_cop_millions_12m.sum()
pct_capturado = (gmv_total / gmv_opp) * 100

print(f"\n  1. GMV Tier A:     {gmv_tier_a:>15,.0f} MM")
print(f"  2. GMV Tier B:     {gmv_tier_b:>15,.0f} MM")
print(f"  3. % Capturado:    {pct_capturado:>15.2f}% ({gmv_total:,.0f} / {gmv_opp:,.0f})")
print(f"  4. Asserts:        {asserts_ok}/6 pasados")

# Exportar si todos los asserts pasaron
if asserts_ok == 6:
    tier_a_export = tier_a.copy()
    tier_a_export['rank'] = range(1, 16)
    tier_a_export['gmv_90d_to_12m_ratio'] = tier_a_export.gmv_cop_millions_90d * 4 / tier_a_export.gmv_cop_millions_12m
    tier_a_export['recency_score'] = np.exp(-tier_a_export.days_since_last_orig / 30) * 100
    tier_a_export['fit_score'] = np.nan
    tier_a_export['momentum_score'] = np.nan
    tier_a_export['category_bonus'] = np.nan
    tier_a_export['final_score'] = np.nan
    tier_a_export['why'] = 'Top 15 GMV puro'
    tier_a_export['routing'] = 'KAM/Hunter Sr'

    tier_b_export = tier_b.copy()
    tier_b_export['rank'] = range(16, 51)
    tier_b_export['gmv_90d_to_12m_ratio'] = tier_b_export.gmv_cop_millions_90d * 4 / tier_b_export.gmv_cop_millions_12m
    tier_b_export['why'] = tier_b_export.apply(
        lambda r: f"Score {r['final_score']:.0f}: {r['gmv_cop_millions_12m']:.0f}MM, {100*r['gmv_90d_to_12m_ratio']:.0f}%",
        axis=1
    )
    tier_b_export['routing'] = 'Motion/SDR'

    top50_export = pd.concat([
        tier_a_export[['rank', 'brand_id', 'tier', 'category', 'gmv_cop_millions_12m',
                       'n_unique_clients_12m', 'gmv_90d_to_12m_ratio', 'days_since_last_orig',
                       'recency_score', 'fit_score', 'momentum_score', 'category_bonus',
                       'final_score', 'why', 'routing']],
        tier_b_export[['rank', 'brand_id', 'tier', 'category', 'gmv_cop_millions_12m',
                       'n_unique_clients_12m', 'gmv_90d_to_12m_ratio', 'days_since_last_orig',
                       'recency_score', 'fit_score', 'momentum_score', 'category_bonus',
                       'final_score', 'why', 'routing']]
    ], ignore_index=True)

    # Redondear
    top50_export['gmv_cop_millions_12m'] = top50_export['gmv_cop_millions_12m'].round(0).astype(int)
    top50_export['gmv_90d_to_12m_ratio'] = top50_export['gmv_90d_to_12m_ratio'].round(2)
    for col in ['recency_score', 'fit_score', 'momentum_score', 'category_bonus', 'final_score']:
        top50_export[col] = top50_export[col].round(1)

    top50_export.to_csv(ANALYSIS_PATH / 'top50.csv', index=False)
    print(f"\n  [OK] EXPORTADO: top50.csv (50 filas)")
else:
    print(f"\n  [ERROR] No se exporto: solo {asserts_ok}/6 asserts pasaron")

print("\n" + "="*80)
