import logging
from chalice import Chalice

from chalicelib.deploy_dashboards import deploy_dashboards
from chalicelib.deploy_reports import deploy_reports

app = Chalice(app_name='mi-dashboard-deployer')
logger = logging.getLogger("Dashboard-logging")
logger.setLevel(logging.DEBUG)


@app.lambda_function(name='splunk-uploader')
def main(event, context):
    logger.info("deploying saved searches...")
    deploy_reports()
    logger.info("deploying dashboards...")
    deploy_dashboards()

    
