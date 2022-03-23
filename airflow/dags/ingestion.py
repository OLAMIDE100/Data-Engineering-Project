#python libraries
import os
import logging
from datetime import datetime,timedelta


#gcloud libraries
from google.cloud import storage


#airflow libraries
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator


#Variables
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")

today = (datetime.today() + timedelta(days= -1)).strftime('%Y-%m-%d')

pa_col = "Date"
clu_col = "category"


path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'Political_tweets')

INPUT_FILETYPE = "csv"

dataset_file = f"tweets_{today}.csv"





def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)

#default argument for dag definition/declaration
default_args = {
    "owner": "mide",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

#DAG declaration using context manager

with DAG(
    dag_id="tweets_ingestion_gcs_dag",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['mide_tweets_project'],
) as dag:
    scrape_dataset_task = BashOperator(
        task_id = "download_dataset_task",
        bash_command=f"python /opt/airflow/dags/scrape.py"
    )
    


    local_to_gcs_task = PythonOperator(
    task_id = "local_to_gcs_task",
    python_callable = upload_to_gcs,
    op_kwargs={
        "bucket": BUCKET, 
        "object_name" :f"tweets/{dataset_file}",
        "local_file": f"{path_to_local_home}/{dataset_file}"
        
             }
    )

    bigquery_external_table_task = BigQueryCreateExternalTableOperator(
        task_id=f"load_tweet_to_datawarehouse_task",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "tweets_external_table",
            },
            "externalDataConfiguration": {
                "autodetect": "True",
                "sourceFormat": f"{INPUT_FILETYPE.upper()}",
                "sourceUris": [f"gs://{BUCKET}/tweets/tweets_2022-*.csv"],
                "allow_quoted_newlines" : "TRUE"
            },
        },
    )
 

    CREATE_BQ_TBL_QUERY = (
        f"CREATE OR REPLACE TABLE {BIGQUERY_DATASET}.tweets \
        PARTITION BY DATE({pa_col}) \
        CLUSTER BY {clu_col} \
        AS \
        SELECT * FROM {BIGQUERY_DATASET}.tweets_external_table;"
    )
   
    # Create a partitioned table from external table
    bq_create_partitioned_and_cluster_table_job = BigQueryInsertJobOperator(
        task_id=f"bq_create_tweets_partitioned_and_clustered_table_task",
        configuration={
            "query": {
                "query": CREATE_BQ_TBL_QUERY,
                "useLegacySql": False,
            }
        }
    )

    remove_data_from_local = BashOperator(
        task_id = "remove_file_from_local_machine",
        bash_command=f"rm {path_to_local_home}/{dataset_file}"
    )

    
    scrape_dataset_task >> local_to_gcs_task >> bigquery_external_table_task >> bq_create_partitioned_and_cluster_table_job >> remove_data_from_local