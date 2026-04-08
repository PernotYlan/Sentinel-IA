#!/bin/bash

# DEV: entrainement AE toutes les 2 minutes pour test
# //TODO: Ne pas oublier de changer le cron a celui qui est de 2 semaines
CRON_JOB="*/2 * * * * cd /app && /usr/local/bin/python3 train/train_ae.py >> /app/ae_train.log 2>&1"

# PROD: entrainement AE toutes les 2 semaines a 2h du matin (commenter la ligne DEV et decommenter celle-ci)
# CRON_JOB="0 2 */14 * * cd /app && /usr/local/bin/python3 train/train_ae.py >> /app/ae_train.log 2>&1"

(crontab -l 2>/dev/null | grep -qF "train_ae.py") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Demarrer le service cron
service cron start

# Lancer Sentinel
exec python3 main.py
