# MONITORING – Weather Monitoring Dashboard

## 1. Aufbau und Nachweise

- Stack: FastAPI `web:8000`, PostgreSQL, Prometheus (15 s Scrape), Grafana.
- Prometheus: `http://localhost:9090/targets`, Job `weather-dashboard`, erwartet `UP = 1`.
- Grafana: `http://localhost:3000`, provisioniertes Dashboard
  `grafana/dashboards/weather-dashboard-overview.json`.
- Sicherheitsgrenze: Grafana/Prometheus in Compose nur an `127.0.0.1` exponiert.
- Screenshots für die Abgabe: `docs/woche-09/dashboard.png` und
  `docs/woche-09/alert-firing.png` (nach den Tests manuell ablegen).
- **Beobachtungsbasis:** Screenshot des ersten lokalen Testlaufs vom 21.10.2026:
  Request-Rate gegen Ende etwa **0,5 req/s**, p95 gesamt **ca. 4,8 ms**,
  5xx-Anteil **0 %**, `UP=1`. Das ist Last durch Testaufrufe, **kein**
  repräsentativer 30-Tage-Produktivbaseline-Wert.

## 2. Dashboard: fünf Panels

### Panel 1 – Request-Rate

| Feld | Dokumentation |
| --- | --- |
| Metrik | `weather_http_requests_total` |
| PromQL | `sum(rate(weather_http_requests_total[5m]))` |
| Frage | Wie viele HTTP-Anfragen pro Sekunde bearbeitet der Dienst? |
| Normalbereich | Bei dem dokumentierten lokalen Lasttest etwa 0,5 req/s am Ende; im Leerlauf nahe 0. Das ist noch keine belastbare Normalbandbreite. |
| Eingriffsschwelle | Kein pauschaler Wert; Anstieg gegenüber einem später empirisch erhobenen Baseline mit gleichzeitig steigendem p95/5xx prüfen. Allein hoher Traffic ist kein Fehler. |

### Panel 2 – Fehlerrate 5xx

| Feld | Dokumentation |
| --- | --- |
| Metrik | `weather_http_requests_total{status=~"5.."}` und `weather_http_requests_total` |
| PromQL | `(sum(rate(weather_http_requests_total{status=~"5.."}[5m])) or vector(0)) / clamp_min(sum(rate(weather_http_requests_total[5m])), 1e-9)` |
| Frage | Wie gross ist der Anteil gescheiterter HTTP-Anfragen mit Serverfehler? |
| Normalbereich | 0 % im ersten Testlauf; 4xx-Validierungsfehler sind keine 5xx. |
| Eingriffsschwelle | Mehr als 5 % im Fünf-Minuten-Fenster **anhaltend fünf Minuten**; unter kleiner Last zusätzlich absolute Requestzahlen beurteilen. |

### Panel 3 – p95-Latenz gesamt

| Feld | Dokumentation |
| --- | --- |
| Metrik | `weather_http_request_duration_seconds_bucket` |
| PromQL | `histogram_quantile(0.95, sum by (le) (rate(weather_http_request_duration_seconds_bucket[5m])))` |
| Frage | Wie schnell antworten 95 % der HTTP-Anfragen ungefähr? |
| Normalbereich | Im lokalen Test ca. 4,8 ms, überwiegend einfache `/`- und `/health`-Aufrufe; Wetter-Provider-Endpunkte separat beobachten. |
| Eingriffsschwelle | p95 über 1 s während fünf Minuten: Warnalarm, angepasst aus dem Woche-09-Labor. |

### Panel 4 – Target-Verfügbarkeit

| Feld | Dokumentation |
| --- | --- |
| Metrik | `up{job="weather-dashboard"}` |
| PromQL | `up{job="weather-dashboard"}` |
| Frage | Kann Prometheus den Metrics-Endpunkt derzeit abfragen? |
| Normalbereich | `1` im ersten Test, Ziel dauerhaft `1`. |
| Eingriffsschwelle | `0` für eine Minute: `WeatherDashboardDown`; `UP` misst nur Scrape-Erreichbarkeit, nicht erfolgreiches Wetterabrufen. |

### Panel 5 – Eigenes Panel: p95-Latenz je Route

| Feld | Dokumentation |
| --- | --- |
| Metrik | `weather_http_request_duration_seconds_bucket` mit `route`-Label |
| PromQL | `histogram_quantile(0.95, sum by (le, route) (rate(weather_http_request_duration_seconds_bucket{route!="/health",route!="/ready",route!="unmatched"}[5m])))` |
| Frage | Welche konkrete API-Route verursacht hohe Antwortzeiten? |
| Normalbereich | Im bisherigen Test für `/` wenige Millisekunden; Wetterrouten benötigen noch separate Messwerte unter realistischer Last. |
| Eingriffsschwelle | Pro Wetterroute p95 über 1 s prüfen; der globale Alarm allein kann bei sehr wenig Wetter-Traffic unauffällig bleiben. |

## 3. SLOs und Error Budgets (vorgeschlagen, noch nicht über 30 Tage gemessen)

### SLO 1 – Erfolgsrate von Wetter-API-Anfragen

- **SLI:** Anteil der 2xx-Antworten unter den 2xx- und 5xx-Antworten auf
  `/api/weather` und `/api/weather/forecast` (4xx-Benutzereingabefehler ausgeschlossen).
- **SLO:** Mindestens **99,5 %** dieser gültigen API-Anfragen über rollierende 30 Tage
  erfolgreich (HTTP 2xx). Auch Provider-Fehler (502) zählen als Fehler.
- **PromQL (30 Tage):**

  ```promql
  sum(increase(weather_http_requests_total{route=~"/api/weather|/api/weather/forecast",status=~"2.."}[30d]))
  /
  sum(increase(weather_http_requests_total{route=~"/api/weather|/api/weather/forecast",status=~"2..|5.."}[30d]))
  ```

- **Error Budget:** `0,005 × N` Fehl-Requests pro 30 Tage, wobei `N`
  die Anzahl gültiger Requests im Zeitraum ist. Beispiel bei **100'000**
  Requests: `0,005 × 100'000 = 500` erlaubte Fehler. Die tatsächliche
  Requestzahl ist noch nicht bekannt. Die häufig genannten **216 Minuten**
  (`0,5 % × 43'200 min`) wären ein *zeitbasiertes* Budget; dieses SLI ist
  dagegen **requestbasiert**, deshalb gelten 500 Fehl-Requests im Beispiel.
- **Begründung:** Der Dienst hängt von externen Datenquellen ab; vollständige
  Fehlerfreiheit ist unrealistisch. 99,5 % setzt eine messbare Toleranz.
- **Einschränkung:** Alte Cache-Daten können mit HTTP 200 geliefert werden.
  Deshalb ergänzt `WeatherStaleCacheFallback` die HTTP-Fehlerrate.

### SLO 2 – Latenz aller instrumentierten HTTP-Anfragen

- **SLI:** Anteil der gemessenen Requests mit Latenz höchstens **500 ms**,
  basierend auf dem kumulativen Histogramm-Bucket `le="0.5"`.
- **SLO:** Mindestens **95 %** aller gemessenen HTTP-Requests innerhalb
  von **500 ms** über rollierende 30 Tage (einschliesslich Nicht-Wetter-Routen).
- **PromQL (30 Tage):**

  ```promql
  sum(increase(weather_http_request_duration_seconds_bucket{le="0.5"}[30d]))
  /
  sum(increase(weather_http_request_duration_seconds_count[30d]))
  ```

- **Error Budget:** `0,05 × N` langsame Requests über 30 Tage. Beispiel:
  Bei **100'000** instrumentierten Requests sind **5'000** Requests über
  500 ms erlaubt.
- **Begründung:** Schnelle Antworten sind für ein interaktives Dashboard wichtig;
  5 % Budget schützt vor Fehlalarmen bei gelegentlichen externen API-Spitzen.
- **Einschränkung:** `/health` und `/` können den globalen SLI verbessern,
  obwohl Wetterrouten langsam sind. Daher zusätzlich p95 je Route betrachten.

## 4. Alarmierung und Runbooks

Prometheus lädt `prometheus/alert.rules.yml` mit vier Regeln:
`WeatherDashboardDown`, `WeatherHighErrorRate`, `WeatherHighLatencyP95`
(Laborregeln, an FastAPI angepasst) und **eigener Alarm**
`WeatherStaleCacheFallback`:

```yaml
- alert: WeatherStaleCacheFallback
  expr: increase(weather_stale_cache_responses_total[10m]) >= 3
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Weather API is serving stale cached observations"
    description: "At least three stale fallback responses occurred in the last ten minutes. Verify the upstream weather provider."
    runbook: "docs/woche-09/alert-runbook.md#weatherstalecachefallback"
```

Diese Regel ist **symptombasiert**: Nutzer bekommen alte Wetterdaten, wenn
Open-Meteo ausfällt, obwohl der HTTP-Status 200 bleibt. Drei Vorfälle in zehn
Minuten vermeiden die Alarmierung für einen einzelnen sporadischen Ausfall;
`for: 2m` verlangt zusätzlich eine anhaltende Bedingung. Bei keinem Traffic
entsteht kein solcher Alarm. Runbook mit 3–6 Handlungsschritten:
[`docs/woche-09/alert-runbook.md`](docs/woche-09/alert-runbook.md).

**Abnahmetest:** `docker compose stop web`, anschliessend unter
`http://localhost:9090/alerts` `WeatherDashboardDown` nach etwa 1–2 Minuten
im Zustand **Firing** nachweisen, Screenshot `docs/woche-09/alert-firing.png`.
Danach `docker compose start web`, `/health` und `up` kontrollieren.

**Wichtig:** Ohne Alertmanager werden die Alerts in Prometheus angezeigt, aber
es findet keine externe Benachrichtigung statt.

## 5. DevSecOps: Trivy und CI-Security-Gate

### 5.1 Reproduzierbarer Image-Scan

Das tatsächlich ausgelieferte, lokal gebaute FastAPI-Image prüfen:

```bash
docker build -t weather-monitoring-dashboard:week09 .
trivy image --scanners vuln --format table weather-monitoring-dashboard:week09
trivy image --scanners vuln --format json \
  --output docs/woche-09/trivy-results.json weather-monitoring-dashboard:week09
```

Der erste Scan lädt möglicherweise eine umfangreiche CVE-Datenbank. Der Befund
ist zeitabhängig (Basis-Image, pip-Abhängigkeiten, Trivy-Datenbank). Noch liegen
**keine tatsächlichen CVE-Ergebnisse** aus dem lokalen Scan vor. Entsprechend
werden auch keine IDs oder Fixed Versions behauptet. Der JSON-Report wird
lokal erzeugt; für die Abgabe die Bewertung und einen datierten Screenshot/
CI-Artifact beilegen, nicht zwingend den gesamten JSON-Report committen.

### 5.2 Verbindlicher CI-Schwellwert

Die bestehende `.github/workflows/ci.yml` baut nach Lint und Tests das Image
`weather-monitoring-dashboard:ci` und führt zwei Trivy-Schritte aus:

1. Ein SARIF-Report zu `CRITICAL,HIGH` (fixbare Funde) wird als GitHub-Actions-
   Artifact gesichert und auf dem Main-Branch in GitHub Security hochgeladen.
2. **Security-Gate:** Ein behebbarer Fund mit Severity **HIGH oder CRITICAL**
   führt zu `exit-code: 1` und damit zu einem **fehlgeschlagenen CI-Build**.
   Nicht behebbare Funde blockieren dank `ignore-unfixed: true` nicht, müssen
   aber separat geprüft und dokumentiert werden.

Lokale Vorabprüfung mit derselben Gate-Schwelle:

```bash
trivy image --scanners vuln --severity HIGH,CRITICAL \
  --ignore-unfixed --exit-code 1 weather-monitoring-dashboard:week09
```

**Bewusster Trade-off:** Nicht behebbare, aber möglicherweise ausnutzbare
Schwachstellen dürfen die CI nicht kommentarlos passieren: Sie gehören in die
Risikoanalyse und sind regelmässig neu zu prüfen. Es gibt vorerst keine
`.trivyignore`-Ausnahmen. Wenn eine Ausnahme nötig ist, muss sie eine konkrete
CVE, Begründung und ein Wiedervorlagedatum enthalten.

### 5.3 Die drei schwersten CVE-Funde und Kontextbewertung

Die Werte werden **erst nach dem tatsächlichen Trivy-Scan** eingesetzt.
Priorität nach Severity (`CRITICAL` vor `HIGH`, danach `MEDIUM` usw.);
bei Gleichstand Kontext und vorhandene Fixes berücksichtigen.

| CVE | Paket / Version | Severity | Fixed Version | Kontext in dieser FastAPI-App | Entscheidung |
| --- | --- | --- | --- | --- | --- |
| Noch zu scannen | | | | | |
| Noch zu scannen | | | | | |
| Noch zu scannen | | | | | |

Bewertungsfragen pro CVE: Ist die betroffene Bibliothek im Laufzeit-Image?
Kann externe Eingabe über einen der API-Endpunkte die verwundbare Funktion
beeinflussen? Ist ein Fix verfügbar? Der Webprozess läuft mit `USER appuser`
(UID 10001), was Rechte reduziert, die Ausnutzbarkeit aber **nicht ausschliesst**.

### 5.4 Secret-Hygiene und Git-Historie

Die Projekt-`.gitignore` schliesst `.env`/`.env.*` aus; die
`terraform/.gitignore` schliesst `.tfvars` und `.tfstate` aus.
**Ein Ignore-Eintrag beweist jedoch nicht, dass die Datei niemals committed war.**
Die folgenden Prüfungen müssen noch am tatsächlichen Git-Repository durchgeführt
und das Resultat hier dokumentiert werden:

```bash
git ls-files -- .env terraform/terraform.tfvars terraform/terraform.tfstate
git log --all --format='%h %s' -- \
  .env terraform/terraform.tfvars terraform/terraform.tfstate
```

Erwartung: Beide Befehle ohne Treffer. Bei Treffern: Werte auf reale Secrets
prüfen, betroffene Credentials **rotieren** und die versehentliche Veröffentlichung
über die Git-Historie und weitere Exporte untersuchen. Das Entfernen einer Datei
im nächsten Commit macht bereits veröffentlichte Werte nicht wieder geheim.

### 5.5 Woche-09-Nachweise (noch offen)

- `docs/woche-09/dashboard.png`: alle fünf Panels mit tatsächlichen Daten.
- `docs/woche-09/alert-firing.png`: Alarm `WeatherDashboardDown` auf `Firing`.
- Trivy-Ausgabe und drei konkrete, bewertete CVEs (oder dokumentiert keine Funde).
- GitHub-Actions-Lauf mit durchlaufenem Trivy-Gate und SARIF-Artifact.
- Ergebnis der Secret-Hygiene-Prüfung in diesem Dokument festhalten.
