# Woche 09: Alert-Runbook (Weather-Dashboard)

Die Alarme werden in Prometheus unter `http://localhost:9090/alerts` angezeigt.
`Pending` bedeutet, dass die Bedingung erst seit kurzer Zeit gilt; `Firing`
bedeutet, dass sie für die volle `for`-Dauer bestand. Ohne Alertmanager
ist damit **noch keine E-Mail-, Push- oder Chat-Benachrichtigung** eingerichtet.

## WeatherDashboardDown

1. Prüfe Prometheus **Targets** (`http://localhost:9090/targets`): Steht `web:8000` auf DOWN?
2. Prüfe `docker compose ps` und `docker compose logs --tail=100 web`.
3. Teste `curl -f http://localhost:8000/health` lokal auf dem Host.
4. Überprüfe Docker-Netzwerk, DNS und den `/metrics`-Endpunkt; starte nur betroffene Container neu.
5. Falls ein Deployment unmittelbar vorausging, prüfe den letzten Change und den Rollback-Pfad.

## WeatherHighErrorRate

1. Bestätige die 5xx-Quote in Grafana und die Zahl der Requests im selben Zeitfenster.
2. Prüfe `docker compose logs --tail=100 web` auf 500/502/503 und Timeouts.
3. Unterscheide Datenbankprobleme (`/ready`) von Ausfällen externer Wetter-/Location-APIs.
4. Prüfe die Abhängigkeiten und reduziere bei Bedarf die Anfragelast oder aktiviere einen Rollback.

## WeatherHighLatencyP95

1. Kontrolliere das p95-Panel je Route und den gleichzeitigen Traffic.
2. Prüfe Container-CPU/RAM mit `docker stats` und Logs auf langsame Requests.
3. Untersuche Datenbankzugriffe und Latenzen bei externen Providern separat.
4. Falls nötig: Last reduzieren und problematische neue Änderungen zurückrollen.

## WeatherStaleCacheFallback

1. Prüfe das Symptom mit `increase(weather_stale_cache_responses_total[10m])` in Prometheus.
2. Rufe `/api/weather?latitude=46.85&longitude=9.53` ab und kontrolliere `meta.stale`.
3. Sieh in die Web-Logs und untersuche Erreichbarkeit, Rate-Limits und Fehler bei Open-Meteo.
4. Prüfe, ob die Daten im Cache alt und trotzdem für Benutzer noch vertretbar sind.
5. Nach Wiederherstellung des Providers kontrolliere, ob neue Antworten wieder `meta.stale=false` liefern.
6. Der Alarm gilt nur bei **mindestens drei stale Fallbacks in zehn Minuten für weitere zwei Minuten**; bei keiner Nutzung kann der Provider ausfallen, ohne diesen Alarm auszulösen.
