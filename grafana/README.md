# Woche 09 – Grafana

Grafana wird über `compose.yaml` gestartet und lädt die Datenquelle und das
Dashboard `Weather Dashboard Overview` automatisch. Prometheus bleibt der
Datenlieferant. Zugang nur lokal über `http://localhost:3000`.

Die fünf Panels sind: **Request-Rate**, **HTTP 5xx-Anteil**, **p95-Latenz**,
**Scrape-UP** und **p95-Latenz nach Route** (eigenes Panel).
Die konkreten Normalbereiche und Eingriffsschwellen müssen nach Lasttests
mit echten Messwerten in `MONITORING.md` dokumentiert werden; sie sind hier
nicht vorgetäuscht.

Grafana-Zugang: Benutzer `admin`, Passwort über `GRAFANA_ADMIN_PASSWORD` in
der lokalen `.env`. Die Datei `.env` ist in `.gitignore` ausgeschlossen.
Beim erstmaligen Einrichten wird das Passwort im persistenten Grafana-Volume
angelegt. Ein späteres Ändern der Umgebungsvariable setzt den gespeicherten
Admin-Login **nicht** automatisch zurück.

**Hinweis:** Leere p95-Panels sind zu Beginn ohne HTTP-Last normal; nach
mehreren Requests und zwei Scrapes (15-s-Intervall) werden Daten sichtbar.
Die 5xx-Rate zeigt bei Traffic ohne Serverfehler `0`, statt `No data`.
