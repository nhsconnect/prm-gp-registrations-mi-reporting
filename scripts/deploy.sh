docker build -t prm-gp-registrations-mi-reporting .
docker run --name prm-gp-registrations-mi-reporting \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_REGION=$AWS_REGION \
    -dit -v $(pwd):/usr/src/app prm-gp-registrations-mi-reporting