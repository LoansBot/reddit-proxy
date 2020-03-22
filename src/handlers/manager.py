"""This module is responsible for detecting handlers within this package and
forwarding the appropriate jobs to them.
"""
import os
import importlib
import json
from datetime import datetime, timedelta
import time
from auth import Auth
from reddit import Reddit
from lblogging import Level


VALID_OPERATIONS = {'copy', 'success', 'failure', 'retry'}
"""The list of valid operations within the style part of a packet"""

DEFAULT_STYLE = {
    '2xx': {'operation': 'copy', 'log_level': 'TRACE'},
    '4xx': {'operation': 'failure', 'log_level': 'WARN'},
    '5xx': {'operation': 'retry', 'log_level': 'WARN'}
}
"""The default style dict for responding to requests. Any missing info in the
style array is fetched from here."""

FALLBACK_STYLE = DEFAULT_STYLE['5xx']
"""In the extremely unlikely event we get a status code not described in
default style, we fall back to this style"""


def register_listeners(logger, amqp):
    """Main entry point to this file. Finds all the handlers and then
    subscribes to the appropriate queue with a callback which uses those
    handlers on top of some bookkeeping"""
    logger = logger.with_iden('handlers/manager.py')

    logger.print(Level.TRACE, 'Finding listeners...')
    logger.connection.commit()
    handlers = _get_handlers(logger)
    logger.connection.commit()
    logger.print(Level.TRACE, 'Listeners found, consuming events..')
    logger.connection.commit()

    listen_with_handlers(logger, amqp, handlers)


def listen_with_handlers(logger, amqp, handlers):
    """Uses the specified list of handlers when subscribing to the appropriate
    queue"""
    handlers_by_name = dict([(handler.name, handler) for handler in handlers])
    queue = os.environ['AMQP_QUEUE']
    response_queues = {}
    last_processed_at = None
    min_td_btwn_reqs = timedelta(seconds=float(os.environ['MIN_TIME_BETWEEN_REQUESTS_S']))

    def delay_for_reddit():
        if (last_processed_at is not None
                and (datetime.now() - last_processed_at) < min_td_btwn_reqs):
            req_sleep_time = min_td_btwn_reqs - (datetime.now() - last_processed_at)
            time.sleep(req_sleep_time.total_seconds())

    time_btwn_clean = timedelta(hours=1)
    remember_td = timedelta(days=1)
    last_cleaned_respqueues = datetime.now()

    reddit = Reddit()
    auth = None
    min_time_to_expiry = timedelta(minutes=15)

    channel = amqp.channel()
    channel.queue_declare(queue)
    for method_frame, properties, body_bytes in channel.consume(queue, inactivity_timeout=600):
        if (datetime.now() - last_cleaned_respqueues) > time_btwn_clean:
            last_cleaned_respqueues = datetime.now()
            for k in list(response_queues.keys()):
                val = response_queues[k]
                time_since_seen = datetime.now() - val['last_seen_at']
                if time_since_seen > remember_td:
                    logger.print(
                        Level.DEBUG,
                        'Forgetting about response queue {} - last saw it {} ago',
                        k, time_since_seen
                    )
                    del val[k]
            logger.connection.commit()

        if method_frame is None:
            logger.print(Level.TRACE, 'No messages in the last 10 minutes')
            logger.connection.commit()
            continue

        body_str = body_bytes.decode('utf-8')
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as exc:
            logger.exception(
                Level.WARN,
                'Received non-json packet! Error info: doc={}, msg={}, pos={}, lineno={}, colno={}',
                exc.doc, exc.msg, exc.pos, exc.lineno, exc.colno
            )
            logger.connection.commit()
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue

        if _detect_structure_errors_with_logging(logger, body_str, body):
            logger.connection.commit()
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue

        resp_info = response_queues.get(body['response_queue'])
        if resp_info is None:
            logger.print(
                Level.DEBUG,
                'New response queue {} detected at version {}',
                body['response_queue'], body['version_utc_seconds']
            )
            if not body['response_queue'].startswith('void'):
                channel.queue_declare(body['response_queue'])
            resp_info = {'version': body['version_utc_seconds']}
            response_queues[body['response_queue']] = resp_info
        elif not body.get('ignore_version') and body['version_utc_seconds'] < resp_info['version']:
            logger.print(
                Level.DEBUG,
                'Ignoring message to response queue {} with type {}; '
                'specified version={} is below current version={}',
                body['response_queue'], body['type'], body['version_utc_seconds'],
                resp_info['version']
            )
            logger.connection.commit()
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue
        elif body['version_utc_seconds'] > resp_info['version']:
            logger.print(
                Level.DEBUG,
                'Detected newer version for response queue {}, was {} and is now {}',
                body['response_queue'], resp_info['version'], body['version_utc_seconds']
            )
            resp_info['version'] = body['version_utc_seconds']

        logger.connection.commit()
        resp_info['last_seen_at'] = datetime.now()

        if body['type'] not in handlers_by_name:
            logger.print(
                Level.WARN,
                'Received request to response queue {} with an unknown type {}',
                body['response_queue'], body['type']
            )
            logger.connection.commit()
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue

        logger.print(
            Level.TRACE,
            'Processing request to response queue {} with type {} ({})',
            body['response_queue'], body['type'], body['uuid']
        )
        logger.connection.commit()

        if auth is None or auth.expires_at < (datetime.now() - min_time_to_expiry):
            logger.print(
                Level.TRACE,
                'Reauthenticating with reddit (expires at {})',
                auth.expires_at if auth is not None else 'None'
            )
            logger.connection.commit()
            delay_for_reddit()
            auth = _auth(reddit, logger)
            last_processed_at = datetime.now()
            if auth is None:
                logger.print(
                    Level.WARN,
                    'Failed to authenticate with reddit! Will nack, requeue=True'
                )
                logger.connection.commit()
                channel.basic_nack(method_frame.delivery_tag, requeue=True)
                continue

        handler = handlers_by_name[body['type']]
        if handler.requires_delay:
            delay_for_reddit()
        try:
            status, info = handler.handle(reddit, auth, body['args'])
        except:  # noqa: E722
            logger.exception(
                Level.WARN,
                'An exception occurred while processing request to response '
                'queue {} with type {}: body={}',
                body['response_queue'], body['type'], body
            )
            status = 'failure'
            info = None

        if handler.requires_delay:
            last_processed_at = datetime.now()
        handle_style = _get_handle_style(body.get('style'), status)

        logger.print(
            getattr(Level, handle_style['log_level']),
            'Got status {} to response type {} for queue {} ({}) - handling with operation {}',
            status, body['type'], body['response_queue'], body['uuid'], handle_style['operation']
        )
        logger.connection.commit()

        if status == 401:
            logger.print(
                Level.INFO,
                'Due to 401 status code, purging cached authorization information. '
                'It should not have expired until {}',
                auth.expires_at
            )
            logger.connection.commit()
            auth = None

        if body['response_queue'].startswith('void'):
            channel.basic_ack(method_frame.delivery_tag)
        elif handle_style['operation'] == 'copy':
            channel.basic_publish('', body['response_queue'], json.dumps({
                'uuid': body['uuid'],
                'type': 'copy',
                'status': status,
                'info': info
            }))
            channel.basic_ack(method_frame.delivery_tag)
        elif handle_style['operation'] == 'retry':
            new_bod = body.copy()
            new_bod['ignore_version'] = handle_style.get('ignore_version', False)
            channel.basic_publish('', queue, json.dumps(new_bod))
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
        elif handle_style['operation'] == 'success':
            channel.basic_publish('', body['response_queue'], json.dumps({
                'uuid': body['uuid'],
                'type': 'success'
            }))
            channel.basic_ack(method_frame.delivery_tag)
        else:
            if handle_style['operation'] != 'failure':
                logger.print(
                    Level.WARN,
                    'Unknown handle style {} to status {} to resposne queue {} for type {}'
                    ' - treating as failure',
                    handle_style['operation'], status, body['response_queue'], body['type']
                )
            channel.basic_publish('', body['response_queue'], json.dumps({
                'uuid': body['uuid'],
                'type': 'failure'
            }))
            channel.basic_nack(method_frame.delivery_tag, requeue=False)


def _auth(reddit, logger):
    raw_resp = reddit.login(
        os.environ['REDDIT_USERNAME'], os.environ['REDDIT_PASSWORD'],
        os.environ['REDDIT_CLIENT_ID'], os.environ['REDDIT_CLIENT_SECRET']
    )
    if raw_resp.status_code < 200 or raw_resp.status_code > 299:
        logger.print(
            Level.WARN,
            'Failed to login; got status code {}',
            raw_resp.status_code
        )
        return None

    logger.print(Level.DEBUG, 'Successfully relogged in')
    return Auth.from_response(raw_resp)


def _get_handle_style(style, status, defaults=DEFAULT_STYLE):
    if status == 'success':
        return {'operation': 'success', 'log_level': 'TRACE'}
    if status == 'failure':
        return {'operation': 'failure', 'log_level': 'TRACE'}

    if style is None:
        if defaults is None:
            raise Exception('should not get here - no style or fallback')
        return _get_handle_style(defaults, status, defaults=None)

    best_match = None
    if style.get(str(status)) is not None:
        best_match = style[str(status)]
    elif style.get(str(status)[0] + 'xx') is not None:
        best_match = style[str(status)[0] + 'xx']

    if best_match is None:
        if defaults is None:
            return FALLBACK_STYLE
        return _get_handle_style(defaults, status, defaults=None)

    if defaults is not None:
        best_match = best_match.copy()
        fill_with = _get_handle_style(style, status, defaults=None)
        for k, v in fill_with.items():
            if k not in best_match:
                best_match[k] = v

    return best_match


def _detect_structure_errors_with_logging(logger, body_str, body):
    # we try to parse the most things most likely to identify the client first,
    # to make tracking down the source easier
    resp_queue = body.get('response_queue')
    if not isinstance(resp_queue, str):
        logger.print(
            Level.WARN,
            'Received malformed packet {} '
            '(response_queue has type {} instead of str)',
            body_str, type(resp_queue).__name__
        )
        return True

    vers_utc = body.get('version_utc_seconds')
    if not isinstance(vers_utc, (int, float)):
        logger.print(
            Level.WARN,
            'Received malformed packet requesting a response to {} '
            '(vers_utc has type {} instead of int or float); body_str={}',
            resp_queue, type(vers_utc).__name__, body_str
        )
        return True

    simple_checks = [
        ('type', str), ('uuid', str), ('sent_at', (int, float)),
        ('style', (dict, type(None))), ('ignore_version', (bool, type(None)))
    ]
    for key, types in simple_checks:
        val = body.get(key)
        if not isinstance(val, types):
            logger.print(
                Level.WARN,
                'Received malformed packet (response_queue={}, version_utc={}) '
                '({} has type {} instead of {}}); body_str={}',
                resp_queue, vers_utc, key, type(val).__name__, types, body_str
            )
            return True

    if body.get('style'):
        bonus_allowed_style_keys = {'2xx', '3xx', '4xx', '5xx'}
        for key, val in body['style']:
            if key not in bonus_allowed_style_keys:
                try:
                    key_num = int(key)
                except ValueError:
                    key_num = -1  # we'll error out in a moment

                if key_num < 200 or key_num > 599:
                    logger.print(
                        Level.WARN,
                        'Received malformed packet (response_queue={}, version_utc={}) '
                        'style has invalid key {} ; expected one of {} or a '
                        'base-10 repr of an int a where 200 <= a <= 599; '
                        'body_str={}',
                        resp_queue, vers_utc, key, bonus_allowed_style_keys, body_str
                    )
                    return True

            if not isinstance(val, dict):
                logger.print(
                    Level.WARN,
                    'Received malformed packet (response_queue={}, version_utc={}) '
                    'style[\'{}\'] has malformed value; expected type dict but got '
                    '{}; body_str={}',
                    resp_queue, vers_utc, key, type(val).__name__, body_str
                )
                return True

            operation = val.get('operation')
            if not isinstance(operation, str):
                logger.print(
                    Level.WARN,
                    'Received malformed packet (response_queue={}, version_utc={}) '
                    'style[\'{}\'][\'operation\'] has a malformed value; expected type '
                    'str but got {}; body_str={}',
                    resp_queue, vers_utc, key, type(operation).__name__, body_str
                )
                return True

            if operation not in VALID_OPERATIONS:
                logger.print(
                    Level.WARN,
                    'Received malformed packet (response_queue={}, version_utc={}) '
                    'style[\'{}\'][\'operation\'] should be one of {} but got {}; '
                    'body_str={}',
                    resp_queue, vers_utc, key, VALID_OPERATIONS, operation, body_str
                )
                return True

            loglevel = val.get('log_level')
            if not isinstance(loglevel, (type(None), str)):
                logger.print(
                    Level.WARN,
                    'Received malformed packet (response_queue={}, version_utc={}) '
                    'style[\'{}\'][\'log_level\'] should be None or a str, but got '
                    '{}; body_str={}',
                    resp_queue, vers_utc, key, type(loglevel).__name__, body_str
                )
                return True

            if loglevel != 'NONE' and not hasattr(Level, loglevel):
                logger.print(
                    Level.WARN,
                    'Received malformed packet (response_queue={}, version_utc={}) '
                    'style[\'{}\'][\'log_level\'] does not have a recognized value. '
                    'Got {}; body_str={}',
                    resp_queue, vers_utc, key, loglevel, body_str
                )
                return True

            if operation == 'retry':
                ignore_version = val.get('ignore_version')
                if not isinstance(ignore_version, (type(None), bool)):
                    logger.print(
                        Level.WARN,
                        'Received malformed packet (response_queue={}, version_utc={}) '
                        'style[\'{}\'][\'ignore_version\'] should be a bool or None, but '
                        'got {}; body_str={}',
                        resp_queue, vers_utc, key, type(ignore_version).__name__, body_str
                    )
                    return True

    return False


def _get_handlers(logger):
    handlers = []
    for root, dirs, files in os.walk('handlers'):
        for f in files:
            if f.endswith('.py'):
                relpath = os.path.join(root, f)
                if relpath[0] == '.':
                    relpath = relpath[2:]
                modnm = relpath.replace(os.path.sep, '.').replace('/', '.')[:-3]
                mod = importlib.import_module(modnm)
                if hasattr(mod, 'register_handlers'):
                    logger.print(Level.TRACE, 'Loading handler {}', modnm)
                    mod.register_handlers(handlers)
    logger.connection.commit()
    return handlers
