#!/bin/bash
# Run the archivetweets management command, or cron it up as:
#
# /home/apps/sites/buzz/scripts/archivetweets-prd.sh >> /home/apps/log/buzz/archivetweets.log 2>&1

echo "[`date`] Starting archive tweets"
 
source /home/apps/env/buzz/bin/activate

cd /home/apps/sites/buzz

python -u manage.py archivetweets --days=7 \
--pythonpath=/home/apps/sites/buzz \
--settings=core.settings.prd

echo "[`date`] Ending archive tweets"

