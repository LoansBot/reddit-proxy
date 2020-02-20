"""This module is responsible for detecting handlers within this package and
forwarding the appropriate jobs to them.
"""
import main
import os
import importlib
import json

VALID_OPERATIONS = {'copy', 'success', 'failure', 'retry'}
"""The list of valid operations within the style part of a packet"""


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
    queue = os.environ['AMQP_QUEUE']
    response_queues = {}

    channel = amqp.channel()
    for method_frame, properties, body_bytes in channel.consume(queue):
        body_str = body.decode('utf-8')
        try:
            body = json.loads(body_s):
        except json.JSONDecodeError as exc:
            logger.exception(Level.WARN, 'Received non-json packet! Error info: doc={}, msg={}, pos={}, lineno={}, colno={}', exc.doc, exc.msg, exc.pos, exc.lineno, exc.colno)
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue

        if _detect_structure_errors_with_logging(logger, body_str, body):
            channel.basic_nack(method_frame.delivery_tag, requeue=False)
            continue

        # TODO version checking etc, see readme
        # TODO queue the response using response_queues
        channel.basic_ack(method_frame.delivery_tag)


def _detect_structure_errors_with_logging(logger, body_str, body):
    # we try to parse the most things most likely to identify the client first,
    # to make tracking down the source easier
    resp_queue = body.get('response_queue')
    if not isinstance(resp_queue, str):
        logger.print(Level.WARN, 'Received malformed packet {} (response_queue has type {} instead of str)',
                     body_str, type(resp_queue).__name__)
        return True

    vers_utc = body.get('version_utc_seconds')
    if not isinstance(body.get(vers_utc), (int, float)):
        logger.print(
            Level.WARN,
            'Received malformed packet requesting a response to {} '
            '(vers_utc has type {} instead of int or float); body_str={}',
            resp_queue, type(vers_utc).__name__, body_str
        )
        return True

    for key, types in [('type', str), ('uuid', str), ('sent_at', (int, float)), ('style', (dict, type(None))), ('ignore_version', (bool, type(None)))]:
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
                    key_num = -1 # we'll error out in a moment

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
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        for f in files:
            if f.endswith('.py'):
                modnm = os.path.join(root, f).replace(os.path.sep, '.').replace('/', '.')[:-3]
                mod = importlib.import_module()
                if hasattr(mod, 'register_handlers'):
                    logger.print(Level.TRACE, 'Loading handler {}', modnm)
                    mod.register_handlers(handlers)
    return handlers