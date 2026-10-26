#!/usr/bin/env bash
# Send one alert on every channel, retrying each. Succeeds if at least one channel got through.
# Usage: notify.sh "<phone title>" "<phone message>" "<priority>" "<tags>" "<issue title>" <issue body file>
set -u
TITLE=$1; MSG=$2; PRIO=$3; TAGS=$4; ITITLE=$5; IBODY=$6
ok=0
if [ -n "${NTFY_TOPIC:-}" ]; then
  if curl -fsS --retry 6 --retry-delay 10 --retry-all-errors --max-time 30 \
       -H "Title: $TITLE" -H "Priority: $PRIO" -H "Tags: $TAGS" -H "Click: $SITE" -d "$MSG" "https://ntfy.sh/$NTFY_TOPIC" > /dev/null; then
    ok=1; echo "phone notification sent"
  else echo "::warning::ntfy failed after retries"; printf '\n_(The phone notification failed to send; this email is the backup.)_\n' >> "$IBODY"; fi
fi
for i in 1 2 3 4 5; do
  if gh issue create --title "$ITITLE" --body-file "$IBODY" > /dev/null; then ok=1; echo "issue created (emails you)"; break; fi
  echo "issue attempt $i failed"; sleep $((i * 15))
done
[ "$ok" = 1 ] || { echo "::error::every channel failed"; exit 1; }
