"""Contrôles de qualité des réservations — Escale Atlantique (mission FastIA).

Chaque contrôle compte les lignes d'une anomalie repérée pendant l'audit (notebooks/01_audit.ipynb).
Ils servent à deux choses :
  - `ecrire_rapport()` : un rapport de qualité écrit à chaque entraînement (appelé par train.py) ;
  - tests/test_qualite.py : un test qui échoue si une anomalie nouvelle apparaît dans la base.

Les contrôles portent sur les colonnes chargées par train.py (celles que voit le modèle).
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from nettoyage import ADR_MAX, ADULTES_MAX

# Valeurs vues dans l'historique : une valeur nouvelle doit être examinée avant d'entraîner dessus
CATEGORIES_CONNUES = {
    "hotel": {"City Hotel", "Resort Hotel"},
    "deposit_type": {"No Deposit", "Non Refund", "Refundable"},
    "customer_type": {"Transient", "Transient-Party", "Contract", "Group"},
    "market_segment": {"Online TA", "Offline TA/TO", "Groups", "Direct", "Corporate", "Complementary",
                       "Aviation", "Undefined"},
    "arrival_date_month": {"January", "February", "March", "April", "May", "June", "July", "August",
                           "September", "October", "November", "December"},
}
COLONNES_POSITIVES = [
    "lead_time", "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "adr",
    "previous_cancellations", "total_of_special_requests", "required_car_parking_spaces",
]

# Anomalies que nettoyage.nettoyer() traite : il n'en doit plus rester après nettoyage
TRAITEES = ["children_manquant", "prix_aberrant", "sejour_sans_nuit", "reservation_vide", "groupe_sur_une_ligne"]


def controles(df: pd.DataFrame) -> dict[str, int]:
    """Nombre de lignes concernées par chaque anomalie connue."""
    nuits = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    personnes = df["adults"] + df["children"].fillna(0)
    categorie_inconnue = pd.Series(False, index=df.index)
    for col, connues in CATEGORIES_CONNUES.items():
        categorie_inconnue |= df[col].notna() & ~df[col].isin(connues)
    resultat = {
        # Traitées par le nettoyage
        "children_manquant": df["children"].isna(),
        "prix_aberrant": df["adr"] > ADR_MAX,
        "sejour_sans_nuit": nuits == 0,
        "reservation_vide": personnes == 0,
        "groupe_sur_une_ligne": df["adults"] > ADULTES_MAX,
        # Gardées et signalées (questions au client)
        "enfants_sans_adulte": (df["adults"] == 0) & (personnes > 0),
        "prix_nul_inexplique": (df["adr"] == 0) & (nuits > 0) & (df["market_segment"] != "Complementary"),
        "non_refund_annule": (df["deposit_type"] == "Non Refund") & (df["is_canceled"] == 1),
        "lignes_identiques": df.duplicated(),
        # Jamais vues dans l'historique : doivent rester à 0
        "valeur_negative": (df[COLONNES_POSITIVES] < 0).any(axis=1),
        "categorie_inconnue": categorie_inconnue,
    }
    return {nom: int(masque.sum()) for nom, masque in resultat.items()}


def ecrire_rapport(brut: pd.DataFrame, nettoye: pd.DataFrame, chemin: Path) -> dict:
    """Écrit le rapport de qualité (avant / après nettoyage) au format JSON et le renvoie."""
    avant, apres = controles(brut), controles(nettoye)
    rapport = {
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "lignes": {"avant_nettoyage": len(brut), "apres_nettoyage": len(nettoye)},
        "periode": [str(brut["arrival_date"].min().date()), str(brut["arrival_date"].max().date())],
        "taux_annulation": {"avant_nettoyage": round(float(brut["is_canceled"].mean()), 4),
                            "apres_nettoyage": round(float(nettoye["is_canceled"].mean()), 4)},
        "controles": {nom: {"avant": avant[nom], "apres": apres[nom], "traitee": nom in TRAITEES}
                      for nom in avant},
        "manquants_apres_nettoyage": {col: int(n) for col, n in nettoye.isna().sum().items() if n},
    }
    chemin.write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")
    return rapport
