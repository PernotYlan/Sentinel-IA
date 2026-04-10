#!/bin/bash

# PROD: entrainement toutes les 2 semaines (IF a 2h, AE a 3h pour eviter conflit sur la table events)
CRON_AE="0 3 */14 * * cd /app && /usr/local/bin/python3 train/train_ae.py >> /app/ae_train.log 2>&1"
CRON_IF="0 2 */14 * * cd /app && /usr/local/bin/python3 train/train_if.py >> /app/if_train.log 2>&1"

# DEV: entrainement toutes les 2 minutes pour test (commenter les lignes PROD et decommenter celles-ci)
# CRON_AE="*/2 * * * * cd /app && /usr/local/bin/python3 train/train_ae.py >> /app/ae_train.log 2>&1"
# CRON_IF="*/2 * * * * cd /app && /usr/local/bin/python3 train/train_if.py >> /app/if_train.log 2>&1"

(crontab -l 2>/dev/null | grep -qF "train_ae.py") || (crontab -l 2>/dev/null; echo "$CRON_AE") | crontab -
(crontab -l 2>/dev/null | grep -qF "train_if.py") || (crontab -l 2>/dev/null; echo "$CRON_IF") | crontab -

# Demarrer le service cron
service cron start

# Lancer Sentinel
exec python3 main.py
