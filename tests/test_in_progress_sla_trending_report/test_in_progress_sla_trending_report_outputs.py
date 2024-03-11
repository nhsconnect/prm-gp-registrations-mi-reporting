import logging
import os
from enum import Enum
import pytest
import json
from time import sleep, strftime
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


class TestTrendingInProgressSlaGraph(TestBase):
    def test_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today() - timedelta(days=1)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP"
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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

            broken_ehr_sending_outside_sla_conversation_id = (
                "test_broken_ehr_sending_outside_sla"
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=21)
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
                        registration_event_datetime=(datetime_utc_now()).strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(datetime_utc_now()).strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla_and_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                        event_type=EventType.EHR_REQUESTS.value,
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla_and_ehr_sending_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(hours=25, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
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

            broken_24hr_sla_conversation_id = "test_broken_ehr_sending_sla_and_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=42)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
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
                        registration_event_datetime=(
                                datetime_utc_now()
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

            broken_24hr_sla_conversation_id = "test_broken_all_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25, minutes=42)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(hours=25, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
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

            # create technical failure conversation
            tech_failure_conv_id = "tech_failure_1"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=tech_failure_conv_id,
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
                        conversation_id=tech_failure_conv_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=4)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.ERRORS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload= create_error_payload(
                            errorCode="99",
                            errorDescription="test",
                            failurePoint="EHR_SENT"
                        )
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "IF": "1",
                      "B24": "1",
                      "BEhrS": "1",
                      "BEhrR": "1",
                      "B24 + BEhrS": "1",
                      "B24 + BEhrR": "1",
                      "BEhrS + BEhrR": "1",
                      "B24 + BEhrS + BEhrR": "1",
                      "other": "1",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_percentage(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today() - timedelta(days=1)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            for idx in range(2):
                in_flight_conversation_id = "test_in_flight"+str(idx)

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=in_flight_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=6)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                                    datetime_utc_now() - timedelta(minutes=5)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP"
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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

            for idx in range(3):
                broken_ehr_sending_outside_sla_conversation_id = (
                    "test_broken_ehr_sending_outside_sla"+str(idx)
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=25)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                                    datetime_utc_now() - timedelta(minutes=21)
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
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.EHR_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(datetime_utc_now()).strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            for idx in range(2):
                broken_24hr_sla_conversation_id = "test_broken_24hr_sla_and_ehr_requesting_sla"+str(idx)

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                            event_type=EventType.EHR_REQUESTS.value,
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

            for idx in range(4):
                broken_24hr_sla_conversation_id = "test_broken_24hr_sla_and_ehr_sending_sla"+str(idx)

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
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

            for idx in range(4):
                broken_24hr_sla_conversation_id = "test_broken_ehr_sending_sla_and_ehr_requesting_sla"+str(idx)

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=42)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                                    datetime_utc_now() - timedelta(minutes=21)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
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
                            registration_event_datetime=(
                                datetime_utc_now()
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

            for idx in range(2):
                broken_24hr_sla_conversation_id = "test_broken_all_sla"+str(idx)

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=42)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test",
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
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
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

            # create technical failure conversation
            tech_failure_conv_id = "tech_failure_1"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=tech_failure_conv_id,
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
                        conversation_id=tech_failure_conv_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=4)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.ERRORS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload= create_error_payload(
                            errorCode="99",
                            errorDescription="test",
                            failurePoint="EHR_SENT"
                        )
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_percentage"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "IF": "10.00",
                      "B24": "5.00",
                      "BEhrS": "15.00",
                      "BEhrR": "5.00",
                      "B24 + BEhrS": "20.00",
                      "B24 + BEhrR": "10.00",
                      "BEhrS + BEhrR": "20.00",
                      "B24 + BEhrS + BEhrR": "10.00",
                      "other": "5.00"
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_time_period_token_month(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today() - timedelta(days=35)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP"
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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

            broken_ehr_sending_outside_sla_conversation_id = (
                "test_broken_ehr_sending_outside_sla"
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=32, minutes=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(days=32, minutes=21)
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
                                datetime_utc_now() - timedelta(days=32)
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
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(days=32)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=32, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=32)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=32)
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
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=32)
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
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_this_month = datetime_utc_now().strftime("%Y-%m")
            time_period_month_last_month = (datetime_utc_now() - timedelta(days=32)).strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_last_month,
                      "IF": "0",
                      "B24": "0",
                      "BEhrS": "1",
                      "BEhrR": "1"
                      },
                "1": {"time_period": time_period_month_this_month,
                      "IF": "1",
                      "B24": "1",
                      "BEhrS": "0",
                      "BEhrR": "0"
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_time_period_token_week(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today() - timedelta(days=35)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP"
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=7)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(days=7)
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
                                datetime_utc_now() - timedelta(days=7)
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
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_sending_outside_sla_conversation_id = (
                "test_broken_ehr_sending_outside_sla"
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=14, minutes=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(days=14, minutes=21)
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
                                datetime_utc_now() - timedelta(days=14)
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
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=14)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=21, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=21)
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
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=21)
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
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "week",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_week_this_week = datetime_utc_now().strftime("%Y-Wk%W")
            time_period_week_this_week_less_one_week = (datetime_utc_now() - timedelta(days=7)).strftime("%Y-Wk%W")
            time_period_week_this_week_less_two_week = (datetime_utc_now() - timedelta(days=14)).strftime("%Y-Wk%W")
            time_period_week_this_week_less_three_week = (datetime_utc_now() - timedelta(days=21)).strftime("%Y-Wk%W")
            expected_values = {
                "0": {"time_period": time_period_week_this_week_less_three_week,
                      "IF": "0",
                      "B24": "0",
                      "BEhrS": "0",
                      "BEhrR": "1"
                      },
                "1": {"time_period": time_period_week_this_week_less_two_week,
                      "IF": "0",
                      "B24": "0",
                      "BEhrS": "1",
                      "BEhrR": "0"
                      },
                "2": {"time_period": time_period_week_this_week_less_one_week,
                      "IF": "0",
                      "B24": "1",
                      "BEhrS": "0",
                      "BEhrR": "0"
                      },
                "3": {"time_period": time_period_week_this_week,
                      "IF": "1",
                      "B24": "0",
                      "BEhrS": "0",
                      "BEhrR": "0"
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_time_period_token_day(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = date.today() - timedelta(days=5)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(minutes=5)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP"
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

            broken_24hr_sla_conversation_id = "test_broken_24hr_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_24hr_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                        registration_event_datetime=(
                                datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_sending_outside_sla_conversation_id = (
                "test_broken_ehr_sending_outside_sla"
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=2, minutes=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
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
                                datetime_utc_now() - timedelta(days=2, minutes=21)
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
                                datetime_utc_now() - timedelta(days=2)
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
                        conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=2)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=3, minutes=21)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=3)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=3)
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
                        conversation_id=broken_ehr_requesting_sla_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=3)
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
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "day",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_day_today = datetime_utc_now().strftime("%Y-%m-%d")
            time_period_day_today_less_one_day = (datetime_utc_now() - timedelta(days=1)).strftime("%Y-%m-%d")
            time_period_day_today_less_two_day = (datetime_utc_now() - timedelta(days=2)).strftime("%Y-%m-%d")
            time_period_day_today_less_three_day = (datetime_utc_now() - timedelta(days=3)).strftime("%Y-%m-%d")
            expected_values = {
                "0": {"time_period": time_period_day_today_less_three_day,
                      "IF": "0",
                      "B24": "0",
                      "BEhrS": "0",
                      "BEhrR": "1"
                      },
                "1": {"time_period": time_period_day_today_less_two_day,
                      "IF": "0",
                      "B24": "0",
                      "BEhrS": "1",
                      "BEhrR": "0"
                      },
                "2": {"time_period": time_period_day_today_less_one_day,
                      "IF": "0",
                      "B24": "1",
                      "BEhrS": "0",
                      "BEhrR": "0"
                      },
                "3": {"time_period": time_period_day_today,
                      "IF": "1",
                      "B24": "0",
                      "BEhrS": "0",
                      "BEhrR": "0"
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)