# Terraform – Weather Monitoring Dashboard

## Zweck

Diese Terraform-Konfiguration stellt das Weather Monitoring Dashboard als lokalen Docker-Container bereit.

Sie ist Teil des Semesterprojekts im DevOps-Modul (Woche 7: Infrastructure as Code).

Die Infrastruktur wird deklarativ mit Terraform und dem Docker-Provider `kreuzwerker/docker` verwaltet.

## Voraussetzungen

- Docker Engine mit laufendem Docker-Daemon
- Terraform >= 1.5
- Zugriff auf den lokalen Docker-Daemon
- Projektquellcode mit Dockerfile

## Deployment

Die Befehle werden vom Projektstamm aus ausgeführt.

**1. Docker-Image bauen**

```bash
docker build -t weather-dashboard:terraform-local .
```

**2. Terraform initialisieren**

```bash
cd terraform
terraform init
terraform fmt -check
terraform validate
```

**3. Infrastruktur planen und erstellen**

```bash
terraform plan
terraform apply
```

Die Anwendung ist anschliessend unter http://localhost:18080 erreichbar.

**4. Deployment überprüfen**

```bash
curl http://127.0.0.1:18080/health
curl http://127.0.0.1:18080/ready
terraform output
```

Beide HTTP-Endpunkte sollen den Statuscode 200 zurückgeben.

## Konfigurierbare Variablen

| Variable | Typ | Standardwert | Bedeutung |
|---|---|---|---|
| `container_name` | string | `weather-dashboard-terraform` | Name des Docker-Containers |
| `host_port` | number | `18080` | Lokaler Host-Port |

Der Host-Port wird validiert und muss zwischen 1025 und 65535 liegen.

Beispiel für einen abweichenden Port:

```bash
terraform plan -var="host_port=18081"
```

## Outputs

| Output | Bedeutung |
|---|---|
| `app_url` | URL der Anwendung |
| `container_id` | ID des verwalteten Docker-Containers |
| `container_name` | Name des Containers |

Anzeigen mit `terraform output`.

## Idempotenz und Configuration Drift

Nach dem erfolgreichen Deployment wurde die Konfiguration mit folgendem Befehl überprüft:

```bash
terraform plan -detailed-exitcode
```

Ergebnis: **Exit-Code 0**, keine Änderungen erforderlich.

Zusätzlich wurde Configuration Drift simuliert, indem der Testcontainer ausserhalb von Terraform gestoppt wurde. Terraform erkannte die Abweichung und plante die Neuerstellung des Containers.

Nach der Wiederherstellung ergab ein erneuter Plan keine Änderungen mehr.

## Architektur und Einschränkungen

Terraform verwaltet ein lokal vorhandenes Docker-Image und einen FastAPI-Container. Das Image wird zuvor separat mit `docker build` erstellt.

Der Container verwendet die SQLite-In-Memory-Datenbank der Anwendung, da keine `DATABASE_URL` konfiguriert ist. Die Daten sind nicht persistent.

Dieses Deployment dient als isolierter Infrastructure-as-Code-Nachweis. Das bestehende Docker-Compose-Deployment mit PostgreSQL bleibt unverändert.

Docker Compose eignet sich weiterhin für die zusammengehörigen Anwendungsdienste. Terraform demonstriert ergänzend die deklarative Infrastrukturverwaltung einschliesslich State, Plan und Drift-Erkennung.

## Terraform-State und Sicherheit

Die lokalen Terraform-State-Dateien sowie der heruntergeladene Provider unter `.terraform/` werden durch `.gitignore` ausgeschlossen.

Die Datei `.terraform.lock.hcl` wird versioniert, damit die Provider-Auswahl reproduzierbar bleibt.

State-Dateien können sensible Informationen enthalten und dürfen nicht öffentlich eingecheckt werden.

## Aufräumen

Alle von dieser Konfiguration verwalteten Ressourcen entfernen:

```bash
terraform destroy
```

Das zuvor selbst gebaute Docker-Image bleibt wegen `keep_locally = true` lokal erhalten.
