# 🛡️ SENTINEL AI

![Status](https://img.shields.io/badge/status-WIP%20%F0%9F%9A%A7-orange)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Phase](https://img.shields.io/badge/phase-Avant--Projet-blue)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-streaming-231F20?logo=apacheKafka&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-dashboard-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-containers-2496ED?logo=docker&logoColor=white)

> **Plateforme de détection réseau intelligente par IA — souveraine, accessible, pédagogique.**

SENTINEL AI est une plateforme de détection d'intrusions réseau (NDR) alimentée par l'intelligence artificielle. Elle a été conçue pour répondre à un manque structurel du marché français : les PME, ETI et collectivités n'ont aujourd'hui accès à aucune solution de cybersécurité réseau souveraine, abordable et lisible. SENTINEL AI y répond.

---

## 🚧 Statut du projet

Ce dépôt est en cours de construction active. Nous sommes actuellement en **phase d'avant-projet (Mars 2026)**.

| Phase | Statut |
|---|---|
| Avant-projet & faisabilité | ✅ Terminé |
| Cadrage & architecture détaillée | 🔄 En cours |
| Développement V1 | ⏳ Prévu — Juillet 2026 |
| Livraison V1 | 🎯 Cible — Mars 2027 |

---

## 🎯 Objectif

La plupart des solutions de détection réseau existantes sont soit trop complexes, soit réservées aux grandes entreprises (Darktrace, Vectra AI, Sophos NDR — souvent > 100 000 €/an), soit hébergées à l'étranger et soumises à des législations incompatibles avec le RGPD (CLOUD Act américain).

SENTINEL AI vise à offrir :

- 🔍 Une **détection proactive** des intrusions, malwares et comportements anormaux en temps réel
- 🧠 Un **moteur IA** entraîné sur des datasets de trafic réseau réels et diversifiés
- 📊 Un **dashboard simplifié** lisible sans expertise en cybersécurité
- 🇫🇷 Une solution **100 % souveraine**, hébergeable sur infrastructure française
- 💶 Un modèle **SaaS accessible** aux PME (budget 8 000 – 25 000 €/an)

---

## 🏗️ Architecture technique
```
Infrastructure Client
        │
        ▼
Network Sensors (Suricata, Zeek, Packetbeat)
        │
        ▼
Log & Telemetry Pipeline (Apache Kafka, Logstash, Filebeat)
        │
        ▼
Feature Engineering (Python, pandas, Spark)
        │
        ▼
ML Detection Layer (Isolation Forest, XGBoost, Autoencoder)
        │
        ▼
Threat Correlation Engine (Elasticsearch, graph analysis)
        │
        ▼
AI Security Analyst (LLM — Mistral / Llama)
        │
   ┌────┴────┐
   ▼         ▼
SOC Dashboard    SOAR — Réponse Automatisée
(Grafana/Kibana)  (StackStorm, Cortex)
```

### Stack principale

| Composant | Technologies |
|---|---|
| **Capteurs réseau** | Suricata, Zeek, Packetbeat |
| **Pipeline de données** | Apache Kafka, Logstash, Filebeat |
| **Feature engineering** | Python, pandas, numpy, Apache Spark |
| **Modèles ML** | Isolation Forest, XGBoost, Autoencoder (PyTorch / scikit-learn) |
| **Corrélation** | Elasticsearch, analyse de graphes |
| **Analyste IA** | LLM (Mistral, Llama) |
| **Dashboard** | React / Vue.js + FastAPI / Go |
| **Orchestration** | Docker, microservices |
| **SOAR** | StackStorm, Cortex + TheHive |

---

## 🎓 Dimension pédagogique

SENTINEL AI est aussi un **projet pédagogique**. Une partie du développement est confiée à des étudiants de l'**École Limayrac** (Toulouse) — niveaux BTS, Bachelor, Mastère — via un concours organisé par **SYNJ**.

- Les missions sont **rémunérées** sous forme de dotations (jusqu'à 150 € par mission)
- Les étudiants travaillent sur de vrais livrables industriels, validés par Interface Numérique
- C'est une **première expérience professionnelle concrète** en cybersécurité

👉 Tu es étudiant à Limayrac ? [Consulte les missions ouvertes](#) *(lien à venir)*

---

## 🤝 Partenaires

| Partenaire | Rôle |
|---|---|
| [**Interface Numérique**](https://www.maintenance-informatique-et-reseaux.com/) | Maître d'œuvre — Architecture, développement, intégration |
| [**SYNJ**](https://synj.fr) | Organisation du concours étudiant — Coordination, briefs, jury |
| [**École Limayrac**](https://www.limayrac.fr/) | Partenaire pédagogique — Communication et contributions étudiantes |

---

## 📁 Structure du dépôt *(à venir)*
```
sentinel-ai/
├── agents/          # Capteurs réseau légers (Linux / Windows)
├── pipeline/        # Ingestion et normalisation des données
├── ml/              # Modèles de détection IA
├── api/             # Backend FastAPI / Go
├── dashboard/       # Frontend React
├── soar/            # Modules de réponse automatisée
├── docs/            # Documentation technique et utilisateur
└── datasets/        # Données d'entraînement (anonymisées)
```

---

## 🚀 Lancer le projet *(à venir)*

> La documentation d'installation sera disponible à partir de la phase de développement (Juillet 2026).
```bash
# Cloner le dépôt
git clone https://github.com/interface-numerique/sentinel-ai.git
cd sentinel-ai

# Lancer l'environnement de développement
docker compose up -d
```

---

## 📜 Licence

Ce projet est **propriétaire** — développé et détenu par **Interface Numérique**.  
Le code source n'est pas public. L'accès est réservé aux parties prenantes du projet.  
Les contributions étudiantes font l'objet d'une cession de droits explicite.  
Consultez le fichier [LICENSE](./LICENSE) pour plus d'informations.

---

## 📬 Contact

Pour toute question sur le projet : **contact@interface-numerique.net**  
Pour le concours étudiant : contacter **SYNJ** via l'École Limayrac.

---

*SENTINEL AI — Interface Numérique × SYNJ × École Limayrac — Mars 2026*
