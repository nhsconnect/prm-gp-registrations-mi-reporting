import os
from os import listdir
from os.path import isfile, join
import urllib.parse
from pathlib import Path
import requests
from requests.compat import urljoin
import boto3
from botocore.exceptions import ClientError
from chalicelib.splunk_config import SplunkConfig
from jinja2 import Environment, BaseLoader

class SplunkQueryError(RuntimeError):
    pass


def make_splunk_request(splunkConfig:SplunkConfig, dashboard_name:str, dashboard_data:str):

    print(f'splunk_host: {splunkConfig._splunk_host}')

    # API reference - https://docs.splunk.com/Documentation/Splunk/9.0.4/RESTREF
    create_dashboard_url = f'/servicesNS/{splunkConfig._splunk_admin_username}/{splunkConfig._splunk_app_id}/data/ui/views'

    url = urljoin(splunkConfig._splunk_host, create_dashboard_url)

    headers = {"Authorization": f"Bearer {splunkConfig._splunk_token}"}

    new_dashboard_data = urllib.parse.urlencode({
        "name": dashboard_name,
        "eai:data": dashboard_data
    })

    response = requests.post(url, headers=headers,
                             data=new_dashboard_data, verify=False, timeout=10)

    print(f'response: {response.status_code}')

    if response.status_code != 201:
        raise SplunkQueryError(
            f"Splunk request returned status code: {response.status_code} \
                with reason: {response.reason}")


client = boto3.client("s3")
s3 = boto3.resource('s3')


def deploy_dashboards(splunkConfig:SplunkConfig):

    # loop through dashboard files  
    bucket = s3.Bucket(splunkConfig._s3_bucket_name)
    
    for obj in bucket.objects.filter(Prefix='dashboards/'):        

        # get the dashboard xml as a string
        dashboard_string = obj.get()['Body'].read().decode('utf-8')
        env = Environment(loader=BaseLoader)
        template = env.from_string(dashboard_string)
        rendered_dashboard = template.render({
            "index": "TODO replace with a param store value of the index on the Splunk environment"
        })

        # create dashboard
        make_splunk_request(obj.key, rendered_dashboard)
