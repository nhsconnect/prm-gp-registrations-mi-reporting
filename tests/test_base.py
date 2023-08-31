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
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from abc import ABC
from jinja2 import Environment, FileSystemLoader
from helpers.splunk import generate_splunk_query_from_report

load_dotenv()

class EventType(Enum):
    READY_TO_INTEGRATE_STATUSES = 'READY_TO_INTEGRATE_STATUSES'
    REGISTRATIONS = 'REGISTRATIONS'
    EHR_INTEGRATIONS = 'EHR_INTEGRATIONS'
    ERRORS = 'ERRORS'
    EHR_RESPONSES = 'EHR_RESPONSES'
    EHR_REQUESTS = 'EHR_REQUESTS'
    TRANSFER_COMPATIBILITY_STATUSES = 'TRANSFER_COMPATIBILITY_STATUSES'
    DOCUMENT_RESPONSES = "DOCUMENT_RESPONSES"

class TestBase(ABC):    

    _log = logging.getLogger(__name__)    
    _splunk_service =  client.connect(username=os.environ.get('SPLUNK_ADMIN_USERNAME'))

    @property
    def splunk_service(self):
        return self._splunk_service 
    
    @property
    def LOG(self):
        return self._log    


    def savedsearch(self, test_query):
        return "search "+test_query
  
    
    def create_index(self):
        """Create splunk index"""
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        index_name = "test_index_" + random_string
        return index_name, self.splunk_service.indexes.create(index_name)
    
    def delete_index(self, index_name: str):
        """Delete splunk index"""
        self.splunk_service.indexes.delete(index_name)

    def generate_splunk_query_from_report(self, report_name):
        return generate_splunk_query_from_report(self,report_name)

