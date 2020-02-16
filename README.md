# Reddit Proxy

This package is used to route requests to the reddit server while staying
within a rate-limit. This also handles request retrying and authorization
management (staying logged in).

## Environment Variables

- USER_AGENT: the user agent string to pass for all requests
