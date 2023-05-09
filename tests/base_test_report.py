import logging
import os
import random
import string
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload,  create_error_payload, create_transfer_compatibility_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader


splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')     # defaults to localhost - see README
service = client.connect(token=splunk_token)


class splunk_index():

    def delete(index_name: str):
        """Delete splunk index"""
        service.indexes.delete(index_name)


    def create(service):
        """Create splunk index"""
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        index_name = "test_index_" + random_string
        return index_name, service.indexes.create(index_name)


class base_test_report():

    _log = logging.getLogger(__name__)

    @property
    def splunk_service(self):
        return self._splunk_service 
    
    @property
    def LOG(self):
        return self._log

    def __init__(self):

        splunk_token = os.environ['SPLUNK_TOKEN']       

        self._splunk_service = client.connect(token=splunk_token)


    def get_search(search_name):
        path = os.path.join(os.path.dirname(__file__),
                            '../reports')
        env = Environment(loader=FileSystemLoader(path))
        template = env.get_template(f'{search_name}.splunk')
        return template.render()


    def savedsearch(test_query):
        return "search "+test_query


    def teardown_function(self):
        """Function delete test_index."""
        self._service.indexes.delete("test_index")
