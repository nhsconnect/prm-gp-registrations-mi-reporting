import datetime
import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import create_date_time
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_ehr_response_payload
from tests.test_base import TestBase, EventType


class TestPlaceholderTrendingBreakdownGraph(TestBase):

    @pytest.mark.parametrize("time_period, expected_output", [
        ("month", {"0": {"time_period": "23-02",
                         "1-5 placeholders": "2",
                         "6-10 placeholders": "1",
                         "11-15 placeholders": "1",
                         "16-20 placeholders": "1",
                         "21+ placeholders": "1"}
                   }
         ),
        ("week", {"0": {"time_period": "23-02-05",
                        "1-5 placeholders": "1",
                        "6-10 placeholders": "1",
                        "11-15 placeholders": "1",
                        "16-20 placeholders": "1",
                        "21+ placeholders": "0"
                        },
                  "1": {"time_period": "23-02-06",
                        "1-5 placeholders": "1",
                        "6-10 placeholders": "0",
                        "11-15 placeholders": "0",
                        "16-20 placeholders": "0",
                        "21+ placeholders": "1"
                        }
                  }
         ),
        ("day", {"0": {"time_period": "23-02-02",
                       "1-5 placeholders": "1",
                       "6-10 placeholders": "0",
                       "11-15 placeholders": "0",
                       "16-20 placeholders": "0",
                       "21+ placeholders": "0"
                       },
                 "1": {"time_period": "23-02-03",
                       "1-5 placeholders": "0",
                       "6-10 placeholders": "1",
                       "11-15 placeholders": "0",
                       "16-20 placeholders": "0",
                       "21+ placeholders": "0"
                       },
                 "2": {"time_period": "23-02-04",
                       "1-5 placeholders": "0",
                       "6-10 placeholders": "0",
                       "11-15 placeholders": "1",
                       "16-20 placeholders": "0",
                       "21+ placeholders": "0"
                       },
                 "3": {"time_period": "23-02-05",
                       "1-5 placeholders": "0",
                       "6-10 placeholders": "0",
                       "11-15 placeholders": "0",
                       "16-20 placeholders": "1",
                       "21+ placeholders": "0"
                       },
                 "4": {"time_period": "23-02-06",
                       "1-5 placeholders": "0",
                       "6-10 placeholders": "0",
                       "11-15 placeholders": "0",
                       "16-20 placeholders": "0",
                       "21+ placeholders": "1"
                       },
                 "5": {"time_period": "23-02-08",
                       "1-5 placeholders": "1",
                       "6-10 placeholders": "0",
                       "11-15 placeholders": "0",
                       "16-20 placeholders": "0",
                       "21+ placeholders": "0"
                       }
                 }
         ),
    ])
    def test_gp2gp_placeholder_breakdown_trending_count(self, time_period, expected_output):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=2, day=1)
        report_end = datetime.datetime(year=2023, month=2, day=28)
        cutoff = "0"

        number_of_placeholders_per_transfer = [5, 6, 11, 16, 21]

        try:
            for idx, placeholders in enumerate(number_of_placeholders_per_transfer):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_placeholder_breakdown_{idx}',
                            registration_event_datetime=create_date_time(
                                date=report_start + timedelta(days=idx + 1), time="08:00:00"),
                            event_type=EventType.EHR_RESPONSES.value,
                            payload=create_ehr_response_payload(number_of_placeholders=placeholders)
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_placeholder_breakdown_{idx}',
                            registration_event_datetime=create_date_time(
                                date=report_start + timedelta(days=idx + 1), time="09:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                        )),
                    sourcetype="myevent")

            # Additional transfer event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_placeholder_breakdown_ex",
                        registration_event_datetime=create_date_time(
                            date=report_start + timedelta(weeks=1), time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=5)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_placeholder_breakdown_ex",
                        registration_event_datetime=create_date_time(
                            date=report_start + timedelta(weeks=1), time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_placeholder_trending_report/gp2gp_placeholders_breakdown_graph_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)

            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
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

    @pytest.mark.parametrize("time_period, expected_output", [
        ("month", {"0": {"time_period": "23-02",
                         "1-5 placeholders": "33.33",
                         "6-10 placeholders": "16.67",
                         "11-15 placeholders": "16.67",
                         "16-20 placeholders": "16.67",
                         "21+ placeholders": "16.67"}
                   }
         ),
        ("week", {"0": {"time_period": "23-02-05",
                        "1-5 placeholders": "25.00",
                        "6-10 placeholders": "25.00",
                        "11-15 placeholders": "25.00",
                        "16-20 placeholders": "25.00",
                        "21+ placeholders": "0.00"
                        },
                  "1": {"time_period": "23-02-06",
                        "1-5 placeholders": "50.00",
                        "6-10 placeholders": "0.00",
                        "11-15 placeholders": "0.00",
                        "16-20 placeholders": "0.00",
                        "21+ placeholders": "50.00"
                        }
                  }
         ),
        ("day", {"0": {"time_period": "23-02-02",
                       "1-5 placeholders": "100.00",
                       "6-10 placeholders": "0.00",
                       "11-15 placeholders": "0.00",
                       "16-20 placeholders": "0.00",
                       "21+ placeholders": "0.00"
                       },
                 "1": {"time_period": "23-02-03",
                       "1-5 placeholders": "0.00",
                       "6-10 placeholders": "100.00",
                       "11-15 placeholders": "0.00",
                       "16-20 placeholders": "0.00",
                       "21+ placeholders": "0.00"
                       },
                 "2": {"time_period": "23-02-04",
                       "1-5 placeholders": "0.00",
                       "6-10 placeholders": "0.00",
                       "11-15 placeholders": "100.00",
                       "16-20 placeholders": "0.00",
                       "21+ placeholders": "0.00"
                       },
                 "3": {"time_period": "23-02-05",
                       "1-5 placeholders": "0.00",
                       "6-10 placeholders": "0.00",
                       "11-15 placeholders": "0.00",
                       "16-20 placeholders": "100.00",
                       "21+ placeholders": "0.00"
                       },
                 "4": {"time_period": "23-02-06",
                       "1-5 placeholders": "0.00",
                       "6-10 placeholders": "0.00",
                       "11-15 placeholders": "0.00",
                       "16-20 placeholders": "0.00",
                       "21+ placeholders": "100.00"
                       },
                 "5": {"time_period": "23-02-08",
                       "1-5 placeholders": "100.00",
                       "6-10 placeholders": "0.00",
                       "11-15 placeholders": "0.00",
                       "16-20 placeholders": "0.00",
                       "21+ placeholders": "0.00"
                       }
                 }
         ),
    ])
    def test_gp2gp_placeholder_breakdown_trending_percentage(self, time_period, expected_output):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=2, day=1)
        report_end = datetime.datetime(year=2023, month=2, day=28)
        cutoff = "0"

        number_of_placeholders_per_transfer = [5, 6, 11, 16, 21]

        try:
            for idx, placeholders in enumerate(number_of_placeholders_per_transfer):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_placeholder_breakdown_{idx}',
                            registration_event_datetime=create_date_time(
                                date=report_start + timedelta(days=idx + 1), time="08:00:00"),
                            event_type=EventType.EHR_RESPONSES.value,
                            payload=create_ehr_response_payload(number_of_placeholders=placeholders)
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_placeholder_breakdown_{idx}',
                            registration_event_datetime=create_date_time(
                                date=report_start + timedelta(days=idx + 1), time="09:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                        )),
                    sourcetype="myevent")

            # Additional transfer event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_placeholder_breakdown_ex",
                        registration_event_datetime=create_date_time(
                            date=report_start + timedelta(weeks=1), time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=5)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_placeholder_breakdown_ex",
                        registration_event_datetime=create_date_time(
                            date=report_start + timedelta(weeks=1), time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_placeholder_trending_report/gp2gp_placeholders_breakdown_graph_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)

            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
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
