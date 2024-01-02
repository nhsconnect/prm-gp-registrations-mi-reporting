import json
import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time, generate_report_start_date, \
    generate_report_end_date



class TestTechnicalFailuresRawDataTableOutputs(TestBase):

    def test_gp2gp_technical_failures_raw_data_table_output(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        error_type_and_failure_point = [
            ("06", "EHR Ready to Integrate"),
            ("06", "EHR Requested"),
            ("06", "EHR Response"),
            ("07", "Endpoint Lookup"),
            ("07", "Other"),
            ("07", "Patient General Update"),
            ("09", "Patient Trace"),
            ("09", "EHR Ready to Integrate"),
            ("09", "EHR Requested"),
            ("Integration failure", "EHR Response"),
            ("Integration failure", "Endpoint Lookup"),
            ("Integration failure", "Other"),
        ]

        try:
            for (error_type, failure_point) in error_type_and_failure_point:

                # create event
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="test_"+error_type+"_"+failure_point.replace(" ", "_"),
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                # create error
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="test_"+error_type+"_"+failure_point.replace(" ", "_"),
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=error_type,
                                errorDescription="random error",
                                failurePoint=failure_point
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_snapshot_report/"
                "gp2gp_technical_failures_snapshot_raw_data_table")

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff
                # "$column$": "Successfully integrated"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            conversation_ids = ["test_"+error_type+"_"+failure_point.replace(" ", "_") for (error_type, failure_point)
                                in error_type_and_failure_point]
            for idx in range(len(conversation_ids)):
                assert jq.first(
                    f".[{idx}] "
                    + f'| select( .conversation_id == "{conversation_ids[idx]}")'
                    + f'| select( .report_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .reporting_practice_ods_code == "A00029")'
                    + f'| select( .requesting_practice_ods_code == "A00029")'
                    + f'| select( .sending_practice_ods_code == "B00157")'
                    + f'| select( .error_code == "{error_type_and_failure_point[idx][0]}")'
                    + f'| select( .failure_point == "{error_type_and_failure_point[idx][1]}")'
                    + f'| select( .error_desc == "random error")'
                    + f'| select( .broken_24h_sla == "0")'
                    + f'| select( .broken_ehr_sending_sla == "0")'
                    + f'| select( .broken_ehr_requesting_sla == "0")'
                    , telemetry
                )

        finally:
            self.delete_index(index_name)


    @pytest.mark.parametrize("sla_status",
                             ["broken_ehr_requesting_sla",
                              "broken_ehr_sending_sla",
                              "broken_24h_sla",
                              "No_sla_broken"
                              ])
    def test_gp2gp_technical_failures_raw_data_table_broken_24h_sla(self, sla_status):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            error_type = "07"
            failure_point = "Other"
            conversation_id = "test_"+sla_status

            # create event

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(internalTransfer=False,
                                                                      transferCompatible=True)
                    )),
                sourcetype="myevent")

            if sla_status in ["broken_ehr_sending_sla", "broken_24h_sla", "No_sla_broken"]:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversation_id,
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_REQUESTS.value,
                        )),
                    sourcetype="myevent")

            if sla_status in ["broken_24h_sla", "No_sla_broken"]:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversation_id,
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_RESPONSES.value,
                        )),
                    sourcetype="myevent")

            if sla_status in ["No_sla_broken"]:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversation_id,
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

            # create error
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode=error_type,
                            errorDescription="random error",
                            failurePoint=failure_point
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_snapshot_report/"
                "gp2gp_technical_failures_snapshot_raw_data_table")

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff
                # "$column$": "Successfully integrated"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            broken_24h_sla_value = "0"
            broken_ehr_sending_sla_value = "0"
            broken_ehr_requesting_sla_value = "0"

            if sla_status == "broken_ehr_requesting_sla":
                broken_ehr_requesting_sla_value = "1"

            if sla_status == "broken_ehr_sending_sla":
                broken_ehr_sending_sla_value = "1"

            if sla_status == "broken_24h_sla":
                broken_24h_sla_value = "1"

            assert jq.first(
                f".[] "
                + f'| select( .conversation_id == "{conversation_id}")'
                + f'| select( .report_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .reporting_practice_ods_code == "A00029")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")'
                + f'| select( .error_code == "{error_type}")'
                + f'| select( .failure_point == "{failure_point}")'
                + f'| select( .error_desc == "random error")'
                + f'| select( .broken_24h_sla == "{broken_24h_sla_value}")'
                + f'| select( .broken_ehr_sending_sla == "{broken_ehr_sending_sla_value}")'
                + f'| select( .broken_ehr_requesting_sla == "{broken_ehr_requesting_sla_value}")'
                , telemetry
            )

        finally:
            self.delete_index(index_name)
