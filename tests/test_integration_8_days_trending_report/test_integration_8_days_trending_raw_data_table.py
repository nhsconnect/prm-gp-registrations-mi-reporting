import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import generate_report_end_date, datetime_utc_now
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, create_integration_payload
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysTrendingRawDataTableOutputs(TestBase):
    @pytest.mark.parametrize(
        "time_period, description, time_delta, number_of_events",
        [
            ("day", "yesterday", 1, 1),
            ("week", "one_week_ago", 7, 2),
            ("month", "this_month", 5, 3)
        ]
    )
    def test_gp2gp_integration_8_days_trending_raw_data_table_column_token(self, time_period, description, time_delta,
                                                                           number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        line = "In flight"

        event_datetime = datetime_utc_now() - timedelta(days=time_delta)

        if time_period == "day":
            column = event_datetime.strftime("%Y-%m-%d")
        elif time_period == "week":
            column = event_datetime.strftime("%Y-Wk%W")
        elif time_period == "month":
            column = event_datetime.strftime("%Y-%m")

        self.LOG.info(f"column for {time_period}: {column}")

        try:

            for i in range(number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'ready_to_integrate_conversation_{i}',
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
                            conversation_id=f'ready_to_integrate_conversation_{i}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_integration_8_days_trending_report/gp2gp_integration_8_days_trending_raw_data_table'
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$line$": line,
                "$column$": column,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert len(telemetry) == number_of_events

            for idx in range(number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "ready_to_integrate_conversation_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") ', telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, line, time_delta, number_of_events",
        [
            ("day", "Integrated on time", 1, 1),
            ("day", "Integrated after 8 days", 9, 1),
            ("week", "Integrated on time", 3, 1),
            ("week", "Integrated after 8 days", 14, 2),
            ("month", "Integrated on time", 7, 3),
            ("month", "Integrated after 8 days", 28, 3)
        ]
    )
    def test_gp2gp_integration_8_days_trending_raw_data_table_line_token(self, time_period, line, time_delta,
                                                                         number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        event_datetime = datetime_utc_now() - timedelta(days=time_delta)

        if time_period == "day":
            column = event_datetime.strftime("%Y-%m-%d")
        elif time_period == "week":
            column = event_datetime.strftime("%Y-Wk%W")
        elif time_period == "month":
            column = event_datetime.strftime("%Y-%m")

        self.LOG.info(f"column: {column}")
        ehr_integration_datetime = datetime_utc_now()

        try:

            for i in range(number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'successful_integration_{i}',
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
                            conversation_id=f'successful_integration_{i}',
                            registration_event_datetime=ehr_integration_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                'gp2gp_integration_8_days_trending_report/gp2gp_integration_8_days_trending_raw_data_table'
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$line$": line,
                "$column$": column,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert len(telemetry) == number_of_events

            for idx in range(number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "successful_integration_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") ', telemetry
                )

        finally:
            self.delete_index(index_name)
