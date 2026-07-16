"""CI gate for the validated scoring model.

This file intentionally duplicates the institutional checks requested for CI:
if a future change breaks any scoring invariant, GitHub Actions must fail.
"""

from pathlib import Path

import pandas as pd

from src.scoring.compute_score import DATASET_PATH, TOP50_PATH, calcular_score, load_universo
from src.scoring.validators import run_all_validations, validate_against_existing_csv


def test_scoring_integrity_against_committed_top50():
    computed = calcular_score(DATASET_PATH)
    committed = pd.read_csv(TOP50_PATH)

    csv_checks = validate_against_existing_csv(computed, TOP50_PATH, tolerance=0.1)
    failed_csv = [check for check in csv_checks if not check.passed]
    assert not failed_csv, [f"{check.name}: {check.detail}" for check in failed_csv]

    universo = load_universo(DATASET_PATH)
    eight_checks = run_all_validations(computed, universo)
    failed_checks = [check for check in eight_checks if not check.passed]
    assert not failed_checks, [f"{check.name}: {check.detail}" for check in failed_checks]

    assert Path(TOP50_PATH).exists()
    assert len(committed) == 50
