variable "container_name" {
  type        = string
  description = "Name des Weather-Dashboard-Containers."
  default     = "weather-dashboard-terraform"
}

variable "host_port" {
  type        = number
  description = "Lokaler Port für das Weather Dashboard."
  default     = 18080

  validation {
    condition     = var.host_port > 1024 && var.host_port <= 65535
    error_message = "Der Port muss zwischen 1025 und 65535 liegen."
  }
}
