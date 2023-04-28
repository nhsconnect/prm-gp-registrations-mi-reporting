import os
import boto3
import logging
from chalicelib.splunk_config import SplunkConfig
from chalice import Chalice

from chalicelib.deploy_dashboards import deploy_dashboards
from chalicelib.deploy_reports import deploy_reports


app = Chalice(app_name='mi-dashboard-deployer')
logger = logging.getLogger("Dashboard-logging")
logger.setLevel(logging.DEBUG)


@app.lambda_function(name='splunk-uploader')
def main(event, context):

    # might already be set from aws ???
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')   

    session = boto3.Session(region_name=AWS_DEFAULT_REGION)

    ssm = session.client('ssm')

    print("requesting ssm parameters...")

    SPLUNK_URL = ssm.get_parameter(Name="/registrations/prod/user-input/splunk-api-url")['Parameter']['Value'] 
    SPLUNK_TOKEN = ssm.get_parameter(Name="/registrations/prod/user-input/splunk-api-token", WithDecryption=True)['Parameter']['Value']    
    S3_BUCKET_NAME = ssm.get_parameter(Name="/registrations/prod/user-input/splunk-report-data-bucket-name")['Parameter']['Value']

    splunkConfig = SplunkConfig(
        SPLUNK_URL,
        SPLUNK_TOKEN,
        S3_BUCKET_NAME
    )  

    print("deploying reports...")
    deploy_reports(splunkConfig)
    # print("deploying dashboards...")
    # deploy_dashboards(splunkConfig)
