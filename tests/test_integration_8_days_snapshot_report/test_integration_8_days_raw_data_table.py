import json
import uuid
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import generate_report_end_date, datetime_utc_now
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysRawDataTableOutputs(TestBase):
    @pytest.mark.parametrize(
        "column, days",
        [
            ("In flight", 7),
            ("Integrated on time", 7),
            ("Integrated after 8 days", 9),
            ("Not integrated after 8 days", 9),
        ]
    )
    def test_gp2gp_integration_8_days_raw_data_table_in_flight(self, column, days):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        event_datetime = datetime_utc_now() - timedelta(days=days)

        try:
            random_conversation_id = f"test_integration_8_days_graph_{uuid.uuid4()}"

            # Awaiting Integration
            if column == "In flight" or column == "Not integrated after 8 days":
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=random_conversation_id,
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=random_conversation_id,
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            # Successful Integration
            if column == "Integrated on time" or column == "Integrated after 8 days":
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=random_conversation_id,
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=random_conversation_id,
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=random_conversation_id,
                            registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(outcome="INTEGRATED")
                        )),
                    sourcetype="myevent"
                )
            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_integration_8_days_snapshot_report/gp2gp_integration_8_days_snapshot_raw_data_table'
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$column$": column
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert jq.all(
                f".[] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                + f'| select( .requesting_supplier_name == "TPP") '
                + f'| select( .sending_supplier_name == "EMIS") '
                + f'| select( .reporting_practice_ods_code == "A00029") '
                + f'| select( .requesting_practice_ods_code == "A00029") '
                + f'| select( .sending_practice_ods_code == "B00157") ', telemetry
            )

        finally:
            self.delete_index(index_name)
