import os
import json
import pytest
from time import sleep
from splunklib import client
import jq
from helpers.splunk import (
    create_ehr_response_payload,
    create_registration_payload,
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_transfer_compatibility_payload, create_error_payload,
)
from tests.test_base import TestBase, EventType
from datetime import timedelta, datetime
from helpers.datetime_helper import (
    datetime_utc_now,
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
)


class TestTransferStatusReportBase(TestBase):

    @pytest.mark.parametrize(
        "cutoff, registrationStatus",
        [
            (1, "REGISTRATION"),
            (7, "EHR_REQUESTED"),
            (11, "EHR_SENT"),
            (19, "READY_TO_INTEGRATE"),
        ],
    )
    def test_cutoffs(self, cutoff, registrationStatus):
        """This test ensures that new conversations are at a different stage based on cutoff."""

        self.LOG.info(f"cutoff:{cutoff}, regstat:{registrationStatus}")

        # Arrange
        index_name, index = self.create_index()

        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=2)

        try:
            conversationId = "test_cutoffs"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=1), time="08:00:00"
                        ),
                        event_type=EventType.REGISTRATIONS.value,
                        payload=create_registration_payload(),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=8), time="05:03:00"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=12), time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=20), time="03:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": str(cutoff),
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.first(
                f'.[] | select( .registrationStatus=="{registrationStatus}")', telemetry
            )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "status, outcome",
        [
            ("ERROR", "Not eligible for electronic transfer"),
            ("REGISTRATION", "Not eligible for electronic transfer"),
            ("REGISTRATION+ERROR", "Not eligible for electronic transfer"),
            ("TRANSFER_COMPAT_FALSE", "Not eligible for electronic transfer"),
            ("TRANSFER_COMPAT_TRUE", "In progress"),
            ("EHR_REQUESTS", "In progress"),
            ("EHR_REQUESTS+ERROR", "Technical failure"),
            ("EHR_RESPONSES", "In progress"),
            ("EHR_RESPONSES+ERROR", "Technical failure"),
            ("READY_TO_INTEGRATE_STATUSES", "Awaiting integration"),
            ("EHR_INTEGRATIONS+INTEGRATION_OUTCOME_FAIL", "Technical failure"),
            ("EHR_INTEGRATIONS+INTEGRATION_OUTCOME_REJECT", "Rejected"),
            ("EHR_INTEGRATIONS+INTEGRATION_OUTCOME_INTEGRATED", "Successful integration"),
        ],
    )
    def test_outcome(self, status, outcome):
        """This test ensures that new conversations are at a different stage based on cutoff."""

        cutoff = 1

        # Arrange
        index_name, index = self.create_index()

        report_start = generate_report_start_date()
        report_end = generate_report_end_date()

        event_list = ["ERROR"]

        try:
            conversationId = "test_outcome"

            if status not in event_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=1), time="08:00:00"
                            ),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload(
                                dtsMatched=False if status == "REGISTRATION" else True
                            ),
                        )
                    ),
                    sourcetype="myevent",
                )

                event_list.extend(["REGISTRATION", "REGISTRATION+ERROR"])

            if status not in event_list:
                trans_compat_status = False if status == "TRANSFER_COMPAT_FALSE" else True
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=1), time="08:00:00"
                            ),
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=trans_compat_status
                            ),
                        )
                    ),
                    sourcetype="myevent",
                )
                event_list.extend(["TRANSFER_COMPAT_FALSE", "TRANSFER_COMPAT_TRUE"])

            if status not in event_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=8), time="05:03:00"
                            ),
                            event_type=EventType.EHR_REQUESTS.value,
                        )
                    ),
                    sourcetype="myevent",
                )
                event_list.extend(["EHR_REQUESTS+ERROR", "EHR_REQUESTS"])

            if status not in event_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=12), time="05:00:00"
                            ),
                            event_type=EventType.EHR_RESPONSES.value,
                            payload=create_ehr_response_payload(number_of_placeholders=2),
                        )
                    ),
                    sourcetype="myevent",
                )
                event_list.extend(["EHR_RESPONSES+ERROR", "EHR_RESPONSES"])

            if status not in event_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=20), time="03:00:00"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        )
                    ),
                    sourcetype="myevent",
                )
                event_list.append("READY_TO_INTEGRATE_STATUSES")

            if status not in event_list:
                if "FAIL" in status:
                    integration_outcome = "FAILED_TO_INTEGRATE"
                elif "REJECT" in status:
                    integration_outcome = "REJECTED"
                elif "INTEGRATED" in status:
                    integration_outcome = "INTEGRATED"
                else:
                    raise ValueError("Unrecognised status.")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=20), time="03:00:00"
                            ),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(
                                outcome=integration_outcome
                            )
                        )
                    ),
                    sourcetype="myevent",
                )

            if "ERROR" in status:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(
                                date=report_start.replace(day=20), time="03:00:00"
                            ),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="99",
                                errorDescription="outcome failure test",
                                failurePoint="Unknown"
                            )
                        )
                    ),
                    sourcetype="myevent",
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": str(cutoff),
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            # self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.first(
                f'.[] | select( .outcome=="{outcome}")', telemetry
            )

        finally:
            self.delete_index(index_name)
