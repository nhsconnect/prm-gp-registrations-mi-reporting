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
    def test_raw_data_table_output_identical_placeholders(self):
        """
        Tests aggregation when all placeholders are the same
        """

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            placeholder = {
                "generatedBy": "SENDER",
                "clinicalType": "SCANNED_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }
            placeholders = [placeholder] * 6
            payload = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders,
                }
            }

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
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

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "6") '
                + f'| select( .clinical_type == "{placeholder["clinicalType"]}")'
                + f'| select( .reason == "{placeholder["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "6")'
                + f'| select( .generated_by == "{placeholder["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder["originalMimeType"]}")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_raw_data_table_output_different_placeholders(self):
        '''
        Tests aggregation when placeholders are different.
        '''
        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            placeholder_1 = {
                "generatedBy": "SENDER",
                "clinicalType": "SCANNED_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholder_2 = {
                "generatedBy": "PRE_EXISTING",
                "clinicalType": "ORIGINAL_TEXT_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholders = [placeholder_1] * 2
            placeholders += [placeholder_2] * 4

            payload = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders,
                }
            }

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
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

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "6") '
                + f'| select( .clinical_type == "{placeholder_1["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_1["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "2")'
                + f'| select( .generated_by == "{placeholder_1["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_1["originalMimeType"]}")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

            assert jq.all(
                f".[1] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "6") '
                + f'| select( .clinical_type == "{placeholder_2["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_2["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "4")'
                + f'| select( .generated_by == "{placeholder_2["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_2["originalMimeType"]}")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_raw_data_table_output_different_conversation_ids(self):
        '''
        Tests aggregation when conversation ids are different.
        '''
        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            placeholder_1 = {
                "generatedBy": "SENDER",
                "clinicalType": "SCANNED_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholder_2 = {
                "generatedBy": "PRE_EXISTING",
                "clinicalType": "ORIGINAL_TEXT_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholders_1 = [placeholder_1] * 3
            placeholders_2 = [placeholder_2] * 3

            payload_1 = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders_1,
                }
            }

            payload_2 = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders_2,
                }
            }

            conversation_id_1 = "conversation_id_1"
            conversation_id_2 = "conversation_id_2"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload_1,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:01:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload_2,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:01:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
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

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{conversation_id_2}") '
                + f'| select( .total_number_of_placeholders == "3") '
                + f'| select( .clinical_type == "{placeholder_2["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_2["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "3")'
                + f'| select( .generated_by == "{placeholder_2["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_2["originalMimeType"]}")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
                )

            assert jq.all(
                f".[1] "
                + f'| select( .conversation_id == "{conversation_id_1}") '
                + f'| select( .total_number_of_placeholders == "3") '
                + f'| select( .clinical_type == "{placeholder_1["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_1["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "3")'
                + f'| select( .generated_by == "{placeholder_1["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_1["originalMimeType"]}")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
                )

        finally:
            self.delete_index(index_name)
