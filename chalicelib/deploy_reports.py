import os
from splunklib import client
from os import listdir
from os.path import isfile, join
import boto3
from botocore.exceptions import ClientError

# set by pipeline
splunk_host = os.environ.get('SPLUNK_HOST') or 'https://localhost:8089'
splunk_admin_username = os.environ.get('SPLUNK_ADMIN_USERNAME')
splunk_app_id = os.environ.get('SPLUNK_APP_ID') or 'search'
splunk_token = os.environ['SPLUNK_TOKEN']

# s3 bucket
bucket_name = os.environ['BUCKET_NAME']

def check_env_variable(env_var: str) -> None:
    try:
        os.environ[env_var]
    except KeyError:
        print(f'Please set the environment variable: {env_var}')


# check essential env variables
check_env_variable("SPLUNK_HOST") # e.g. https://localhost:8089
check_env_variable("SPLUNK_ADMIN_USERNAME") # user with admin role
check_env_variable("SPLUNK_TOKEN") # token created with splunk
check_env_variable("SPLUNK_APP_ID") 
check_env_variable("BUCKET_NAME")


s3 = boto3.resource('s3')


def deploy_reports():

    # loop through dashboard files  
    bucket = s3.Bucket(bucket_name)
    service = client.connect(token=splunk_token)
    
    for obj in bucket.objects.filter(Prefix='dashboards/'):        

        # get the dashboard xml as a string
        report_content = obj.get()['Body'].read().decode('utf-8')  
        report_name = obj.key

        if report_name in service.saved_searches:
            service.saved_searches.delete(report_name)

        service.saved_searches.create(report_name, report_content)