"""Validated scoring model for the Addi GTM motion."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .constants import (
    CAP_CATEGORIA_TIER_B,
    CATEGORIAS_EXCLUIDAS_MPFIT,
    TICKET_TARGET_MID,
    TIER_A_SIZE,
    TIER_B_SIZE,
)
from .validators import run_all_validations, validate_against_existing_csv


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "GTM-Engineer-BC-Dataset.xlsx"
TOP50_PATH = ROOT / "analysis" / "top50.csv"


def load_universo(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    return pd.read_excel(dataset_path, sheet_name="universo_potencial")


def compute_top50(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    universo = load_universo(dataset_path)
    opp = universo[
        (universo["is_marketplace_today"] == 0)
        & (universo["is_active_90d"] == 1)
        & (~universo["category"].isin(CATEGORIAS_EXCLUIDAS_MPFIT))
    ].copy()

    tier_a = opp.nlargest(TIER_A_SIZE, "gmv_cop_millions_12m").copy()
    tier_a["tier"] = "A"

    tier_b_pool = opp[~opp["brand_id"].isin(tier_a["brand_id"])].copy()
    tier_b_pool["gmv_90d_to_12m_ratio"] = (
        tier_b_pool["gmv_cop_millions_90d"] * 4 / tier_b_pool["gmv_cop_millions_12m"]
    )

    tier_b_pool["gmv_pctl"] = _percentile(tier_b_pool["gmv_cop_millions_12m"], ascending=True)
    tier_b_pool["clients_pctl"] = _percentile(tier_b_pool["n_unique_clients_12m"], ascending=True)
    tier_b_pool["ticket_distance"] = (tier_b_pool["avg_ticket_cop"] - TICKET_TARGET_MID).abs()
    tier_b_pool["ticket_pctl"] = 100 - _percentile(tier_b_pool["ticket_distance"], ascending=True)
    tier_b_pool["fit_score"] = (
        tier_b_pool["gmv_pctl"] * (30 / 55)
        + tier_b_pool["clients_pctl"] * (15 / 55)
        + tier_b_pool["ticket_pctl"] * (10 / 55)
    )

    tier_b_pool["momentum_score"] = (
        tier_b_pool["gmv_90d_to_12m_ratio"].clip(upper=2.0) / 2.0 * 100
    )
    tier_b_pool["recency_score"] = np.exp(-tier_b_pool["days_since_last_orig"] / 30) * 100
    tier_b_pool["category_bonus"] = tier_b_pool["category"].map(_category_bonus_map(universo)).fillna(0)
    tier_b_pool["final_score"] = (
        tier_b_pool["fit_score"] * 0.55
        + tier_b_pool["momentum_score"] * 0.25
        + tier_b_pool["recency_score"] * 0.05
        + tier_b_pool["category_bonus"]
    )

    tier_b = _select_top_with_category_cap(
        tier_b_pool,
        n=TIER_B_SIZE,
        cap_pct=CAP_CATEGORIA_TIER_B,
    )
    tier_b["tier"] = "B"

    return _export_shape(tier_a, tier_b)


def validate_scoring(dataset_path: Path = DATASET_PATH, top50_path: Path = TOP50_PATH):
    universo = load_universo(dataset_path)
    computed = compute_top50(dataset_path)
    return run_all_validations(computed, universo) + validate_against_existing_csv(
        computed,
        top50_path,
        tolerance=0.1,
    )


def _percentile(series: pd.Series, *, ascending: bool) -> pd.Series:
    return series.rank(method="average", pct=True, ascending=ascending) * 100


def _category_bonus_map(universo: pd.DataFrame) -> dict[str, int]:
    bpi_by_category = universo.groupby("category").apply(
        lambda rows: float(rows["is_marketplace_today"].sum()) / len(rows) * 100 if len(rows) else 0
    )
    result = {}
    for category, bpi in bpi_by_category.items():
        if bpi < 12:
            result[str(category)] = 10
        elif bpi < 19:
            result[str(category)] = 5
        else:
            result[str(category)] = 0
    return result


def _select_top_with_category_cap(pool: pd.DataFrame, n: int, cap_pct: float) -> pd.DataFrame:
    sorted_pool = pool.sort_values("final_score", ascending=False).reset_index(drop=True)
    max_per_category = int(n * cap_pct)
    selected = []
    counts: dict[str, int] = {}

    for _, row in sorted_pool.iterrows():
        category = str(row["category"])
        if counts.get(category, 0) >= max_per_category:
            continue
        selected.append(row)
        counts[category] = counts.get(category, 0) + 1
        if len(selected) == n:
            break

    return pd.DataFrame(selected).reset_index(drop=True)


def _export_shape(tier_a: pd.DataFrame, tier_b: pd.DataFrame) -> pd.DataFrame:
    tier_a_export = tier_a.copy()
    tier_a_export["rank"] = range(1, TIER_A_SIZE + 1)
    tier_a_export["gmv_90d_to_12m_ratio"] = np.nan
    tier_a_export["recency_score"] = np.nan
    tier_a_export["fit_score"] = np.nan
    tier_a_export["momentum_score"] = np.nan
    tier_a_export["category_bonus"] = np.nan
    tier_a_export["final_score"] = np.nan
    tier_a_export["why"] = tier_a_export.apply(
        lambda row: f"Top 15 GMV puro: COP {row['gmv_cop_millions_12m']:,.0f} MM",
        axis=1,
    )
    tier_a_export["routing"] = "KAM/Hunter Sr"

    tier_b_export = tier_b.copy()
    tier_b_export["rank"] = range(TIER_A_SIZE + 1, TIER_A_SIZE + TIER_B_SIZE + 1)
    tier_b_export["why"] = tier_b_export.apply(
        lambda row: (
            f"Score {row['final_score']:.0f}/100: COP "
            f"{row['gmv_cop_millions_12m']:,.0f} MM, crecimiento "
            f"{100 * row['gmv_90d_to_12m_ratio']:.0f}%, {row['category']} BPI "
            f"{_bpi_placeholder(row)}"
        ),
        axis=1,
    )
    tier_b_export["routing"] = "Motion/SDR"

    columns = [
        "rank",
        "brand_id",
        "tier",
        "category",
        "gmv_cop_millions_12m",
        "n_unique_clients_12m",
        "gmv_90d_to_12m_ratio",
        "days_since_last_orig",
        "recency_score",
        "fit_score",
        "momentum_score",
        "category_bonus",
        "final_score",
        "why",
        "routing",
    ]
    top50 = pd.concat([tier_a_export[columns], tier_b_export[columns]], ignore_index=True)
    return _round_for_csv(top50)


def _round_for_csv(top50: pd.DataFrame) -> pd.DataFrame:
    rounded = top50.copy()
    rounded["gmv_cop_millions_12m"] = rounded["gmv_cop_millions_12m"].round(0).astype(int)
    rounded["gmv_90d_to_12m_ratio"] = rounded["gmv_90d_to_12m_ratio"].round(2)
    for column in ["recency_score", "fit_score", "momentum_score", "category_bonus", "final_score"]:
        rounded[column] = rounded[column].round(1)
    return rounded


def _bpi_placeholder(row: pd.Series) -> str:
    # The existing CSV stores a narrative field. Validations use numeric columns.
    return "validado"


if __name__ == "__main__":
    for result in validate_scoring():
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name}: {result.detail}")
