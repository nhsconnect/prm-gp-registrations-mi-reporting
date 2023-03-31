import os
from splunklib import client
from os import listdir
from os.path import isfile, join
import boto3
from botocore.exceptions import ClientError
from splunk_config import SplunkConfig


s3 = boto3.resource('s3')

def deploy_reports(splunkConfig:SplunkConfig):

    # loop through dashboard files  
    bucket = s3.Bucket(splunkConfig._s3_bucket_name)
    service = client.connect(token = splunkConfig._splunk_token)
    
    for obj in bucket.objects.filter(Prefix='dashboards/'):        

        # get the dashboard xml as a string
        report_content = obj.get()['Body'].read().decode('utf-8')  
        report_name = obj.key

        if report_name in service.saved_searches:
            service.saved_searches.delete(report_name)

        service.saved_searches.create(report_name, report_content)