import json
from datetime import timedelta
from time import sleep

import jq

from helpers.datetime_helper import (
    generate_report_end_date,
    datetime_utc_now,
)
from helpers.splunk import (
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_transfer_compatibility_payload,
)
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysGraph(TestBase):
    def test_records_integration_8_days_snapshot_report_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Event date times
        ehr_integration_datetime = datetime_utc_now()
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)
        registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

        integration_outcomes = [
            "INTEGRATED",
            "INTEGRATED_AND_SUPPRESSED",
            "SUPPRESSED_AND_REACTIVATED",
            "FILED_AS_ATTACHMENT",
            "INTERNAL_TRANSFER",
            "REJECTED",
            "FAILED_TO_INTEGRATE"
        ]

        try:
            for idx, registration_time in enumerate(registration_event_datetime_list):
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

                for outcome in integration_outcomes:
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
                                registration_event_datetime=ehr_integration_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_INTEGRATIONS.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_integration_payload(outcome=outcome)

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

    def test_records_integration_8_days_snapshot_report_overall_percentage(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Event date times
        ehr_integration_datetime = datetime_utc_now()
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)
        registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

        integration_outcomes = [
            "INTEGRATED",
            "INTEGRATED_AND_SUPPRESSED",
            "SUPPRESSED_AND_REACTIVATED",
            "FILED_AS_ATTACHMENT",
            "INTERNAL_TRANSFER",
            "REJECTED",
            "FAILED_TO_INTEGRATE"
        ]

        try:
            for idx, registration_time in enumerate(registration_event_datetime_list):

                # Eligible for transfer only
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'eligible_for_transfer_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test1"
                            )
                        )
                    ),
                    sourcetype="myevent",
                )

                # Awaiting Integration
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

                # Integration
                for outcome in integration_outcomes:
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
                                registration_event_datetime=ehr_integration_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_report_overall_percentage"
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
                "In flight": "5.56",
                "Integrated on time": "27.78",
                "Integrated after 8 days": "27.78",
                "Not integrated after 8 days": "5.56",
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

    def test_records_integration_8_days_snapshot_report_awaiting_integration_percentage(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Event date times
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)
        registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

        # Awaiting integration and over 8 days
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id="not_integrated_and_overtime_id",
                    registration_event_datetime=late_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                    conversation_id="not_integrated_and_overtime_id",
                    registration_event_datetime=late_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    sendingSupplierName="EMIS",
                    requestingSupplierName="TPP",
                )
            ),
            sourcetype="myevent",
        )

        # Generate more events
        try:
            for idx, registration_time in enumerate(registration_event_datetime_list):
                # Eligible for transfer only
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'eligible_for_transfer_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test1"
                            )
                        )
                    ),
                    sourcetype="myevent",
                )

                # Awaiting Integration
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

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report"
                "/gp2gp_integration_8_days_snapshot_report_awaiting_integration_percentage"
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
                "In flight": "33.33",
                "Not integrated after 8 days": "66.67",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .awaiting_integration_status=="{key}") | select (.percent=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .awaiting_integration_status=="{key}") | select (.percent=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    def test_records_integration_8_days_snapshot_report_successful_integration_percentage(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Event date times
        ehr_integration_datetime = datetime_utc_now()
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)
        registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

        successful_integration_outcomes = [
            "INTEGRATED",
            "INTEGRATED_AND_SUPPRESSED",
            "SUPPRESSED_AND_REACTIVATED",
            "FILED_AS_ATTACHMENT",
            "INTERNAL_TRANSFER"
        ]

        # Successful integration within 8 days
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id="integrated_on_time_id",
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
                    conversation_id="integrated_on_time_id",
                    registration_event_datetime=ehr_integration_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=EventType.EHR_INTEGRATIONS.value,
                    sendingSupplierName="EMIS",
                    requestingSupplierName="TPP",
                    payload=create_integration_payload(outcome="INTEGRATED")
                )),
            sourcetype="myevent"
        )

        # Generate more events
        try:
            for idx, registration_time in enumerate(registration_event_datetime_list):

                # Eligible for transfer only
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'eligible_for_transfer_{idx}',
                            registration_event_datetime=registration_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test1"
                            )
                        )
                    ),
                    sourcetype="myevent",
                )

                # Successful integration
                for outcome in successful_integration_outcomes:
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
                                registration_event_datetime=ehr_integration_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                "gp2gp_integration_8_days_snapshot_report"
                "/gp2gp_integration_8_days_snapshot_report_successful_integration_percentage"
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
                "Integrated on time": "54.55",
                "Integrated after 8 days": "45.45",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .successful_integration_status=="{key}") | select (.percent=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .successful_integration_status=="{key}") | select (.percent=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)
