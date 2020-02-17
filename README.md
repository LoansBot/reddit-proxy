# Reddit Proxy

This package is used to route requests to the reddit server while staying
within a rate-limit. This also handles request retrying and authorization
management (staying logged in).

## Environment Variables

- USER_AGENT: The user agent string to pass for all requests
- APPNAME: The application name for logging
- PGHOST: Host for logging
- PGPORT: Port for logging
- PGDATABASE: Database name for logging
- PGUSER: Username to login as for logging
- PGPASSWORD: Password to login with for logging
- AMQP_HOST: The AMQP host to connect to
- AMQP_PORT: The AMQP port to connect on
- AMQP_USERNAME: The username for the AMQP connection
- AMQP_PASSWORD: The password for the AMQP connection
- AMQP_VHOST: The AMQP virtual host
- AMQP_QUEUE: Which AMQP queue to listen on

## Folder Structure

- main.py: The main entrypoint
- endpoints/: Contains the requests to reddit
- handlers/: Contains the queue request handlers
