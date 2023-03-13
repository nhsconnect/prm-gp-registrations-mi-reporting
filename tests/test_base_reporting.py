import os
import json
import os
from splunklib import client
import jq
from helpers.splunk import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query
from time import sleep

splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)


def teardown_function():
    service.indexes.delete("test_index")


def test_reporting_window_then_return_event_within():
    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "WITHIN_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-10T00:00:00"
            )),
            sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "OUTSIDE_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-20T00:00:00"
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

    telemetry = get_telemetry_from_splunk("search "+test_query, service)
    
    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId', telemetry) == 'WITHIN_REPORT_WINDOW'


def test_reporting_window_as_savedsearch():
    index = get_or_create_index("test_index", service)

    service.saved_searches.create('gp2gp_reporting_window', get_search('gp2gp_reporting_window'))

    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "WITHIN_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-10T00:00:00"
            )),
            sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "OUTSIDE_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-20T00:00:00"
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
    assert jq.first('.[]._raw | fromjson.conversationId', telemetry) == 'WITHIN_REPORT_WINDOW'


def get_search(search_name):
    path = os.path.join(os.path.dirname(__file__), '../queries', f'{search_name}.splunk')
    return open(path).read()