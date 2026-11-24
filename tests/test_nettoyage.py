"""Tests des règles de nettoyage : un petit DataFrame construit à la main par règle."""

import pandas as pd

import nettoyage
from nettoyage import (
    imputer_enfants_manquants,
    nettoyer,
    supprimer_groupes_sur_une_ligne,
    supprimer_prix_aberrants,
    supprimer_reservations_vides,
    supprimer_sejours_sans_nuit,
)


def reservations(**colonnes) -> pd.DataFrame:
    """Réservations valides par défaut (2 adultes, 2 nuits, 100 €) ; on ne précise que ce qui change."""
    n = len(next(iter(colonnes.values()))) if colonnes else 1
    base = {"adults": [2] * n, "children": [0] * n, "stays_in_weekend_nights": [1] * n,
            "stays_in_week_nights": [1] * n, "adr": [100.0] * n}
    return pd.DataFrame({**base, **colonnes})


def test_imputer_enfants_manquants():
    df = pd.DataFrame({"children": [0, None, 2, None]})

    out, touchees = imputer_enfants_manquants(df)

    assert out["children"].tolist() == [0, 0, 2, 0]
    assert touchees == 2
    assert df["children"].isna().sum() == 2   # l'entrée n'a pas été modifiée


def test_nettoyer_produit_un_compte_rendu():
    df = reservations(children=[None, 1])

    out, compte_rendu = nettoyer(df)

    assert list(compte_rendu.columns) == ["regle", "lignes_touchees", "lignes_restantes"]
    assert len(compte_rendu) == len(nettoyage.REGLES)


def test_supprimer_prix_aberrants():
    df = reservations(adr=[0.0, 100.0, 1000.0, 1000.01, 5400.0])

    out, touchees = supprimer_prix_aberrants(df)

    assert out["adr"].tolist() == [0.0, 100.0, 1000.0]   # le prix nul et la borne elle-même sont gardés
    assert touchees == 2
    assert len(df) == 5


def test_supprimer_sejours_sans_nuit():
    df = reservations(stays_in_weekend_nights=[0, 0, 2, 0], stays_in_week_nights=[0, 3, 0, 0])

    out, touchees = supprimer_sejours_sans_nuit(df)

    assert out.index.tolist() == [1, 2]   # une nuit en semaine OU en week-end suffit
    assert touchees == 2
    assert len(df) == 4


def test_supprimer_reservations_vides():
    df = reservations(adults=[0, 0, 2, 0], children=[0, 2, 0, None])

    out, touchees = supprimer_reservations_vides(df)

    assert out.index.tolist() == [1, 2]   # des enfants sans adulte : gardés (question au client)
    assert touchees == 2                  # children manquant et 0 adulte : personne
    assert len(df) == 4


def test_supprimer_reservations_vides_compte_les_bebes_si_charges():
    df = reservations(adults=[0, 0], children=[0, 0])
    df["babies"] = [0, 1]

    out, touchees = supprimer_reservations_vides(df)

    assert out.index.tolist() == [1]
    assert touchees == 1


def test_supprimer_groupes_sur_une_ligne():
    df = reservations(adults=[1, 10, 11, 55])

    out, touchees = supprimer_groupes_sur_une_ligne(df)

    assert out["adults"].tolist() == [1, 10]   # la borne elle-même est gardée
    assert touchees == 2
    assert len(df) == 4


def test_nettoyer_enchaine_les_regles_dans_l_ordre():
    df = reservations(
        adults=[2, 0, 2, 2, 40, 2],
        children=[None, None, 0, 0, 0, 1],
        stays_in_week_nights=[1, 1, 0, 1, 1, 1],
        stays_in_weekend_nights=[1, 1, 0, 1, 1, 1],
        adr=[100.0, 100.0, 0.0, 5400.0, 0.0, 80.0],
    )

    out, compte_rendu = nettoyer(df)

    assert out.index.tolist() == [0, 5]
    assert out["children"].isna().sum() == 0
    assert compte_rendu["lignes_touchees"].tolist() == [2, 1, 1, 1, 1]
    assert compte_rendu["lignes_restantes"].tolist() == [6, 5, 4, 3, 2]
