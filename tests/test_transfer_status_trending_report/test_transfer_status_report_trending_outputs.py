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


class TestTransferStatusReportTrendingOutputs(TestBase):

    def test_gp2gp_transfer_status_report_trending_count_with_datetimes(self):
        '''This test just tests the "percentages output" is calling the base query correctly.'''

        # Arrange
        index_name, index = self.create_index()

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_2',
                        registration_event_datetime="2023-03-10T09:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test2"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_3',
                        registration_event_datetime="2023-03-10T10:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.get_search(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "0",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"1": {"time_period": "23-03",
                                     "TECHNICAL_FAILURE": "2"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)
