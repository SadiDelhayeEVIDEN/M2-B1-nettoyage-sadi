"""Tests des contrôles de qualité, et garde-fou sur la base réelle.

Les tests marqués « base » lisent PostgreSQL : ils sont ignorés (skip) si la base n'est pas joignable.
"""

import os

import pandas as pd
import pytest
from sqlalchemy import create_engine

from nettoyage import nettoyer
from qualite import TRAITEES, controles

# Inventaire de l'audit du 24/11/2026 (notebooks/01_audit.ipynb), sur les colonnes chargées par train.py.
# Si un chiffre augmente, une anomalie est apparue : l'examiner, décider, PUIS mettre l'inventaire à jour.
ANOMALIES_CONNUES = {
    "children_manquant": 4,
    "prix_aberrant": 1,
    "sejour_sans_nuit": 571,
    "reservation_vide": 113,
    "groupe_sur_une_ligne": 12,
    "enfants_sans_adulte": 160,
    "prix_nul_inexplique": 471,
    "non_refund_annule": 10376,
    "lignes_identiques": 24812,
    "valeur_negative": 0,
    "categorie_inconnue": 0,
}


def reservation(**valeurs) -> dict:
    """Une réservation valide ; on ne précise que ce qui change."""
    return {"hotel": "City Hotel", "arrival_date_month": "May", "market_segment": "Online TA",
            "deposit_type": "No Deposit", "customer_type": "Transient", "country": "PRT", "lead_time": 30,
            "stays_in_weekend_nights": 1, "stays_in_week_nights": 2, "adults": 2, "children": 0, "adr": 90.0,
            "previous_cancellations": 0, "total_of_special_requests": 0, "required_car_parking_spaces": 0,
            "is_canceled": 0, **valeurs}


def test_controles_detectent_chaque_anomalie():
    df = pd.DataFrame([
        reservation(),
        reservation(children=None, lead_time=31),
        reservation(adr=5400.0),
        reservation(stays_in_weekend_nights=0, stays_in_week_nights=0),
        reservation(adults=0),
        reservation(adults=40, lead_time=32),
        reservation(adults=0, children=2),
        reservation(adr=0.0, lead_time=33),
        reservation(deposit_type="Non Refund", is_canceled=1),
        reservation(lead_time=-1),
        reservation(hotel="Hôtel inconnu"),
        reservation(),   # identique à la première ligne
    ])

    resultat = controles(df)

    assert resultat == {nom: 1 for nom in ANOMALIES_CONNUES}


def test_chaque_controle_a_une_reference():
    df = pd.DataFrame([reservation()])

    assert set(controles(df)) == set(ANOMALIES_CONNUES)


@pytest.fixture(scope="module")
def base() -> pd.DataFrame:
    import train   # charge le .env

    try:
        return train.load_data(create_engine(os.environ["DATABASE_URL"]))
    except Exception as erreur:   # base arrêtée, .env absent…
        pytest.skip(f"base de réservations indisponible : {erreur}")


def test_base_aucune_anomalie_nouvelle(base):
    resultat = controles(base)

    en_hausse = {nom: f"{ANOMALIES_CONNUES[nom]} → {n}" for nom, n in resultat.items() if n > ANOMALIES_CONNUES[nom]}

    assert not en_hausse, f"anomalies nouvelles dans la base, à examiner avant d'entraîner : {en_hausse}"


def test_base_le_nettoyage_elimine_les_anomalies_traitees(base):
    nettoye, _ = nettoyer(base)

    resultat = controles(nettoye)

    assert {nom: resultat[nom] for nom in TRAITEES} == {nom: 0 for nom in TRAITEES}
