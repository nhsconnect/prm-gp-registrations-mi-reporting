import logging
import os
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
from tests.test_base import TestBase, EventType

class TestInternalTransfers(TestBase):

    def test_internal_transfer(self):

        try:
            # Arrange

            index_name, index = self.create_index()

            # test - #1 internal transfer

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_internal_transfer_test#1',
                        registration_event_datetime="2023-03-10T09:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            # test - #2 NOT inernal transfer
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_internal_transfer_test#2',
                        registration_event_datetime="2023-03-10T09:30:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_test_internal_transfer')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_internal_transfer=="1" )', telemetry)
            
        finally:
            self.delete_index(index_name)
