import os
from os import listdir
from os.path import isfile, join
import urllib.parse
from pathlib import Path
import requests
from requests.compat import urljoin

# set by pipeline
splunk_host = os.environ.get('SPLUNK_HOST')
splunk_admin_username = os.environ.get('SPLUNK_ADMIN_USERNAME')
splunk_token = os.environ['SPLUNK_TOKEN']



def check_env_variable(env_var: str) -> None:
    try:
        os.environ[env_var]
    except KeyError:
        print(f'Please set the environment variable: {env_var}')


class SplunkQueryError(RuntimeError):
    pass


def make_splunk_request(name, code):

    print(f'splunk_host: {splunk_host}')

    # API reference - https://docs.splunk.com/Documentation/Splunk/9.0.4/RESTREF
    create_dashboard_url = f'/servicesNS/{splunk_admin_username}/search/data/ui/views'

    url = urljoin(splunk_host, create_dashboard_url)

    headers = {"Authorization": f"Bearer {splunk_token}"}

    new_dashboard_data = urllib.parse.urlencode({
        "name": name,
        "eai:data": code
    })

    response = requests.post(url, headers=headers,
                             data=new_dashboard_data, verify=False, timeout=10)

    print(f'response: {response.status_code}')

    if response.status_code != 201:
        raise SplunkQueryError(
            f"Splunk request returned status code: {response.status_code} \
                with reason: {response.reason}")


# check essential env variables
check_env_variable("SPLUNK_HOST") # e.g. https://localhost:8089
check_env_variable("SPLUNK_ADMIN_USERNAME") # user with admin role
check_env_variable("SPLUNK_TOKEN") # token created with splunk

# loop through dashboard files
path = os.path.join(os.path.dirname(__file__),
                    '../dashboards')

dashboard_filenames = [f for f in listdir(path) if isfile(join(path, f))]

for dashboard_filename in dashboard_filenames:

    dashboard_path = os.path.join(os.path.dirname(__file__),
                                  '../dashboards', dashboard_filename)

    # get the dashboard xml as a string
    dashboard_string = open(dashboard_path, encoding="utf-8").read()

    # get filename without extension
    fileName = Path(dashboard_path).stem

    # create dashboard
    make_splunk_request(fileName, dashboard_string)
