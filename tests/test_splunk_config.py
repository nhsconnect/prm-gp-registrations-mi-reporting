import logging
import os
import pytest
import json
from chalicelib.splunk_config import SplunkConfig


LOG = logging.getLogger(__name__)

def test_create_splunk_config():
    '''
    Create splunk config class from an existing parameter store value.
    '''

    # Arrange

    # format of existing parameter store value - /registrations/prod/user-input/splunk-api-url
    test_url = "https://my_splunk_host:8089/servicesNS/splunk_admin_user/my_app_name/search/jobs/export"
    test_token = "my_token"
    test_bucket_name = "my_bucket"    


    # Act
    splunk_config = SplunkConfig(test_url, test_token, test_bucket_name)

    # Assert

    assert splunk_config.splunk_scheme == "https"
    assert splunk_config.splunk_host == "my_splunk_host"
    assert splunk_config.splunk_port == 8089
    assert splunk_config.splunk_namespace == "servicesNS"
    assert splunk_config.splunk_admin_username == "splunk_admin_user"
    assert splunk_config.splunk_app_id == "my_app_name"
    assert splunk_config.splunk_token == test_token
    assert splunk_config.s3_bucket_name == test_bucket_name

    # check able to construct base api endpoint url. Note: we are not interested in/search/jobs/export
    assert test_url.startswith(splunk_config.get_base_api_url())
