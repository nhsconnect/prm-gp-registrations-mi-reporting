class SplunkConfig:

    def __init__(self, splunk_host: str, splunk_admin_username: str, splunk_token: str, splunk_app_id: str, s3_bucket_name: str):
        self._splunk_host = splunk_host
        self._splunk_admin_username = splunk_admin_username
        self._splunk_token = splunk_token
        self._splunk_app_id = splunk_app_id,
        self._s3_bucket_name = s3_bucket_name
