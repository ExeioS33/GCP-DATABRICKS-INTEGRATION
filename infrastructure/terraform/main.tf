# ========================================
# TERRAFORM - INFRASTRUCTURE AS CODE
# Pipeline GCP/Databricks - Configuration automatisée
# ========================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ========================================
# VARIABLES
# ========================================

variable "project_id" {
  description = "Project ID GCP"
  type        = string
  default     = "biforaplatform"
}

variable "region" {
  description = "Région GCP"
  type        = string
  default     = "europe-west1"
}

variable "user_email" {
  description = "Email de l'utilisateur admin"
  type        = string
  default     = "andrirazafy9@gmail.com"
}

variable "bucket_name" {
  description = "Nom du bucket GCS"
  type        = string
  default     = "supdevinci_bucket"
}

variable "bucket_path" {
  description = "Chemin dans le bucket"
  type        = string
  default     = "sanda_celia"
}

# ========================================
# PROVIDER CONFIGURATION
# ========================================

provider "google" {
  project = var.project_id
  region  = var.region
}

# ========================================
# DATA SOURCES
# ========================================

data "google_project" "current" {
  project_id = var.project_id
}

# ========================================
# SERVICE ACCOUNT DATAFLOW
# ========================================

resource "google_service_account" "dataflow_generator" {
  account_id   = "dataflow-generator"
  display_name = "Service Account pour génération de données Dataflow"
  description  = "Service account dédié au pipeline de génération de données financières"
}

# Clé de service account (optionnel, préférer Workload Identity)
resource "google_service_account_key" "dataflow_generator_key" {
  service_account_id = google_service_account.dataflow_generator.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# ========================================
# RÔLES IAM - SERVICE ACCOUNT
# ========================================

# Dataflow Admin
resource "google_project_iam_member" "dataflow_admin" {
  project = var.project_id
  role    = "roles/dataflow.admin"
  member  = "serviceAccount:${google_service_account.dataflow_generator.email}"
}

# Dataflow Worker
resource "google_project_iam_member" "dataflow_worker" {
  project = var.project_id
  role    = "roles/dataflow.worker"
  member  = "serviceAccount:${google_service_account.dataflow_generator.email}"
}

# Storage Admin
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.dataflow_generator.email}"
}

# Dataflow Developer (pour développement)
resource "google_project_iam_member" "dataflow_developer" {
  project = var.project_id
  role    = "roles/dataflow.developer"
  member  = "serviceAccount:${google_service_account.dataflow_generator.email}"
}

# ========================================
# RÔLES IAM - UTILISATEUR
# ========================================

# Service Account User
resource "google_project_iam_member" "user_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "user:${var.user_email}"
}

# Dataflow Admin
resource "google_project_iam_member" "user_dataflow_admin" {
  project = var.project_id
  role    = "roles/dataflow.admin"
  member  = "user:${var.user_email}"
}

# Dataflow Developer
resource "google_project_iam_member" "user_dataflow_developer" {
  project = var.project_id
  role    = "roles/dataflow.developer"
  member  = "user:${var.user_email}"
}

# ========================================
# BUCKET GCS ET STRUCTURE
# ========================================

# Bucket principal (s'il n'existe pas déjà)
resource "google_storage_bucket" "main_bucket" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false

  # Versioning pour audit
  versioning {
    enabled = true
  }

  # Lifecycle pour optimiser les coûts
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Dossiers virtuels dans le bucket
resource "google_storage_bucket_object" "folder_tmp" {
  name    = "${var.bucket_path}/tmp/.gitkeep"
  bucket  = google_storage_bucket.main_bucket.name
  content = "Dossier temporaire Dataflow - ${timestamp()}"
}

resource "google_storage_bucket_object" "folder_raw" {
  name    = "${var.bucket_path}/raw/mouvements/.gitkeep"
  bucket  = google_storage_bucket.main_bucket.name
  content = "Données CSV brutes - ${timestamp()}"
}

resource "google_storage_bucket_object" "folder_staging" {
  name    = "${var.bucket_path}/staging/mouvements/.gitkeep"
  bucket  = google_storage_bucket.main_bucket.name
  content = "Données Parquet optimisées - ${timestamp()}"
}

resource "google_storage_bucket_object" "folder_delta" {
  name    = "${var.bucket_path}/delta/mouvements/.gitkeep"
  bucket  = google_storage_bucket.main_bucket.name
  content = "Tables Delta - ${timestamp()}"
}

# ========================================
# APIS ENABLEMENT
# ========================================

resource "google_project_service" "dataflow_api" {
  service = "dataflow.googleapis.com"
}

resource "google_project_service" "storage_api" {
  service = "storage.googleapis.com"
}

resource "google_project_service" "bigquery_api" {
  service = "bigquery.googleapis.com"
}

resource "google_project_service" "iam_api" {
  service = "iam.googleapis.com"
}

# ========================================
# ORGANIZATION POLICY (si possible)
# ========================================

# Tentative de désactiver la contrainte Dataflow
resource "google_project_organization_policy" "dataflow_compute_service_account" {
  project    = var.project_id
  constraint = "constraints/dataflow.enforceComputeDefaultServiceAccountCheck"

  boolean_policy {
    enforced = false
  }
}

# ========================================
# OUTPUTS
# ========================================

output "service_account_email" {
  description = "Email du service account Dataflow"
  value       = google_service_account.dataflow_generator.email
}

output "service_account_key" {
  description = "Clé du service account (base64)"
  value       = google_service_account_key.dataflow_generator_key.private_key
  sensitive   = true
}

output "bucket_url" {
  description = "URL du bucket GCS"
  value       = "gs://${google_storage_bucket.main_bucket.name}/${var.bucket_path}"
}

output "project_number" {
  description = "Numéro du projet GCP"
  value       = data.google_project.current.number
}

output "deployment_commands" {
  description = "Commandes pour utiliser l'infrastructure"
  value = <<-EOT
    # Configuration des credentials
    echo '${google_service_account_key.dataflow_generator_key.private_key}' | base64 -d > key-dataflow.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key-dataflow.json"
    
    # Lancement du pipeline
    uv run src/generate_to_gcs.py
    
    # Monitoring
    gcloud dataflow jobs list --region=${var.region}
  EOT
} 