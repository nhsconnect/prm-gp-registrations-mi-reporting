import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import datetime_utc_now, generate_report_end_date
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType


class TestIntegrationEightDaysTrendingReportOutputs(TestBase):
    @pytest.mark.parametrize("time_period", ["month", "week", "day"])
    def test_gp2gp_integration_8_days_report_trending_count(self, time_period):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Calculate event date times
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)

        try:
            # Generate events
            integration_outcomes = ["INTEGRATED", "INTEGRATED_AND_SUPPRESSED"]
            registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

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
                                reason="testCountPerTimePeriod"
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
                                payload=create_integration_payload(outcome=outcome)

                            )),
                        sourcetype="myevent"
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_trending_report/gp2gp_integration_8_days_trending_report_count"
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_output = {}
            # Calculate expected output based on dynamic datetime used in test set up
            if time_period == "month":
                current_month_start = datetime_utc_now().replace(day=1)

                if current_month_start < on_time_event_datetime and current_month_start < late_event_datetime:
                    # Events and 8-day integration window fall within the current month
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%Y-%m")}',
                                "In flight": "1",
                                "Integrated on time": "2",
                                "Integrated after 8 days": "2",
                                "Not integrated after 8 days": "1",
                                "Others": "2"
                            },
                    }
                elif late_event_datetime < on_time_event_datetime < current_month_start:
                    # Events were created in the previous month but 8-day window includes beginning of current month
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%Y-%m")}',
                                "In flight": "1",
                                "Integrated on time": "2",
                                "Integrated after 8 days": "2",
                                "Not integrated after 8 days": "1",
                                "Others": "2"
                            },
                    }
                elif late_event_datetime < current_month_start < on_time_event_datetime:
                    # Late events created before the current month and on time within the current month
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-%m")}',
                                "In flight": "0",
                                "Integrated on time": "0",
                                "Integrated after 8 days": "2",
                                "Not integrated after 8 days": "1",
                                "Others": "1"
                            },
                        "1":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%Y-%m")}',
                                "In flight": "1",
                                "Integrated on time": "2",
                                "Integrated after 8 days": "0",
                                "Not integrated after 8 days": "0",
                                "Others": "1"
                            },
                    }
            elif time_period == "week":
                late_event_week_start = late_event_datetime.isocalendar().week
                on_time_event_week_start = on_time_event_datetime.isocalendar().week

                if late_event_week_start == on_time_event_week_start:
                    # Events fall into the same week
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "1",
                                "Integrated on time": "2",
                                "Integrated after 8 days": "2",
                                "Not integrated after 8 days": "1",
                                "Others": "2"
                            }
                    }
                else:
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "0",
                                "Integrated on time": "0",
                                "Integrated after 8 days": "2",
                                "Not integrated after 8 days": "1",
                                "Others": "1"
                            },
                        "1":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "1",
                                "Integrated on time": "2",
                                "Integrated after 8 days": "0",
                                "Not integrated after 8 days": "0",
                                "Others": "1"
                            }
                    }
            elif time_period == "day":
                expected_output = {
                    "0":
                        {
                            "time_period": f'{late_event_datetime.strftime("%Y-%m-%d")}',
                            "In flight": "0",
                            "Integrated on time": "0",
                            "Integrated after 8 days": "2",
                            "Not integrated after 8 days": "1",
                            "Others": "1"
                        },
                    "1":
                        {
                            "time_period": f'{on_time_event_datetime.strftime("%Y-%m-%d")}',
                            "In flight": "1",
                            "Integrated on time": "2",
                            "Integrated after 8 days": "0",
                            "Not integrated after 8 days": "0",
                            "Others": "1"
                        },
                }

            expected_values = expected_output

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
    def test_gp2gp_integration_8_days_report_trending_percentage(self, time_period):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now() - timedelta(days=30)
        report_end = generate_report_end_date()
        cutoff = "0"

        # Calculate event date times
        on_time_event_datetime = datetime_utc_now() - timedelta(days=7)
        late_event_datetime = datetime_utc_now() - timedelta(days=9)

        try:
            # Generate events
            integration_outcomes = ["INTEGRATED", "INTEGRATED_AND_SUPPRESSED"]
            registration_event_datetime_list = [on_time_event_datetime, late_event_datetime]

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
                                reason="testOverallPercentage"
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

                # Successful Integration
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
                                payload=create_integration_payload(outcome=outcome)

                            )),
                        sourcetype="myevent"
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_integration_8_days_trending_report/gp2gp_integration_8_days_trending_report_percentage"
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_output = {}
            # Calculate expected output based on dynamic datetime used in test set up
            if time_period == "month":
                current_month_start = datetime_utc_now().replace(day=1)

                if current_month_start < on_time_event_datetime and current_month_start < late_event_datetime:
                    # Total number of eligible transfers in timeframe = 8
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%Y-%m")}',
                                "In flight": "12.50",
                                "Integrated on time": "25.00",
                                "Integrated after 8 days": "25.00",
                                "Not integrated after 8 days": "12.50",
                                "Others": "25.00"
                            },
                    }
                elif late_event_datetime < on_time_event_datetime < current_month_start:
                    # Total number of eligible transfers in timeframe = 8
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%Y-%m")}',
                                "In flight": "12.50",
                                "Integrated on time": "25.00",
                                "Integrated after 8 days": "25.00",
                                "Not integrated after 8 days": "12.50",
                                "Others": "25.00"
                            },
                    }
                elif late_event_datetime < current_month_start < on_time_event_datetime:
                    # Total number of eligible transfers before the start of month = 4
                    # Total number of eligible transfers after the start of month = 4
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-%m")}',
                                "In flight": "0.00",
                                "Integrated on time": "0.00",
                                "Integrated after 8 days": "50.00",
                                "Not integrated after 8 days": "25.00",
                                "Others": "25.00"
                            },
                        "1":
                            {
                                "time_period": f'{datetime_utc_now().strftime("%Y-%m")}',
                                "In flight": "25.00",
                                "Integrated on time": "50.00",
                                "Integrated after 8 days": "0.00",
                                "Not integrated after 8 days": "0.00",
                                "Others": "25.00"
                            },
                    }
            elif time_period == "week":
                late_event_week_start = late_event_datetime.isocalendar().week
                on_time_event_week_start = on_time_event_datetime.isocalendar().week

                if late_event_week_start == on_time_event_week_start:
                    # Total number of eligible transfers in timeframe = 8
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "12.50",
                                "Integrated on time": "25.00",
                                "Integrated after 8 days": "25.00",
                                "Not integrated after 8 days": "12.50",
                                "Others": "25.00"
                            }
                    }
                else:
                    # Total number of eligible transfers in first reporting week = 4
                    # Total number of eligible transfers in second reporting week = 4
                    expected_output = {
                        "0":
                            {
                                "time_period": f'{late_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "0.00",
                                "Integrated on time": "0.00",
                                "Integrated after 8 days": "50.00",
                                "Not integrated after 8 days": "25.00",
                                "Others": "25.00"
                            },
                        "1":
                            {
                                "time_period": f'{on_time_event_datetime.strftime("%Y-Wk%W")}',
                                "In flight": "25.00",
                                "Integrated on time": "50.00",
                                "Integrated after 8 days": "0.00",
                                "Not integrated after 8 days": "0.00",
                                "Others": "25.00"
                            }
                    }
            elif time_period == "day":
                # Total number of eligible transfers on first day = 4
                # Total number of eligible transfers on second day = 4
                expected_output = {
                    "0":
                        {
                            "time_period": f'{late_event_datetime.strftime("%Y-%m-%d")}',
                            "In flight": "0.00",
                            "Integrated on time": "0.00",
                            "Integrated after 8 days": "50.00",
                            "Not integrated after 8 days": "25.00",
                            "Others": "25.00"
                        },
                    "1":
                        {
                            "time_period": f'{on_time_event_datetime.strftime("%Y-%m-%d")}',
                            "In flight": "25.00",
                            "Integrated on time": "50.00",
                            "Integrated after 8 days": "0.00",
                            "Not integrated after 8 days": "0.00",
                            "Others": "25.00"
                        },
                }

            expected_values = expected_output

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)
