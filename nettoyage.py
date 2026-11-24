"""Règles de nettoyage des réservations — Escale Atlantique (mission FastIA).

Une fonction par règle : elle reçoit un DataFrame, renvoie un NOUVEAU DataFrame (jamais modifié en place)
et le nombre de lignes qu'elle a touchées. `nettoyer()` les enchaîne et produit un compte rendu.

⚠️ `train.py` ne charge que les colonnes utiles au modèle (voir sa requête SQL). Une règle qui a besoin
d'une autre colonne impose de l'ajouter à la requête.
"""

import pandas as pd


# --- Exemple fourni : une règle, sa justification, son test (tests/test_nettoyage.py) -------------------

def imputer_enfants_manquants(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """`children` manquant → 0.

    Justification : quelques lignes seulement, et une réservation sans enfant renseigné est,
    de loin, le cas le plus fréquent. Décision réversible : la valeur d'origine est perdue,
    mais le compte rendu garde la trace du nombre de lignes concernées.
    """
    manquants = df["children"].isna()
    out = df.copy()
    out.loc[manquants, "children"] = 0
    return out, int(manquants.sum())


# --- Règles de la tâche 4 (décisions justifiées dans notebooks/01_audit.ipynb, tâche 3) ----------------

ADR_MAX = 1000      # € par nuit : le prix suivant le plus élevé de la base est 508 €
ADULTES_MAX = 10    # au-delà, la ligne est une option de groupe, pas une réservation


def supprimer_prix_aberrants(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """`adr` > ADR_MAX → ligne supprimée.

    Justification : une seule ligne (5 400 €), dix fois au-dessus de tous les autres prix.
    La corriger (54 € ?) serait une supposition ; la supprimer ne coûte rien.
    """
    aberrant = df["adr"] > ADR_MAX
    return df[~aberrant].copy(), int(aberrant.sum())


def supprimer_sejours_sans_nuit(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """0 nuit en semaine et 0 nuit en week-end → ligne supprimée.

    Justification : le modèle prédit l'annulation d'un séjour à l'hôtel ; sans nuit, ce n'en est pas un
    (571 lignes, toutes à prix nul). Question posée au client : location de chambres à la journée ?
    """
    sans_nuit = (df["stays_in_weekend_nights"] + df["stays_in_week_nights"]) == 0
    return df[~sans_nuit].copy(), int(sans_nuit.sum())


def supprimer_reservations_vides(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Aucun adulte, aucun enfant (ni bébé si la colonne est chargée) → ligne supprimée.

    Justification : une réservation pour personne est une saisie ratée (113 lignes).
    `train.py` ne charge pas `babies` : dans la base, aucune ligne n'a de bébé sans adulte ni enfant,
    le résultat est donc le même avec ou sans cette colonne.
    Les réservations avec seulement des enfants sont gardées (question au client).
    À appliquer après `imputer_enfants_manquants` (un `children` manquant compterait sinon comme personne).
    """
    personnes = df["adults"] + df["children"].fillna(0)
    if "babies" in df.columns:
        personnes = personnes + df["babies"]
    vide = personnes == 0
    return df[~vide].copy(), int(vide.sum())


def supprimer_groupes_sur_une_ligne(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """`adults` > ADULTES_MAX → ligne supprimée.

    Justification : 12 lignes de 20 à 55 adultes, toutes annulées, toutes à prix nul : des options de
    groupe posées puis libérées, pas des séjours.
    """
    groupe = df["adults"] > ADULTES_MAX
    return df[~groupe].copy(), int(groupe.sum())


# Ordre d'application : l'imputation d'abord, pour que `supprimer_reservations_vides` voie des 0 et non des NaN.
REGLES = [
    imputer_enfants_manquants,
    supprimer_prix_aberrants,
    supprimer_sejours_sans_nuit,
    supprimer_reservations_vides,
    supprimer_groupes_sur_une_ligne,
]


def nettoyer(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Applique toutes les règles dans l'ordre.

    Renvoie le DataFrame nettoyé et un compte rendu : une ligne par règle,
    avec le nombre de lignes touchées et le nombre de lignes restantes.
    """
    compte_rendu = []
    for regle in REGLES:
        df, touchees = regle(df)
        compte_rendu.append({"regle": regle.__name__, "lignes_touchees": touchees, "lignes_restantes": len(df)})
    return df, pd.DataFrame(compte_rendu)
