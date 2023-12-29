"""Airflow DAG for the data pipeline"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import pendulum
import utils # from utils.py
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.redshift_cluster import RedshiftResumeClusterOperator
from airflow.providers.amazon.aws.sensors.redshift_cluster import RedshiftClusterSensor
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.amazon.aws.operators.redshift_cluster import RedshiftPauseClusterOperator

# # Use below code to generate Fernet key and save to env file
# # to be referred in docker-compose file for data encryption
# from cryptography.fernet import Fernet
# fernet_key= Fernet.generate_key()
# print(fernet_key.decode())

# Get exported variables from Airflow
BUCKET_NAME = Variable.get("RAW_BUCKET_NAME")
CLIENT_ID = Variable.get("REDDIT_CLIENT_ID")
PASSWORD = Variable.get("REDDIT_PASSWORD")
SECRET_KEY = Variable.get("REDDIT_SECRET_KEY")
USER_NAME = Variable.get("REDDIT_USER_NAME")
TODAY = datetime.utcnow()
POST_DIR_PATH = "wsb_posts"
POST_COMMENTS_DIR_PATH = "wsb_posts_and_comms"
FILE_TYPE = "transformed"


# Default arguments for defining the DAG
# start_date: if today is 8th, and I want to run my daily DAG on 9th, specify 8th
# actual_start_date = start_date + schedule_interval
default_args = {
    "owner": "davidj",
    "start_date": pendulum.datetime(2023, 10, 23, tz="UTC"),
    "depends_on_past": False,
    "email": ["airflow@airflow.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    # "retries": 5,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id = "WSB_reddit_to_aws_data_pipeline_v4",
    default_args = default_args,
    schedule_interval = '0 */12 * * *'
) as dag1:
    
    fetch_data_to_file = PythonOperator(
        task_id="fetch_reddit_data_from_api_to_json_file",
        python_callable=utils._fetch_reddit_data,
        op_kwargs={
            "client_id": CLIENT_ID, 
            "secret_key": SECRET_KEY,
            "user_name": USER_NAME,
            "password": PASSWORD
        }
    )
        
    load_post_comm_file_to_s3 = PythonOperator(
        task_id = "load_post_comm_json_file_to_s3",
        python_callable=utils._local_file_to_s3,
        op_kwargs={
            "filepath": Path(f"{FILE_TYPE}/{POST_COMMENTS_DIR_PATH}/{POST_COMMENTS_DIR_PATH}-{TODAY.year}-{TODAY.month}-{TODAY.day}-{TODAY.hour}.json"),
            "bucket_name": BUCKET_NAME, 
            "key": Path(f"{FILE_TYPE}/{POST_COMMENTS_DIR_PATH}/{POST_COMMENTS_DIR_PATH}-{TODAY.year}-{TODAY.month}-{TODAY.day}-{TODAY.hour}.json"),
            "remove_local": False
        }
    )

    load_post_file_to_s3 = PythonOperator(
        task_id = "load_post_json_file_to_s3",
        python_callable=utils._local_file_to_s3,
        op_kwargs={
            "filepath": Path(f"{FILE_TYPE}/{POST_DIR_PATH}/{POST_DIR_PATH}-{TODAY.year}-{TODAY.month}-{TODAY.day}-{TODAY.hour}.json"),
            "bucket_name": BUCKET_NAME, 
            "key": Path(f"{FILE_TYPE}/{POST_DIR_PATH}/{POST_DIR_PATH}-{TODAY.year}-{TODAY.month}-{TODAY.day}-{TODAY.hour}.json"),
            "remove_local": False
        }
    )

    resume_redshift = RedshiftResumeClusterOperator(
        task_id = "resume_redshift_cluster",
        cluster_identifier = "wsb-redshift-cluster-uswest1-davidjeongaws-dev0",
        aws_conn_id= "wsb_conn_id"
    )
    
    cluster_sensor = RedshiftClusterSensor(
        task_id = "wait_for_cluster_to_be_available",
        cluster_identifier= "wsb-redshift-cluster-uswest1-davidjeongaws-dev0",
        target_status= "available",
        aws_conn_id= "wsb_conn_id"
    )

    load_jsonfile_to_redshift_from_s3 = S3ToRedshiftOperator(
        task_id="load_json_file_to_redshift_from_s3",
        schema="fct",
        table="wsb_file",
        s3_bucket=BUCKET_NAME,
        s3_key=f"{FILE_TYPE}/{POST_COMMENTS_DIR_PATH}/{POST_COMMENTS_DIR_PATH}-{TODAY.year}-{TODAY.month}-{TODAY.day}-{TODAY.hour}.json",
        copy_options=["json 'auto'"],
        redshift_conn_id="redshift_conn_idd",
        aws_conn_id="wsb_conn_id",
        method='UPSERT',
        upsert_keys=["created_utc"]
    )
    
    pause_redshift = RedshiftPauseClusterOperator(
        task_id = "pause_redshift_cluster",
        cluster_identifier = "wsb-redshift-cluster-uswest1-davidjeongaws-dev0",
        aws_conn_id = "wsb_conn_id"
    )

    (
    fetch_data_to_file 
    >> [load_post_comm_file_to_s3, load_post_file_to_s3] 
    >> resume_redshift 
    >> cluster_sensor
    >> load_jsonfile_to_redshift_from_s3
    >> pause_redshift
    )