import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import (
    generate_report_start_date,
    generate_report_end_date,
    datetime_utc_now,
)
from helpers.splunk import (
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
)
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysGraph(TestBase):
    @pytest.mark.parametrize("awaiting_integration_timeframe", ["WITHIN_8_DAYS", "AFTER_8_DAYS"])
    def test_records_not_integrated_based_on_timeframe_count(self, awaiting_integration_timeframe):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        if awaiting_integration_timeframe == "WITHIN_8_DAYS":
            registration_event_datetime = datetime_utc_now() - timedelta(days=7)
        else:
            registration_event_datetime = datetime_utc_now() - timedelta(days=9)

        try:
            conversation_id = "awaiting_integration_id"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_report_count"
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
            if awaiting_integration_timeframe == "WITHIN_8_DAYS":
                expected_values = {
                    "In flight": "1",
                    "Integrated on time": "0",
                    "Integrated after 8 days": "0",
                    "Not integrated after 8 days": "0",
                }
            else:
                expected_values = {
                    "In flight": "0",
                    "Integrated on time": "0",
                    "Integrated after 8 days": "0",
                    "Not integrated after 8 days": "1",
                }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("integration_timeframe", ["WITHIN_8_DAYS", "AFTER_8_DAYS"])
    def test_records_successfully_integrated_based_on_timeframe_count(self, integration_timeframe):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        if integration_timeframe == "WITHIN_8_DAYS":
            registration_event_datetime = datetime_utc_now() - timedelta(days=7)
        else:
            registration_event_datetime = datetime_utc_now() - timedelta(days=9)

        ehr_integrated_datetime = datetime_utc_now()

        # We want to count only successful integrations
        integration_outcome_list = [
            "INTEGRATED",
            "INTEGRATED_AND_SUPPRESSED",
            "SUPPRESSED_AND_REACTIVATED",
            "FILED_AS_ATTACHMENT",
            "INTERNAL_TRANSFER",
            "REJECTED"
        ]

        try:
            for outcome in integration_outcome_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'integration_with_{outcome}',
                            registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=f'integration_with_{outcome}',
                            registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'integration_with_{outcome}',
                            registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome=outcome
                            )

                        )),
                    sourcetype="myevent"
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_report_count"
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
            if integration_timeframe == "WITHIN_8_DAYS":
                expected_values = {
                    "In flight": "0",
                    "Integrated on time": "5",
                    "Integrated after 8 days": "0",
                    "Not integrated after 8 days": "0",
                }
            else:
                expected_values = {
                    "In flight": "0",
                    "Integrated on time": "0",
                    "Integrated after 8 days": "5",
                    "Not integrated after 8 days": "0",
                }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    def test_records_integration_8_days_snapshot_report_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)

        registration_event_time_list = [on_time_event_datetime, late_event_datetime]
        ehr_integrated_datetime = datetime_utc_now()

        integration_outcome_list = [
            "INTEGRATED",
            "INTEGRATED_AND_SUPPRESSED",
            "SUPPRESSED_AND_REACTIVATED",
            "FILED_AS_ATTACHMENT",
            "INTERNAL_TRANSFER",
            "REJECTED",
            "FAILED_TO_INTEGRATE"
        ]

        try:
            for idx, registration_time in enumerate(registration_event_time_list):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'ready_to_integrate_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=f'ready_to_integrate_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                for outcome in integration_outcome_list:
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'integration_on_{idx}_with_{outcome}',
                                registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                                conversation_id=f'integration_on_{idx}_with_{outcome}',
                                registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                            )
                        ),
                        sourcetype="myevent",
                    )

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'integration_on_{idx}_with_{outcome}',
                                registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_INTEGRATIONS.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_integration_payload(
                                    outcome=outcome
                                )

                            )),
                        sourcetype="myevent"
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_report_count"
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
            expected_values = {
                "In flight": "1",
                "Integrated on time": "5",
                "Integrated after 8 days": "5",
                "Not integrated after 8 days": "1",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    def test_records_integration_8_days_snapshot_report_percentage(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)

        registration_event_time_list = [on_time_event_datetime, late_event_datetime]
        ehr_integrated_datetime = datetime_utc_now()

        integration_outcome_list = [
            "INTEGRATED",
            "REJECTED",
        ]

        try:
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="integration_on_time",
                        registration_event_datetime=on_time_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id="integration_on_time",
                        registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_integration_payload(
                            outcome="INTEGRATED"
                        )

                    )),
                sourcetype="myevent"
            )

            for idx, registration_time in enumerate(registration_event_time_list):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'ready_to_integrate_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=f'ready_to_integrate_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                for outcome in integration_outcome_list:
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'integration_on_{idx}_with_{outcome}',
                                registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                                conversation_id=f'integration_on_{idx}_with_{outcome}',
                                registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_INTEGRATIONS.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_integration_payload(
                                    outcome=outcome
                                )

                            )),
                        sourcetype="myevent"
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_report_percentage"
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
            expected_values = {
                "In flight": "50.00",
                "Integrated on time": "66.67",
                "Integrated after 8 days": "33.33",
                "Not integrated after 8 days": "50.00",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.percent=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .integration_status=="{key}") | select (.percent=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)
