from urllib.parse import urljoin
from typing import Optional

class SplunkConfig:

    @property
    def splunk_scheme(self):
        return self._scheme

    @property
    def splunk_host(self):
        return self._splunk_host

    @property
    def splunk_port(self):
        return self._splunk_port

    @property
    def splunk_namespace(self):
        return self._splunk_namespace
    
    @property
    def splunk_admin_username(self):
        return self._splunk_admin_username
    
    @property
    def splunk_token(self):
        return self._splunk_token
    
    @property
    def splunk_app_id(self):
        return self._splunk_app_id
    
    @property
    def s3_bucket_name(self):
        return self._s3_bucket_name       
    
    

    def __init__(self, splunk_host: str, splunk_port: int, splunk_admin_username: str, splunk_token: str, s3_bucket_name: str, splunk_scheme = 'https', splunk_app_id: Optional[str]=None):
        self._splunk_scheme = splunk_scheme
        self._splunk_host = splunk_host
        self._splunk_port = splunk_port
        self._splunk_admin_username = splunk_admin_username
        self._splunk_token = splunk_token
        self._splunk_app_id = splunk_app_id
        self._s3_bucket_name = s3_bucket_name

    # def __init__(self, splunk_api_url_parameter_store_value: str, splunk_token: str, s3_bucket_name: str):

    #     # splunk_api_url_parameter_store_value e.g "https://my_splunk_host:8089/servicesNS/splunk_admin_user/my_app_name/search/jobs/export"

    #     if splunk_api_url_parameter_store_value.startswith('https'):
    #         self._scheme = 'https'
    #     elif splunk_api_url_parameter_store_value.startswith('http'):
    #         self._scheme = 'http'
    #     else:
    #         self._scheme = None

    #     if (self._scheme is not None):
    #         url = splunk_api_url_parameter_store_value.replace(self._scheme +'://', '')

    #     scheme_split = url.split(':', 1)
    #     self._splunk_host = scheme_split[0]
    #     self._splunk_port = int(scheme_split[1][0:4])

    #     path_split = url.split("/")
    #     self._splunk_namespace = path_split[1]
    #     self._splunk_admin_username = path_split[2]
    #     self._splunk_app_id = path_split[3]

    #     self._splunk_token = splunk_token
    #     self._s3_bucket_name = s3_bucket_name        

    def get_base_api_url(self):
        
        return self.splunk_scheme + '://' + self.splunk_host + ":" + str(self._splunk_port)+ '/' + self.splunk_namespace + '/' + self.splunk_admin_username + '/' + self.splunk_app_id