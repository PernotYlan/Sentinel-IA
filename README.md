# Sentinel-IA

![Status](https://img.shields.io/badge/status-PreProd-orange)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-containers-2496ED?logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-ingestion-FF4438?logo=redis&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-ML-189fdd)
![TensorFlow](https://img.shields.io/badge/TensorFlow-Keras-FF6F00?logo=tensorflow&logoColor=white)

> Plateforme de détection d'anomalies réseau par apprentissage automatique. Sentinel-IA consomme des logs Zeek et Filebeat via Redis, les analyse en temps réel à travers un pipeline de trois modèles ML, et persiste les résultats dans une base SQLite locale.

---

## Objectif

La plupart des solutions de détection réseau existantes sont soit trop complexes, soit réservées aux grandes entreprises (Darktrace, Vectra AI, Sophos NDR — souvent > 100 000 €/an), soit hébergées à l'étranger et soumises à des législations incompatibles avec le RGPD (CLOUD Act américain).

Sentinel-IA vise à offrir :

- Une détection proactive des intrusions, malwares et comportements anormaux en temps réel
- Un moteur IA entraîné sur le trafic réel du client, affiné toutes les deux semaines
- Une solution 100 % souveraine, hébergeable sur infrastructure française
- Un modèle SaaS accessible aux PME, ETI et collectivités (budget 8 000 – 25 000 €/an)

---

## Architecture

```
Zeek / Filebeat
      |
      v
   Redis (BLPOP)
      |
      v
   parser.py  <-- routing par tags JSON
    /       \
zeek        syslog
  |            |
  v            v
buffer.db   buffer.db
(events)   (unknown_events)
  |
  v
Isolation Forest  -->  XGBoost  -->  Autoencoder
```

Le pipeline ML est séquentiel : XGBoost et Autoencoder ne s'exécutent que sur les événements déjà flaggés par Isolation Forest, ce qui réduit drastiquement les faux positifs.

---

## Modèles ML

### Isolation Forest
- Modèle non supervisé, entraine sur le trafic client
- Attend 30 000 événements Zeek avant le premier entrainement
- Si un modèle existe sur disque (`train/if_model.pkl`), il est chargé immédiatement au démarrage sans attendre les 30k
- Réentraine toutes les 2 semaines via cron

### XGBoost
- Modèle supervisé, pré-entrainé sur NSL-KDD et CICIDS2017
- Ne s'exécute que sur les événements flaggés par Isolation Forest
- Modèle statique : `train/xgb_model.json`

### Autoencoder
- Réseau de neurones entraîné sur le trafic client (architecture 7→16→8→4→8→16→7)
- Détecte les anomalies par reconstruction error vs seuil (mean + 2*std)
- Réentraine toutes les 2 semaines via cron, une heure après IF
- Vide la table `events` après chaque cycle d'entrainement

---

## Persistence et hotswap

Les modèles IF et AE sont sauvegardés sur disque après chaque entrainement. Un watcher `watchdog` surveille les fichiers `.pkl` et `.keras` et recharge les modèles à chaud sans redémarrer Sentinel.

Les données d'entrainement s'accumulent dans `buffer.db` (SQLite). L'AE vide la table `events` après chaque cycle — IF et AE s'entrainent donc sur les mêmes données, sans doublon.

---

## Structure du dépôt

```
sentinel-ia/
├── main.py               # Point d'entrée
├── entrypoint.sh         # Setup cron + lancement
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── env.py            # Lecture config Redis
│   ├── redis.py          # Connexion + boucle BLPOP
│   ├── parser.py         # Routing Zeek / syslog, fenetre glissante
│   ├── db.py             # SQLite : init, store, dump, flush
│   ├── features.py       # Extraction et encodage des features
│   ├── model_if.py       # Isolation Forest : init, watchdog, scoring
│   ├── model_xgb.py      # XGBoost : chargement, scoring
│   └── model_ae.py       # Autoencoder : init, watchdog, scoring
└── train/
    ├── train_if.py        # Script entrainement IF (appelé par cron)
    ├── train_ae.py        # Script entrainement AE (appelé par cron)
    └── train_xgb.py       # Script entrainement XGBoost sur datasets publics
```

---

## Lancer le projet

Prérequis : Docker, Docker Compose, accès à un Redis recevant des logs Zeek/Filebeat.

```bash
git clone https://github.com/PernotYlan/Sentinel-IA.git
cd Sentinel-IA
chmod +x entrypoint.sh
docker compose build
docker compose run sentinel
```

Au premier lancement, Sentinel demande interactivement l'hôte et le port Redis.
La configuration est sauvegardée dans `.env` et réutilisée aux lancements suivants.

---

## Crons

| Modele | Frequence (PROD) | Heure |
|--------|-----------------|-------|
| Isolation Forest | toutes les 2 semaines | 2h00 |
| Autoencoder | toutes les 2 semaines | 3h00 |

Pour passer en mode DEV (entrainement toutes les 2 minutes), commenter les lignes PROD dans `entrypoint.sh` et décommenter les lignes DEV.

---

## Stack technique

| Composant | Technologie |
|-----------|------------|
| Ingestion | Redis (BLPOP) |
| Capteurs | Zeek, Filebeat |
| ML | scikit-learn, XGBoost, TensorFlow/Keras |
| Persistence | SQLite, pickle |
| Hotswap | watchdog |
| Conteneurisation | Docker, Docker Compose |
| Cron | cron (dans le conteneur) |

---

## Dimension pédagogique

Sentinel-IA est aussi un projet pédagogique. Une partie du développement est confiée à des étudiants de l'**École Limayrac** (Toulouse) — niveaux BTS, Bachelor, Mastère — via un concours organisé par **SYNJ**.

- Les missions sont rémunérées sous forme de dotations (jusqu'à 150 € par mission)
- Les étudiants travaillent sur de vrais livrables industriels, validés par Interface Numérique
- C'est une première expérience professionnelle concrète en cybersécurité

Tu es étudiant à Limayrac ? Consulte les missions ouvertes *(lien à venir)*

---

## Partenaires

| Partenaire | Role |
|---|---|
| [Interface Numérique](https://www.maintenance-informatique-et-reseaux.com/) | Maitre d'oeuvre — Architecture, développement, intégration |
| [SYNJ](https://synj.fr) | Organisation du concours étudiant — Coordination, briefs, jury |
| [École Limayrac](https://www.limayrac.fr/) | Partenaire pédagogique — Communication et contributions étudiantes |

---

## Equipe

| Nom | Role |
|-----|------|
| Ylan.P | Dev |
| Thierry.B | Dev |

---

## Licence

Projet propriétaire — développé par Interface Numérique.
Le code source n'est pas public. L'accès est réservé aux parties prenantes du projet.
Consultez le fichier [LICENSE](./LICENSE) pour plus d'informations.

---

## Contact

Pour toute question sur le projet : **contact@interface-numerique.net**
Pour le concours étudiant : contacter **SYNJ** via l'École Limayrac.

---

*Sentinel-IA — Interface Numérique x SYNJ x École Limayrac — 2026*
