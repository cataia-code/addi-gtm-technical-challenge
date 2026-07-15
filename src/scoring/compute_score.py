"""Scoring model and validation helpers.

This module keeps scoring logic importable from notebooks, tests and agents.
It intentionally avoids writing files unless a caller asks for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "GTM-Engineer-BC-Dataset.xlsx"
TOP50_PATH = ROOT / "analysis" / "top50.csv"


EXCLUDED_CATEGORIES = {
    "Grandes Superficies",
    "Educacion",
    "Educación",
    "Viajes",
    "Viajes y experiencias",
    "Salud",
    "Musica y audio",
    "Música y audio",
    "Música/Audio",
}


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    detail: str


def _norm_pct(series: pd.Series, ascending: bool = True) -> pd.Series:
    return series.rank(method="average", pct=True, ascending=ascending) * 100


def _recency_score(days_since_last_orig: pd.Series) -> pd.Series:
    return np.exp(-days_since_last_orig / 30) * 100


def _category_bonus(universo: pd.DataFrame) -> dict[str, int]:
    bpi_by_category = universo.groupby("category").apply(
        lambda x: float(x["is_marketplace_today"].sum()) / len(x) * 100 if len(x) else 0
    )

    def bonus(bpi: float) -> int:
        if bpi < 12:
            return 10
        if bpi < 19:
            return 5
        return 0

    return {str(category): bonus(float(bpi)) for category, bpi in bpi_by_category.items()}


def load_universo(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    return pd.read_excel(dataset_path, sheet_name="universo_potencial")


def compute_top50(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    """Compute the top 50 portfolio from the source workbook.

    Tier A is the top 15 by GMV among active non-marketplace brands, excluding
    Grandes Superficies. Tier B uses the validated multidimensional score.
    """

    universo = load_universo(dataset_path)
    opp = universo[
        (universo["is_marketplace_today"] == 0)
        & (universo["is_active_90d"] == 1)
        & (~universo["category"].isin(EXCLUDED_CATEGORIES))
    ].copy()

    tier_a = opp.nlargest(15, "gmv_cop_millions_12m").copy()
    tier_a["tier"] = "A"

    pool = opp[~opp["brand_id"].isin(tier_a["brand_id"])].copy()
    pool["gmv_90d_to_12m_ratio"] = (
        pool["gmv_cop_millions_90d"] * 4 / pool["gmv_cop_millions_12m"]
    )
    pool["gmv_pctl"] = _norm_pct(pool["gmv_cop_millions_12m"], ascending=True)
    pool["clients_pctl"] = _norm_pct(pool["n_unique_clients_12m"], ascending=True)
    ticket_target_mid = 275000
    pool["ticket_dist"] = (pool["avg_ticket_cop"] - ticket_target_mid).abs()
    pool["ticket_pctl"] = 100 - _norm_pct(pool["ticket_dist"], ascending=True)
    pool["fit_score"] = (
        pool["gmv_pctl"] * (30 / 55)
        + pool["clients_pctl"] * (15 / 55)
        + pool["ticket_pctl"] * (10 / 55)
    )
    pool["ratio_wins"] = pool["gmv_90d_to_12m_ratio"].clip(upper=2.0)
    pool["momentum_score"] = (pool["ratio_wins"] / 2.0) * 100
    pool["recency_score"] = _recency_score(pool["days_since_last_orig"])
    bonus_map = _category_bonus(universo)
    pool["category_bonus"] = pool["category"].map(bonus_map).fillna(0)
    pool["final_score"] = (
        pool["fit_score"] * 0.55
        + pool["momentum_score"] * 0.25
        + pool["recency_score"] * 0.05
        + pool["category_bonus"]
    )

    tier_b = _select_top_with_category_cap(pool, n=35, cap_pct=0.40)
    tier_b["tier"] = "B"

    tier_a_export = tier_a.copy()
    tier_a_export["rank"] = range(1, 16)
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
    tier_b_export["rank"] = range(16, 51)
    tier_b_export["why"] = tier_b_export.apply(
        lambda row: (
            f"Score {row['final_score']:.0f}: "
            f"{row['gmv_cop_millions_12m']:.0f}MM, "
            f"{100 * row['gmv_90d_to_12m_ratio']:.0f}%"
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
    return _round_for_export(top50)


def _select_top_with_category_cap(pool: pd.DataFrame, n: int, cap_pct: float) -> pd.DataFrame:
    pool_sorted = pool.sort_values("final_score", ascending=False).reset_index(drop=True)
    cap_per_category = int(n * cap_pct)
    selected = []
    category_counts: dict[str, int] = {}

    for _, row in pool_sorted.iterrows():
        category = str(row["category"])
        if category_counts.get(category, 0) >= cap_per_category:
            continue
        selected.append(row)
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) == n:
            break

    return pd.DataFrame(selected).reset_index(drop=True)


def _round_for_export(top50: pd.DataFrame) -> pd.DataFrame:
    rounded = top50.copy()
    rounded["gmv_cop_millions_12m"] = rounded["gmv_cop_millions_12m"].round(0).astype(int)
    rounded["gmv_90d_to_12m_ratio"] = rounded["gmv_90d_to_12m_ratio"].round(2)
    for column in [
        "recency_score",
        "fit_score",
        "momentum_score",
        "category_bonus",
        "final_score",
    ]:
        rounded[column] = rounded[column].round(1)
    return rounded


def validate_against_current_top50(
    dataset_path: Path = DATASET_PATH, top50_path: Path = TOP50_PATH
) -> list[ValidationResult]:
    computed = compute_top50(dataset_path)
    current = pd.read_csv(top50_path)
    results = [
        ValidationResult("row_count", len(computed) == len(current) == 50, f"{len(computed)} vs {len(current)}"),
        ValidationResult(
            "brand_order",
            computed["brand_id"].tolist() == current["brand_id"].tolist(),
            "same ordered brand_id list",
        ),
        ValidationResult(
            "tier_a_size",
            int((computed["tier"] == "A").sum()) == 15,
            f"{int((computed['tier'] == 'A').sum())} Tier A",
        ),
        ValidationResult(
            "no_grandes_superficies",
            not computed["category"].eq("Grandes Superficies").any(),
            "Grandes Superficies excluded",
        ),
    ]
    return results


if __name__ == "__main__":
    for result in validate_against_current_top50():
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name}: {result.detail}")
