terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "weather_dashboard" {
  name         = "weather-dashboard:terraform-local"
  keep_locally = true
}

resource "docker_container" "weather_dashboard" {
  name  = var.container_name
  image = docker_image.weather_dashboard.image_id

  ports {
    internal = 8000
    external = var.host_port
    ip       = "127.0.0.1"
  }

  restart = "unless-stopped"
}
