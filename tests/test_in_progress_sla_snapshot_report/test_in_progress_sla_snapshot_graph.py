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
from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader
from helpers.datetime_helper import (
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
    datetime_utc_now,
)
import uuid
from tests.test_base import TestBase, EventType


class TestSnapshotInProgressSlaGraph(TestBase):
    def test_in_flight(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test_in_flight",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(minutes=4)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(minutes=3)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_snapshot_report/gp2gp_in_progress_sla_snapshot_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.all('.[0] | select( .in_flight=="1" )', telemetry)

        finally:
            self.delete_index(index_name)

    def test_broken_24hr_sla(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(hours=26)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test_in_flight",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(datetime_utc_now()).strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_snapshot_report/gp2gp_in_progress_sla_snapshot_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.all('.[] | select( .broken_24hr_sla=="1")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_broken_ehr_sending_sla(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            broken_ehr_sending_outside_sla_conversation_id = (
                "test_broken_ehr_sending_outside_sla"
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(hours=1)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test_in_flight",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(minutes=30)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_snapshot_report/gp2gp_in_progress_sla_snapshot_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.all('.[] | select( .broken_ehr_sending_sla=="1")', telemetry)

        finally:
            self.delete_index(index_name)
