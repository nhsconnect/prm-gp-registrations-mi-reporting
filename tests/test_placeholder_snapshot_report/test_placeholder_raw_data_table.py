import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk import (
    get_telemetry_from_splunk,
    get_or_create_index,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_error_payload,
    create_transfer_compatibility_payload,
    create_ehr_response_payload,
)
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import (
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
)
import uuid


class TestPlaceholderRawDataTable(TestBase):
    def test_total_number_of_placeholders(self):
        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2),
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_placeholder_snapshot_report/"
                "gp2gp_placeholder_snapshot_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            expected_values = {
                "conversation_id": random_conversation_id,
                "total_number_of_placeholders": "2",
            }

            assert_list = []
            for idx, (key, value) in enumerate(expected_values.items()):
                assert_list.append('."{key}"=="{value}"')

            assert_str = ",".join(assert_list)
            self.LOG.info(f".[{idx}] | select( {assert_list})")

            assert jq.first(
                f".[{idx}] | select( {assert_list})",
                telemetry,
            )

        finally:
            self.delete_index(index_name)
