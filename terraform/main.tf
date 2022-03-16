terraform {
  required_version = ">= 1.0"
  backend "local" {}
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}


provider "google" {
  project = var.project
  region = var.region
}


# Data Lake Bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${var.storage_name}_${var.project}"
  location      = var.region

    # Optional, but recommended settings:
  storage_class = var.Storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}


#Data Warehouse
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
  project    = var.project
  location   = var.region
  }
