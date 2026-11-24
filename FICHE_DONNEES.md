# Fiche du jeu de données — Réservations Escale Atlantique (nettoyées)

## En une phrase

L'historique des réservations des deux hôtels Escale Atlantique, nettoyé de ses saisies impossibles, sur lequel est entraîné le modèle de prédiction d'annulation **v2.1.0** (`model/cancellation_model_v2.1.0.joblib`).

## Origine

| | |
|---|---|
| Source | Base PostgreSQL du projet, table `reservations` jointe à `hotels` (pour le code de l'hôtel). Les données proviennent du système de réservation des deux établissements : Escale Atlantique Centre (Lisbonne, urbain) et Escale Atlantique Océan (Algarve, resort). Il s'agit d'un extrait de *Hotel Booking Demand* (N. Antonio, A. de Almeida, L. Nunes, 2019, *Data in Brief* 22, licence CC BY 4.0) ; les noms des établissements sont fictifs. |
| Période | Arrivées du **1er juillet 2015 au 31 décembre 2016** (18 mois). |
| Nombre de réservations | **78 703** avant nettoyage, **78 042** après (−661, soit −0,8 %). |
| Mise à jour | Historique figé : il est chargé une fois, au premier démarrage de la base (`db/init/`). Aucune mise à jour automatique. La fréquence et le responsable des mises à jour en production restent à définir avec le client. |

## Contenu

Le modèle utilise 15 colonnes (une ligne = une réservation), plus la date d'arrivée pour le découpage dans le temps et la réponse à prédire.

| Colonne | Ce qu'elle signifie pour l'hôtel |
|---|---|
| `hotel` | L'établissement : `City Hotel` (Lisbonne) ou `Resort Hotel` (Algarve). |
| `arrival_date_month` | Le mois d'arrivée prévu (saisonnalité). |
| `market_segment` | Le canal commercial : agence en ligne, agence ou tour-opérateur classique, groupe, direct, entreprise, séjour offert, aviation. |
| `deposit_type` | L'acompte demandé : aucun, non remboursable, remboursable. |
| `customer_type` | Le type de client : individuel, individuel lié à un groupe, contrat, groupe. |
| `country` | Le pays d'origine du client (code à 3 lettres). |
| `lead_time` | Le nombre de jours entre la réservation et l'arrivée. |
| `stays_in_weekend_nights` | Le nombre de nuits de vendredi et samedi. |
| `stays_in_week_nights` | Le nombre de nuits du dimanche au jeudi. |
| `adults` | Le nombre d'adultes. |
| `children` | Le nombre d'enfants (hors bébés). |
| `adr` | Le prix moyen par nuit, en euros. |
| `previous_cancellations` | Le nombre de réservations annulées auparavant par ce client. |
| `total_of_special_requests` | Le nombre de demandes particulières (lit bébé, étage, vue…). |
| `required_car_parking_spaces` | Le nombre de places de parking demandées. |
| `arrival_date` | La date d'arrivée prévue (utilisée pour séparer l'entraînement du test, pas comme variable du modèle). |
| `is_canceled` | **La réponse à prédire** : 1 si la réservation a été annulée (ou si le client ne s'est pas présenté), 0 sinon. 36,4 % des réservations après nettoyage. |

La base contient d'autres colonnes, que le modèle **ne charge pas**. Certaines trahiraient la réponse, comme `reservation_status`, `reservation_status_date` ou `assigned_room_type`. Les autres ne sont pas connues de l'API de réservation : `babies`, `meal`, `agent`, `company`, etc.

## Traitements appliqués

| Règle | Lignes concernées | Pourquoi |
|---|---|---|
| Enfants manquants mis à 0 | 4 | Quatre lignes ; 0 enfant est de loin le cas le plus fréquent. |
| Prix supérieur à 1 000 € par nuit supprimé | 1 | Une ligne à 5 400 €, dix fois au-dessus de tous les autres prix : erreur de saisie. |
| Séjour sans aucune nuit supprimé | 571 | Ce n'est pas un séjour à l'hôtel ; toutes ces lignes ont un prix nul. |
| Réservation sans aucune personne supprimée | 77 (113 au total, dont 36 déjà retirées par la règle précédente) | Une réservation pour personne est une saisie ratée. |
| Plus de 10 adultes sur une ligne supprimé | 12 | Options de groupe (toutes annulées, à prix nul), pas des réservations. |

Rejouables avec `python train.py` ; détail dans `nettoyage.py`, justification dans `notebooks/01_audit.ipynb` (tâche 3). Chaque entraînement écrit aussi un rapport de qualité avant/après nettoyage (`model/quality_report_v2.1.0.json`). Le test `tests/test_qualite.py` échoue si une anomalie nouvelle apparaît dans la base.

## Limites connues

- **Acomptes non remboursables** : 10 461 réservations, annulées à 99,2 %. Elles sont **gardées** en attendant le client : ce sont peut-être des blocs de chambres posés par des agences, pas de vraies réservations. Le modèle apprend donc « non remboursable ⇒ annulé » et le prédit pour 100 % de ces cas.
- **Lignes identiques** : 22 999 lignes (29 %) sont identiques à une autre ligne. Elles sont **gardées**, car sans identifiant client ni numéro de chambre, on ne distingue pas une erreur d'une réservation de groupe (une ligne par chambre). Les groupes et les agences pèsent donc probablement plus que leur poids réel dans l'apprentissage.
- **Prix nul sans explication** : 406 séjours restants ont des nuits, ne sont pas offerts et ont un prix nul. Ils sont gardés en attendant le client.
- **Enfants sans adulte** : 160 réservations, gardées (probablement un nombre d'adultes non transmis par les agences en ligne).
- **Hors du domaine du modèle** : les séjours sans nuit et les réservations vides ont été retirés. Si l'API en reçoit, le modèle répondra quand même, sans base fiable : il faut les filtrer à l'entrée.
- **Représentativité** : seulement deux hôtels, au Portugal, sur 18 mois (2015-2016), avec une clientèle portugaise à 45 %. Rien ne garantit que les comportements d'annulation soient les mêmes aujourd'hui ou ailleurs.
- **Colonnes non contrôlées** : le nettoyage ne porte que sur les colonnes utilisées par le modèle. Les anomalies vues sur les autres (bébés à 9 ou 10, dates de départ incohérentes) sont signalées mais non corrigées.

## Données personnelles

Le jeu ne contient **ni nom, ni adresse, ni e-mail, ni téléphone, ni numéro de carte**. Il contient en revanche des informations sur des personnes :
- la **nationalité** (`country`) ;
- la **composition du groupe** (adultes, enfants, bébés) ;
- les **dates de séjour** ;
- les **demandes particulières** et le parking ;
- l'**historique d'annulation** du client ;
- des numéros d'agence et d'entreprise.

Croisées entre elles (hôtel, date d'arrivée, pays, nombre d'enfants), ces informations peuvent permettre de reconnaître une famille. Le jeu est donc **pseudonymisé, pas anonyme**, et reste soumis au RGPD dès qu'il s'agit des données réelles du client.

Accès : base PostgreSQL **locale** (conteneur Docker), réservée à l'équipe FastIA de la mission. Les identifiants sont dans le fichier `.env`, à ne jamais versionner ni réutiliser ailleurs. Le modèle entraîné ne contient pas les réservations elles-mêmes, seulement des paramètres : des coefficients, la liste des catégories vues et des médianes.
