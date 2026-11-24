# Note — Nettoyage des données de réservation

**À :** service réservations et DSI d'Escale Atlantique

**De :** Sadi · **Date :** 24 novembre 2026

## Ce que j'ai fait

J'ai audité les 78 703 réservations sur lesquelles le modèle d'annulation a appris. J'ai écarté 661 saisies impossibles (0,8 %) : des séjours sans nuit, des réservations sans personne, un prix à 5 400 € et des options de groupe saisies sur une seule ligne. J'ai ensuite réentraîné le modèle (v2.1) et l'ai comparé à la version actuelle (v2) sur les mêmes réservations de test.

## Ce que ça change

**Pour le modèle : rien de mesurable en performance.** Nous avons évalué les deux versions sur les mêmes 19 911 réservations des quatre derniers mois (septembre → décembre 2016), telles qu'elles sont enregistrées. Le score est identique : 0,734 pour la v2, 0,733 pour la v2.1. Les deux versions repèrent 3 annulations sur 4 et ont raison 7 fois sur 10 quand elles annoncent une annulation. Elles ne prennent une décision différente que sur 129 réservations (0,6 %).

**Pour le service réservations :**

- **Mêmes réponses** pour la quasi-totalité des réservations.
- **Moins fiables** : les séjours sans nuit et les réservations sans personne. La v2.1 n'en a jamais vu, et elle en annonce 1 sur 5 comme annulées alors que seules 4 % le sont. Nous proposons de les signaler comme « hors du champ du modèle » au lieu de les prédire.
- **Toujours mal traitées** : les réservations à acompte non remboursable. Le modèle les annonce toutes comme annulées, parce que c'est ce que montre l'historique (99 %). Si ces lignes ne sont pas de vraies réservations, un client qui a réellement payé un acompte non remboursable sera à tort signalé comme probable annulation. C'est l'objet de la première question ci-dessous.

**Le vrai gain est la transparence.** Nous pouvons maintenant dire précisément sur quelles données le modèle a appris. Les règles sont écrites et testées, chaque entraînement produit un rapport de qualité, et un contrôle automatique nous alerte si une anomalie nouvelle apparaît dans la base.

## Les questions à poser au client

1. **Les acomptes non remboursables.** 10 461 réservations, annulées à 99 %, presque toutes des groupes ou des agences, réservées très tôt. S'agit-il de vrais acomptes encaissés, ou de blocs de chambres posés par des agences puis libérés ? *En attendant : lignes gardées telles quelles ; le modèle continue de les prédire comme annulées.*
2. **Les lignes identiques.** 22 999 réservations (29 %) sont identiques à une autre. Une ligne correspond-elle à une chambre ? Pouvez-vous nous fournir un numéro de dossier ou de groupe ? *En attendant : gardées, considérées comme des chambres distinctes d'un même groupe.*
3. **Les séjours à 0 €.** 471 séjours non offerts ont un prix nul, surtout des groupes et des agences. Le tarif est-il facturé ailleurs (contrat, note globale) ? *En attendant : gardés.*
4. **Les séjours sans nuit.** 571 réservations n'ont aucune nuit. Louez-vous des chambres à la journée ? Faut-il que le modèle les prédise ? *En attendant : écartées de l'apprentissage.*
5. **Les réservations sans adulte.** 160 réservations ne comptent que des enfants, surtout via des agences en ligne. Le nombre d'adultes est-il bien transmis par les agences ? *En attendant : gardées.*

## Ma recommandation

**Mettre la v2.1 en service à la place de la v2, à une condition, et garder la v2 en secours.**

- Ses performances sont les mêmes, mais ses données sont connues, documentées et contrôlées : c'est la version dont nous pouvons répondre.
- **La condition** : l'API de prédiction doit refuser ou signaler les réservations hors du champ du modèle (aucune personne, aucune nuit, plus de 10 adultes, prix supérieur à 1 000 €). Sans ce filtre, la v2.1 fait légèrement moins bien que la v2 sur ces cas rares.
- **La v2 reste archivée** pour pouvoir revenir en arrière immédiatement si besoin.
- **Le vrai progrès viendra des réponses aux questions 1 et 2.** À elles deux, elles concernent près d'un tiers des réservations. Selon les réponses, une v2.2 pourra traiter les acomptes non remboursables et les lignes identiques, et c'est là que nous attendons un effet réel sur la qualité des prédictions.
