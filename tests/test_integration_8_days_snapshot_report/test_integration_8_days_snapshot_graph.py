import json
from time import sleep
import jq
from helpers.splunk import (
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_transfer_compatibility_payload,
)
from datetime import date, timedelta
from helpers.datetime_helper import (
    generate_report_start_date,
    generate_report_end_date,
    datetime_utc_now,
)
from tests.test_base import TestBase, EventType

class TestIntegrationEightDaysGraph(TestBase):
    def test_under_8_days_not_integrated_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            in_flight_conversation_id = "test_in_flight"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=in_flight_conversation_id,
                        registration_event_datetime=report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_count"
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
                "Integrated on time": "0",
                "Integrated after 8 days": "0",
                "Not integrated after 8 days": "0",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)
    
    def test_integrated_in_8_days_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        # test requires a date difference of less than 8 days.
        registration_event_datetime = datetime_utc_now().replace(day=1)
        ehr_integrated_datetime = datetime_utc_now().replace(day=8)

        try:
            integrated_conversation_id = "test_integrated_on_time"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=integrated_conversation_id,
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
                        conversation_id=integrated_conversation_id,
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
                        conversation_id=integrated_conversation_id,
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


            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_count"
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
                "In flight": "0",
                "Integrated on time": "1",
                "Integrated after 8 days": "0",
                "Not integrated after 8 days": "0",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    def test_integrated_after_8_days_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        # test requires a date difference of more than 8 days.
        registration_event_datetime = datetime_utc_now()
        ehr_integrated_datetime = datetime_utc_now() + timedelta(days=9)

        try:
            integrated_conversation_id = "test_integrated_on_time"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=integrated_conversation_id,
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
                        conversation_id=integrated_conversation_id,
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
                        conversation_id=integrated_conversation_id,
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


            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_count"
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
                "In flight": "0",
                "Integrated on time": "0",
                "Integrated after 8 days": "1",
                "Not integrated after 8 days": "0",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)

    def test_not_integrated_after_8_days_count(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        registration_event_datetime = datetime_utc_now() - timedelta(days=8)

        try:
            not_integrated_conversation_id = "test_not_integrated_on_time"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=not_integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=not_integrated_conversation_id,
                        registration_event_datetime=registration_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=not_integrated_conversation_id,
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
                        conversation_id=not_integrated_conversation_id,
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
                "gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_count"
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
                "In flight": "0",
                "Integrated on time": "0",
                "Integrated after 8 days": "0",
                "Not integrated after 8 days": "1",
            }

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")'
                )
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)