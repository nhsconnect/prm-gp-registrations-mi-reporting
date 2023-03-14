import os
from splunklib import client
from os import listdir
from os.path import isfile, join


splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)

path = os.path.join(os.path.dirname(__file__),
                    '../queries')

query_filenames = [f for f in listdir(path) if isfile(join(path, f))]

for query_filename in query_filenames:

    query_path = os.path.join(os.path.dirname(__file__),
                    '../queries',query_filename)
    
    queryString = open(query_path, encoding="utf-8").read()

    fileName = os.path.basename(query_path)

    if fileName in service.saved_searches:
        service.saved_searches.delete(fileName)

    service.saved_searches.create(
        fileName, queryString)
