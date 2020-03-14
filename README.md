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
- MIN_TIME_BETWEEN_REQUESTS_S: The number of seconds between requests to reddit.
- REDDIT_USERNAME: The username for reddit
- REDDIT_PASSWORD: The password for reddit
- REDDIT_CLIENT_ID: The client id for the app in reddit
- REDDIT_CLIENT_SECRET: THe client secret for the app in reddit

## Folder Structure

- main.py: The main entrypoint
- endpoints/: Contains the requests to reddit
- handlers/: Contains the queue request handlers

## Packet Structure

Requests

```json
{
    "type": "request_type",
    "response_queue": "my_response_queue",
    "uuid": "7c07f3c0-f62c-43a0-badc-ce89869547e2",
    "version_utc_seconds": 1581255042.707,
    "sent_at": 1581255043.000,
    "args": {},
    "style": {
        "2xx": { "operation": "copy" },
        "4xx": { "operation": "failure" },
        "5xx": { "operation": "retry", "ignore_version": false }
    },
    "ignore_version": false
}
```

Responses

```json
{
    "uuid": "7c07f3c0-f62c-43a0-badc-ce89869547e2",
    "type": "copy",
    "status": 200,
    "info": {}
}
```

The `request_type` typically corresponds to an alias for a reddit endpoint
(i.e., `user_listing`). Request types much match one of the fixed set of keys
known by the reddit proxy. Request types which are prefixed with an underscore
don't actually correspond to reddit API calls and are instead for configuration
and monitoring purposes - these only give `success` and `failure` responses.

The `style` argument may be omitted to get the above behavior. The response
queue may be omitted for no response. The valid operations are as follows:

- `copy`: The response queue object will include the status code and the
  handlers response.
- `success`: The response queue object will just indicate success, without the
  status code or body.
- `failure`: The response queue object will just indicate failure, without the
  status code or body.
- `retry`: The operation will be requeued. By default, the operation will be
  retried either until success, a newer version of the application connects
  to the given response queue, or the response is explicitly cleared. The
  operation will be retried with "ignore_version" set to false, unless the
  style specifies `"ignore_version": true`.

By default all operations are logged. `copy` and `success` default to `TRACE`
level, whereas `failure` and `retry` default to `WARN`. Logging for a request
for a given status code can be silenced by setting `log_level` to the special
value `NONE`. For example, the following disables logging except on failure,
which uses the `INFO` level:

```json
{
    "__comment": "other fields ommitted for simplicity",
    "style": {
        "2xx": { "operation": "copy", "log_level": "NONE" },
        "4xx": { "operation": "failure", "log_level": "INFO" },
        "5xx": { "operation": "retry", "log_level": "NONE" }
    }
}
```

The top-level `ignore_version` field should be false if the request should be
nacked without retries when the version is older than the newest version and
true if the version field should not be checked. As a general rule of thumb,
information requests should have `ignore_version` false whereas action requests
should have `ignore_version` true but the `retry` ignore version should always
be `false` for non-critical sections.

For example, when fetching a listing it would be complicated for the client to
recall the context for why it was requesting that listing through restarts and
there is no disadvantage to simply requeueing the request. However, when
posting comments it's complicated for it to requeue the request compared to
knowing that once the packet is sent to the queue, the bot will at least attempt
to post that comment once, however if a request has previously failed we'd
rather drop it than retry through restarts (in case it is failing due to a
programming error).

Setting ignore version to true on retries should only happen if the code is
extremely resilient, hence we're very confident only temporary issues would
cause it to fail.

Prefixing the response queue with `void` will cause the reddit proxy to never
send a response. There will be no way to confirm the success of the request.

### Special Request Types

Request types prefixed with an underscore have no "style" argument as they only
provide either success or failure and it's not configurable when these are
returned. These operations typically affect the state of the reddit proxy and
don't impact reddit itself.

- `_connect`: Essentially a no-op used to change the version number. Responds
  success if the connecter is at least as new as the previous newest version
  and failure otherwise. No arguments.
- `_ping`: Always returns success, useful for measuring ping or checking
  liveliness. Also used internally as a notification we have reached the
  tail of the queue since some previous event. No arguments.
