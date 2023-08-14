import pytest
import json
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_ehr_response_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time, generate_report_start_date, generate_report_end_date
import uuid


class TestPlaceholderBreakdownGraph(TestBase):

    @pytest.mark.parametrize("placeholders,expected_output", [
        (5, {"1-5 placeholders": 1, "6-10 placeholders": 0, "11-15 placeholders": 0, "16-20 placeholders": 0, "21+ placeholders": 0}),
        (6, {"1-5 placeholders": 0, "6-10 placeholders": 1, "11-15 placeholders": 0, "16-20 placeholders": 0, "21+ placeholders": 0}),
        (11, {"1-5 placeholders": 0, "6-10 placeholders": 0, "11-15 placeholders": 1, "16-20 placeholders": 0, "21+ placeholders": 0}),
        (16, {"1-5 placeholders": 0, "6-10 placeholders": 0, "11-15 placeholders": 0, "16-20 placeholders": 1, "21+ placeholders": 0}),
        (21, {"1-5 placeholders": 0, "6-10 placeholders": 0, "11-15 placeholders": 0, "16-20 placeholders": 0, "21+ placeholders": 1}),
    ])
    def test_count_of_placeholders(self, placeholders, expected_output):

        self.LOG.info(f"placeholders: {placeholders}")

        # Arrange
        index_name, index = self.create_index()

        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "1"

        try:
            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=placeholders)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:30:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_placeholder_snapshot_report/gp2gp_placeholders_breakdown_graph_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = expected_output
            self.LOG.info(f"output: {expected_output}")            

         
            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)
              

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("placeholders,expected_output", [
        (5, {"1-5 placeholders": "100.00", "6-10 placeholders": "0.00", "11-15 placeholders": "0.00", "16-20 placeholders": "0.00", "21+ placeholders": "0.00"}),
        (6, {"1-5 placeholders": "0.00", "6-10 placeholders": "100.00", "11-15 placeholders": "0.00", "16-20 placeholders": "0.00", "21+ placeholders": "0.00"}),
        (11, {"1-5 placeholders": "0.00", "6-10 placeholders": "0.00", "11-15 placeholders": "100.00", "16-20 placeholders": "0.00", "21+ placeholders": "0.00"}),
        (16, {"1-5 placeholders": "0.00", "6-10 placeholders": "0.00", "11-15 placeholders": "0.00", "16-20 placeholders": "100.00", "21+ placeholders": "0.00"}),
        (21, {"1-5 placeholders": "0.00", "6-10 placeholders": "0.00", "11-15 placeholders": "0.00", "16-20 placeholders": "0.00", "21+ placeholders": "100.00"})
    ])
    def test_percentage_of_placeholders(self, placeholders, expected_output):

        self.LOG.info(f"placeholders: {placeholders}")

        # Arrange
        index_name, index = self.create_index()

        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "1"

        try:
            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=placeholders)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:30:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_placeholder_snapshot_report/gp2gp_placeholders_breakdown_graph_percentages')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

             # Assert
            expected_values = expected_output
            self.LOG.info(f"output: {expected_output}")            

         
            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)
