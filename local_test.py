import os
import boto3
import logging
from chalicelib.splunk_config import SplunkConfig
from chalicelib.deploy_reports import deploy_reports

splunkConfig = SplunkConfig(
    splunk_scheme='https',
    splunk_host='localhost',
    splunk_port=8089,
    splunk_admin_username='lorenzo',
    splunk_token='eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJsb3JlbnpvIGZyb20gbG9yZW56by5mZWNjaSdzIE1hYyIsInN1YiI6ImxvcmVuem8iLCJhdWQiOiJkZXYiLCJpZHAiOiJTcGx1bmsiLCJqdGkiOiIzNWM5N2I0N2VjZjVkMDJkYTc2NjVhMjgyYjg2ZWQyMzRhZjk0MWMxNmUyODdjMGNjYjQ2MjgxN2Y2ODMxYjc3IiwiaWF0IjoxNjgxMzA0ODAxLCJleHAiOjE2ODM4OTY4MDEsIm5iciI6MTY4MTMwNDgwMX0._N3Z0UURjO2Y4E-g8QFdVd0JUZEQd0Qw3Y1FGGPAPILIeLzTaqLxr3JJ0yrwJt0rHYQL73zYrFL8FDdP8fWyXA',    
    s3_bucket_name='foo')


# splunkConfig = SplunkConfig(
#     splunk_scheme='https',
#     splunk_host='nhsdigital.splunkcloud.com',
#     splunk_port=8089,
#     splunk_admin_username='nhsd_svuser_gp2gp',
#     splunk_token='eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJzdmtlMUBoc2NpYy5nb3YudWsgZnJvbSBzaC1pLTA1OWE2ZmQzMjczZDI4MjgzIiwic3ViIjoibmhzZF9zdnVzZXJfZ3AyZ3AiLCJhdWQiOiJTcGx1bmsgQVBJIGZvciBHUDJHUCB0ZWFtIiwiaWRwIjoiU3BsdW5rIiwianRpIjoiZjAzNGUyOWNmODBjMGJjYmNlYTNkYmFkMzMwNWY4MmE1YzAxNGYwNTFmZmQxM2VmODYzMDdjYTFlMDU4MGY2ZiIsImlhdCI6MTYzMzU5MTE3NCwiZXhwIjoxOTQ5MTczMTQwLCJuYnIiOjE2MzM1OTExNzR9.bxkTDNxWSggx5SES81hQBhWnUXDnnmBCjDkJNU69bXMkdqrfF6VhFzy677dUBVlv-JERtpbGpv5s3kQt1PDihw',    
#     s3_bucket_name='foo')


print("deploying reports...")
deploy_reports(splunkConfig)



