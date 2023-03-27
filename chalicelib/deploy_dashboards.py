import os
from os import listdir
from os.path import isfile, join
import urllib.parse
from pathlib import Path
import requests
from requests.compat import urljoin
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


class SplunkQueryError(RuntimeError):
    pass


def make_splunk_request(name, code):

    print(f'splunk_host: {splunk_host}')

    # API reference - https://docs.splunk.com/Documentation/Splunk/9.0.4/RESTREF
    create_dashboard_url = f'/servicesNS/{splunk_admin_username}/{splunk_app_id}/data/ui/views'

    url = urljoin(splunk_host, create_dashboard_url)

    headers = {"Authorization": f"Bearer {splunk_token}"}

    new_dashboard_data = urllib.parse.urlencode({
        "name": name,
        "eai:data": code
    })

    response = requests.post(url, headers=headers,
                             data=new_dashboard_data, verify=False, timeout=10)

    print(f'response: {response.status_code}')

    if response.status_code != 201:
        raise SplunkQueryError(
            f"Splunk request returned status code: {response.status_code} \
                with reason: {response.reason}")


# check essential env variables
check_env_variable("SPLUNK_HOST") # e.g. https://localhost:8089
check_env_variable("SPLUNK_ADMIN_USERNAME") # user with admin role
check_env_variable("SPLUNK_TOKEN") # token created with splunk

client = boto3.client("s3")
s3 = boto3.resource('s3')


def get_or_create_bucket(name:str):

    try:       
        client.head_bucket(Bucket=name)
    except ClientError:
        # The bucket does not exist or you have no access.
        client.create_bucket(Bucket=name, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

    return s3.Bucket(name)



def deploy_dashboards():

    # loop through dashboard files  
    bucket = get_or_create_bucket(bucket_name)  #s3.Bucket("[Bucket Name]")   
    
    for obj in bucket.objects.filter(Prefix='dashboards/'):        

        # get the dashboard xml as a string
        dashboard_string = obj.get()['Body'].read().decode('utf-8')  

        # create dashboard
        make_splunk_request(obj.key, dashboard_string)
