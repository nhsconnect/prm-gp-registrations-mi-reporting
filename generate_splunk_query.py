import argparse
from helpers.splunk import generate_splunk_query_from_report

# helper script to translate .splunk files in reports folder into runnable splunk queries
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--report", required=True, help="path to the report from reports folder")

args = vars(ap.parse_args())

generate_splunk_query_from_report(None, args['report'])
