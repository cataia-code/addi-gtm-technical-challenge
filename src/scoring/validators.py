"""Reusable validation gates for the scoring model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .constants import (
    CAP_CATEGORIA_TIER_B,
    CATEGORIAS_EXCLUIDAS_MPFIT,
    TIER_A_SIZE,
    TIER_B_SIZE,
)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    detail: str


def validate_no_duplicates(top50: pd.DataFrame) -> ValidationResult:
    duplicates = int(top50["brand_id"].duplicated().sum())
    return ValidationResult("sin_duplicados", duplicates == 0, f"{duplicates} duplicados")


def validate_no_excluded_categories(top50: pd.DataFrame) -> ValidationResult:
    present = sorted(set(top50["category"]).intersection(CATEGORIAS_EXCLUIDAS_MPFIT))
    detail = "0 categorias excluidas" if not present else "presentes=" + ",".join(present)
    return ValidationResult("sin_categorias_excluidas", len(present) == 0, detail)


def validate_tier_a_exact_top15(top50: pd.DataFrame, universo: pd.DataFrame) -> ValidationResult:
    opp = _opportunity_universe(universo)
    expected = set(opp.nlargest(TIER_A_SIZE, "gmv_cop_millions_12m")["brand_id"])
    actual = set(top50[top50["tier"] == "A"]["brand_id"])
    detail = "Tier A coincide con top 15 GMV"
    if actual != expected:
        detail = f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
    return ValidationResult("tier_a_top15_exacto", actual == expected, detail)


def validate_fit_score_positive(top50: pd.DataFrame) -> ValidationResult:
    tier_b = top50[top50["tier"] == "B"].copy()
    corr = tier_b[["fit_score", "gmv_cop_millions_12m"]].corr().iloc[0, 1]
    return ValidationResult("fit_score_signo", corr > 0.3, f"corr={corr:.3f}")


def validate_momentum_score_positive(top50: pd.DataFrame) -> ValidationResult:
    tier_b = top50[top50["tier"] == "B"].copy()
    corr = tier_b[["momentum_score", "gmv_90d_to_12m_ratio"]].corr().iloc[0, 1]
    return ValidationResult("momentum_score_signo", corr > 0.5, f"corr={corr:.3f}")


def validate_recency_score_negative(top50: pd.DataFrame) -> ValidationResult:
    tier_b = top50[top50["tier"] == "B"].copy()
    corr = tier_b[["recency_score", "days_since_last_orig"]].corr().iloc[0, 1]
    return ValidationResult("recency_score_signo", corr < -0.3, f"corr={corr:.3f}")


def validate_category_cap(top50: pd.DataFrame) -> ValidationResult:
    tier_b = top50[top50["tier"] == "B"].copy()
    max_count = int(tier_b["category"].value_counts().max())
    max_allowed = int(TIER_B_SIZE * CAP_CATEGORIA_TIER_B)
    return ValidationResult(
        "cap_categoria_tier_b",
        max_count <= max_allowed,
        f"max_count={max_count}, max_allowed={max_allowed}",
    )


def validate_gmv_matches_dataset(top50: pd.DataFrame, universo: pd.DataFrame) -> ValidationResult:
    source = universo.set_index("brand_id")["gmv_cop_millions_12m"]
    mismatches = []
    for _, row in top50.iterrows():
        expected = source.get(row["brand_id"])
        if expected is None or abs(float(row["gmv_cop_millions_12m"]) - float(expected)) > 0.5:
            mismatches.append(row["brand_id"])
    detail = "todos coinciden" if not mismatches else "mismatches=" + ",".join(mismatches[:10])
    return ValidationResult("gmv_coincide_dataset", len(mismatches) == 0, detail)


def validate_against_existing_csv(
    computed: pd.DataFrame,
    csv_path: Path,
    *,
    tolerance: float = 0.1,
) -> list[ValidationResult]:
    current = pd.read_csv(csv_path)
    current_scores = pd.to_numeric(current["final_score"], errors="coerce")
    computed_scores = pd.to_numeric(computed["final_score"], errors="coerce")
    deltas = (computed_scores.fillna(-9999) - current_scores.fillna(-9999)).abs()
    max_delta = float(deltas.max()) if len(deltas) else 0.0
    return [
        ValidationResult("csv_50_filas", len(computed) == len(current) == 50, f"{len(computed)} vs {len(current)}"),
        ValidationResult(
            "csv_brand_order",
            computed["brand_id"].tolist() == current["brand_id"].tolist(),
            "mismo orden de brand_id",
        ),
        ValidationResult(
            "csv_final_score_tolerancia_0_1",
            bool((deltas <= tolerance).all()),
            f"max_delta={max_delta:.3f}",
        ),
    ]


def run_all_validations(top50: pd.DataFrame, universo: pd.DataFrame) -> list[ValidationResult]:
    return [
        validate_no_duplicates(top50),
        validate_no_excluded_categories(top50),
        validate_tier_a_exact_top15(top50, universo),
        validate_fit_score_positive(top50),
        validate_momentum_score_positive(top50),
        validate_recency_score_negative(top50),
        validate_category_cap(top50),
        validate_gmv_matches_dataset(top50, universo),
    ]


def _opportunity_universe(universo: pd.DataFrame) -> pd.DataFrame:
    return universo[
        (universo["is_marketplace_today"] == 0)
        & (universo["is_active_90d"] == 1)
        & (~universo["category"].isin(CATEGORIAS_EXCLUIDAS_MPFIT))
    ].copy()

