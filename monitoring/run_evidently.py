# monitoring/run_evidently.py
from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

# --- Réglages par défaut (modifiables via variables d'env) -------------------
# Par défaut, on compare X_test_all.csv à… X_test_all.csv (smoke test).
# Ensuite tu pourras pointer CURR_CSV vers un nouveau snapshot pour mesurer un vrai drift.
REF_CSV = Path(os.getenv("REF_CSV", "notebooks/X_test_all.csv"))
CURR_CSV = Path(os.getenv("CURR_CSV", "notebooks/X_test_all.csv"))

# Où écrire le rapport HTML (ton dossier reports est à la racine du repo)
REPORT_PATH = Path("reports/drift_report.html")

# Pour éviter de charger des datasets énormes
MAX_ROWS = int(os.getenv("MAX_ROWS", "50000"))  # échantillonne si > MAX_ROWS


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    df = pd.read_csv(path)
    if len(df) > MAX_ROWS:
        df = df.sample(MAX_ROWS, random_state=42).reset_index(drop=True)
    return df


def main() -> None:
    print(f"🔹 Référence: {REF_CSV}")
    print(f"🔹 Courant  : {CURR_CSV}")

    reference = load_csv(REF_CSV)
    current = load_csv(CURR_CSV)

    # On aligne les colonnes communes pour éviter les erreurs
    common_cols = [c for c in reference.columns if c in current.columns]
    reference = reference[common_cols].copy()
    current = current[common_cols].copy()

    if reference.empty or current.empty:
        raise ValueError("Pas de colonnes communes entre les deux jeux de données.")

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.save_html(REPORT_PATH.as_posix())
    print(f"✅ Rapport Evidently généré : {REPORT_PATH.as_posix()}")


if __name__ == "__main__":
    main()
