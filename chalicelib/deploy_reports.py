import os
from splunklib import client, binding
from splunklib.binding import AuthenticationError
from splunklib.binding import HTTPError as HttpError
from os import listdir
from os.path import isfile, join
import boto3
from botocore.exceptions import ClientError
from chalicelib.splunk_config import SplunkConfig


s3 = boto3.resource('s3')


def deploy_reports(splunkConfig: SplunkConfig):

    # report files stored in s3 bucket
    # bucket = s3.Bucket(splunkConfig.s3_bucket_name)

    try:
        connectionHanlder = binding.handler(timeout=10)

        service = client.connect(            
            # scheme=splunkConfig.splunk_scheme,
            host=splunkConfig.splunk_host,
            port=splunkConfig.splunk_port,
            token=splunkConfig.splunk_token,
            username=splunkConfig.splunk_admin_username,
            app=splunkConfig.splunk_app_id,
            connectionHanlder=connectionHanlder)
        
        print(f"splunk admin username: {splunkConfig.splunk_admin_username}")

        print("Connected to splunk ok. Looping through reports...")

        print("getting saved searches...")
        saved_searches = service.saved_searches            

        print("creating saved search...")
        saved_searches.create('my_saved_search_2',
                                  'search * | head 1')
        print("saved search created ok.")

        # for obj in bucket.objects.filter(Prefix='reports/'):

        #     # get the dashboard xml as a string
        #     report_content = obj.get()['Body'].read().decode('utf-8')
        #     report_name = obj.key

        #     print(f"Report: {report_name}")
        #     # print(f"Report contect: {report_content}")

        #     # if len(service.saved_searches) == 0:
        #     #     print("No saved searches.")
        #     #     service.saved_searches.create(report_name, report_content)
        #     #     print(f"created report: {report_name}")
        #     #     return True

        #     # for saved_search in service.saved_searches:
        #     #     print(f"Saved search: {str(saved_search)}")

        #     #     if saved_search.name == report_name:
        #     #         service.saved_searches.delete(report_name)

        #     # service.saved_searches.create(
        #     #     name=report_name, search=report_content)
        #     print("getting saved searches...")
        #     saved_searches = service.saved_searches            

        #     print("creating saved search...")
        #     saved_searches.create('my_saved_search',
        #                           'search * | head 1')
        #     print("saved search created ok.")

        #     assert 'my_saved_search' in saved_searches

        #     saved_searches.delete('my_saved_search')

        #     assert 'my_saved_search' not in saved_searches

    except AuthenticationError as ae:
        print(
            f"Authentication error occurred while connecting to Splunk search head. Reason being, {ae}")
    except HttpError as he:
        print(f"Http Error:{str(he)}")
    except Exception as ex:
        print(f"Exception deploying reports: {str(ex)}")

        import traceback
        print(traceback.format_exc())
