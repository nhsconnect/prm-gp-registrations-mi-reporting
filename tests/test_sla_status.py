import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload,  create_transfer_compatibility_payload
from datetime import datetime, timedelta
from helpers.datetime_helper import datetime_utc_now
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase,EventType


class TestSlaStatus(TestBase):

    def test_total_transfer_time_outside_sla_24_hours(self):

        # Arrange

        index_name, index = self.create_index()       

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:

            # reporting window
            yesterday = datetime_utc_now() - timedelta(hours=24)
            tomorrow = datetime_utc_now() + timedelta(hours=24)

            # test requires a datetime less than 24hrs
            now_minus_23_hours = datetime_utc_now() - timedelta(hours=23, minutes=0)
            self.LOG.info(f"now_minus_20_mins: {now_minus_23_hours}")

            # test - #1

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='outside_sla_24_hours_1',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='inside_sla_24_hours_1',
                        registration_event_datetime=now_minus_23_hours.strftime(
                            "%Y-%m-%dT%H:%M:%S"),  # needs to be within 24 hours
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_2_outside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_2_outside_sla',
                        registration_event_datetime="2023-03-15T09:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_2_inside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_2_inside_sla',
                        registration_event_datetime="2023-03-10T11:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #3

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_outside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_outside_sla',
                        registration_event_datetime="2023-03-15T09:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_outside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED")
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_inside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_inside_sla',
                        registration_event_datetime="2023-03-10T11:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_3_inside_sla',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            # Act

            test_query =  self.get_search('gp2gp_sla_outcomes')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .totalTransferTimeOutsideSla24Hours=="3" )', telemetry)

        finally:
            self.delete_index(index_name)            


    def test_ehr_sending_outside_sla(self):

        # Arrange

        index_name, index = self.create_index()

        try:

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            # test - #1 - outside sla

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_1',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #2 - inside sla

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_2',
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #3 - outside sla READY_TO_INTEGRATE

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T11:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #4 - inside sla READY_TO_INTEGRATE

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T09:05:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test - #5 - inside sla INTEGRATED

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_integrated',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_integrated',
                        registration_event_datetime="2023-03-10T09:05:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_integrated',
                        registration_event_datetime="2023-03-10T10:01:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_integrated',
                        registration_event_datetime="2023-03-10T10:30:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            # test - #6 - outside sla INTEGRATED

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_integrated',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_integrated',
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_integrated',
                        registration_event_datetime="2023-03-10T10:01:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_integrated',
                        registration_event_datetime="2023-03-10T10:30:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            # test #7 - EHR_SENT - outside sla

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_ehr_sent',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_outside_sla_ehr_sent',
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #8 - EHR_SENT - inside sla

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_ehr_sent',
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_ehr_sending_inside_sla_ehr_sent',
                        registration_event_datetime="2023-03-10T09:15:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.get_search('gp2gp_sla_outcomes')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_ehr_sending_outside_sla=="4" )', telemetry)

        finally:

            self.delete_index(index_name)


    def test_ehr_requesting_outside_sla(self):

        # Arrange

        index_name, index = self.create_index()

        try:
            # test #1.a - Eligibile for transfer outside SLA

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_ehr_requesting_outside_sla_test#1.a",
                        registration_event_datetime="2023-03-10T09:15:00",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            # test #1.b - Eligibile for transfer inside SLA

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_ehr_requesting_outside_sla_test#1.b",
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            # test #2.a - READY_TO_INTEGRATE outside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#2.a'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:30:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #2.b - READY_TO_INTEGRATE inside SLA

            conversation_id = 'test_ehr_requesting_inside_sla_test#2.b'

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #3.a - INTEGRATED outside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#3.a'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:30:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #3.b - INTEGRATED inside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#3.b'

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #4.a - EHR_SENT outside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#4.a'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:30:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #4.b - EHR_SENT inside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#4.b'

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T10:00:00",
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #5.a - EHR_REQUESTED outside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#5.a'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:00:00",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:30:00",
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # test #5.b - EHR_REQUESTED inside SLA

            conversation_id = 'test_ehr_requesting_outside_sla_test#5.b'

            # test requires a datetime less than 20mins
            now_minus_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=15)
            self.LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=now_minus_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP"
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.get_search('gp2gp_sla_outcomes')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_ehr_requesting_outside_sla=="5" )', telemetry)

        finally:
            self.delete_index(index_name)
            
