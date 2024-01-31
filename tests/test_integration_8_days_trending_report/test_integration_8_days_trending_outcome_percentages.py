import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import datetime_utc_now, generate_report_end_date
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_transfer_compatibility_payload, create_integration_payload
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysTrendingOutcomePercentages(TestBase):
    @pytest.mark.parametrize("time_period", ["month", "week", "day"])
    def test_gp2gp_integration_8_days_report_trending_awaiting_integration_percent(self, time_period):
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

        # Awaiting integration for over 8 days
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
                "gp2gp_integration_8_days_trending_report"
                "/gp2gp_integration_8_days_trending_awaiting_integration_percentage"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": time_period
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            expected_values = {}
            # Calculate expected output based on dynamic datetime used in test set up
            if time_period == "month":
                current_month_start = datetime_utc_now().replace(day=1)

                if current_month_start < on_time_event_datetime and current_month_start < late_event_datetime:
                    # Total number of awaiting integration in timeframe = 3
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%y-%m")}',
                                "In flight": "33.33",
                                "Not integrated after 8 days": "66.67",
                            },
                    }
                elif late_event_datetime < on_time_event_datetime < current_month_start:
                    # Total number of awaiting integration in timeframe = 3
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%y-%m")}',
                                "In flight": "33.33",
                                "Not integrated after 8 days": "66.67",
                            },
                    }
                elif late_event_datetime < current_month_start < on_time_event_datetime:
                    # Total number of awaiting integration before the start of month = 2
                    # Total number of awaiting integration after the start of month = 1
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m")}',
                                "In flight": "0.00",
                                "Not integrated after 8 days": "100.00",
                            },
                        "1":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%y-%m")}',
                                "In flight": "100.00",
                                "Not integrated after 8 days": "0.00",
                            },
                    }
            elif time_period == "week":
                late_event_week_start = late_event_datetime.isocalendar().week
                on_time_event_week_start = on_time_event_datetime.isocalendar().week

                if late_event_week_start == on_time_event_week_start:
                    # Total number of awaiting integration in timeframe = 3
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m-%W")}',
                                "In flight": "33.33",
                                "Not integrated after 8 days": "66.67",
                            },
                    }
                else:
                    # Total number of awaiting integration in first reporting week = 2
                    # Total number of awaiting integration in second reporting week = 1
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m-%W")}',
                                "In flight": "0.00",
                                "Not integrated after 8 days": "100.00",
                            },
                        "1":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%y-%m-%W")}',
                                "In flight": "100.00",
                                "Not integrated after 8 days": "0.00",
                            }
                    }
            elif time_period == "day":
                # Total number of awaiting integration in first day = 2
                # Total number of awaiting integration in second day = 1
                expected_values = {
                    "0":
                        {
                            "time_period": f'{late_event_datetime.strftime("%y-%m-%d")}',
                            "In flight": "0.00",
                            "Not integrated after 8 days": "100.00",
                        },
                    "1":
                        {
                            "time_period": f'{on_time_event_datetime.strftime("%y-%m-%d")}',
                            "In flight": "100.00",
                            "Not integrated after 8 days": "0.00",
                        },
                }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("time_period", ["month", "week", "day"])
    def test_gp2gp_integration_8_days_report_trending_successful_integration_percent(self, time_period):
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

        integration_outcomes = ["INTEGRATED", "INTEGRATED_AND_SUPPRESSED"]

        # Successful integration under 8 days
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
                    registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                                registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                "gp2gp_integration_8_days_trending_report"
                "/gp2gp_integration_8_days_trending_successful_integration_percentage"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": time_period
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            expected_values = {}
            # Calculate expected output based on dynamic datetime used in test set up
            if time_period == "month":
                current_month_start = datetime_utc_now().replace(day=1)

                if current_month_start < on_time_event_datetime and current_month_start < late_event_datetime:
                    # Total number of successful integration in timeframe = 5
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%y-%m")}',
                                "Integrated on time": "60.00",
                                "Integrated after 8 days": "40.00",
                            },
                    }
                elif late_event_datetime < on_time_event_datetime < current_month_start:
                    # Total number of successful integration in timeframe = 5
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%y-%m")}',
                                "Integrated on time": "60.00",
                                "Integrated after 8 days": "40.00",
                            },
                    }
                elif late_event_datetime < current_month_start < on_time_event_datetime:
                    # Total number of successful integration before the start of month = 2
                    # Total number of successful integration after the start of month = 3
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m")}',
                                "Integrated on time": "0.00",
                                "Integrated after 8 days": "100.00",
                            },
                        "1":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%y-%m")}',
                                "Integrated on time": "100.00",
                                "Integrated after 8 days": "0.00",
                            },
                    }
            elif time_period == "week":
                late_event_week_start = late_event_datetime.isocalendar().week
                on_time_event_week_start = on_time_event_datetime.isocalendar().week

                if late_event_week_start == on_time_event_week_start:
                    # Total number of successful integration in timeframe = 5
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m-%W")}',
                                "Integrated on time": "60.00",
                                "Integrated after 8 days": "40.00",
                            },
                    }
                else:
                    # Total number of successful integration in first reporting week = 2
                    # Total number of successful integration in second reporting week = 3
                    expected_values = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%y-%m-%W")}',
                                "Integrated on time": "0.00",
                                "Integrated after 8 days": "100.00",
                            },
                        "1":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%y-%m-%W")}',
                                "Integrated on time": "100.00",
                                "Integrated after 8 days": "0.00",
                            }
                    }
            elif time_period == "day":
                # Total number of successful integration in first day = 2
                # Total number of successful integration in second day = 3
                expected_values = {
                    "0":
                        {
                            "time_period": f'{late_event_datetime.strftime("%y-%m-%d")}',
                            "Integrated on time": "0.00",
                            "Integrated after 8 days": "100.00",
                        },
                    "1":
                        {
                            "time_period": f'{on_time_event_datetime.strftime("%y-%m-%d")}',
                            "Integrated on time": "100.00",
                            "Integrated after 8 days": "0.00",
                        },
                }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)
