import os
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query


splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)


def teardown_function():
    """Function delete test_index."""
    service.indexes.delete("test_index")


def test_reporting_window_then_return_event_within() -> None:
    """Function create test index."""
    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="WITHIN_REPORT_WINDOW",
                registration_event_datetime="2023-03-10T00:00:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="OUTSIDE_REPORT_WINDOW",
                registration_event_datetime="2023-03-20T00:00:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    test_query = get_search('gp2gp_reporting_window')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId',
                    telemetry) == 'WITHIN_REPORT_WINDOW'


def test_reporting_window_as_savedsearch():
    index = get_or_create_index("test_index", service)

    service.saved_searches.create(
        'gp2gp_reporting_window', get_search('gp2gp_reporting_window'))

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="WITHIN_REPORT_WINDOW",
                registration_event_datetime="2023-03-10T00:00:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="OUTSIDE_REPORT_WINDOW",
                registration_event_datetime="2023-03-20T00:00:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    test_query = get_search('gp2gp_reporting_proccess')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(test_query, service)
    service.saved_searches.delete('gp2gp_reporting_window')
    print(jq.all('.[]._raw | fromjson.registrationEventDateTime', telemetry))

    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId',
                    telemetry) == 'WITHIN_REPORT_WINDOW'


def get_search(search_name):
    path = os.path.join(os.path.dirname(__file__),
                        '../queries', f'{search_name}.splunk')
    return open(path, encoding="utf-8").read()


def savedsearch(test_query):
    return "search "+test_query


def test_business_process_report_integrated_within_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type="REGISTRATIONS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-14T10:00:00",
                event_type="EHR_INTEGRATIONS"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "10",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-20"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "INTERGRATED_LESS_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_not_integrated_within_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_LESS_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type="REGISTRATIONS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_LESS_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "7",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-20"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "NOT_INTERGRATED_LESS_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_integrated_over_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type="REGISTRATIONS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-19T10:00:00",
                event_type="EHR_INTEGRATIONS"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "15",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "INTERGRATED_MORE_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_not_integrated_over_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type="REGISTRATIONS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type="READY_TO_INTEGRATE_STATUSES"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "15",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert    

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "NOT_INTERGRATED_MORE_THAN_8_DAYS") | .count',
                    telemetry) == '1'
