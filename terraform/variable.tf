variable "storage_name" {
  description = "My datalake storage name"
  default = "tweets_datalake_project"
  type = string
}

variable "project" {
  description = "My GCP Project ID"
  default = "endless-context-338620"
  type = string
}

variable "region" {
  description = "Region for my GCP resources"
  default = "us-east1"
  type = string
}

variable "Storage_class" {
  description = "Storage class type for your bucket"
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "Political_tweets"
}