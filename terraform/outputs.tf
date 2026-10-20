output "container_id" {
  description = "Docker-Container-ID."
  value       = docker_container.weather_dashboard.id
}

output "container_name" {
  description = "Name des Weather-Dashboard-Containers."
  value       = docker_container.weather_dashboard.name
}

output "app_url" {
  description = "Lokale URL des Weather Dashboards."
  value       = "http://localhost:${var.host_port}"
}
