"""The main entrypoint to the application. Connects to RabbitMQ and Postgres,
initializes the loggers, and manages the event queue.
"""
import psycopg2
from lblogging import Logger, Level
import os
import pika
import traceback
import time
import sys
import atexit
import handlers.manager


shutdown_started = False
shutdown_listeners = []


def main():
    # Turns out initializing 2 connections and trying to report errors on those
    # connections is painful. Also to make it not highly annoying to use this
    # program, we will attempt connections a few times before giving up.
    # This literally just connects to postgres, then connects to amqp,
    # registers a shutdown hook, then calls handlers.manager.register_listeners

    # The assumption is this process is being managed by something which will
    # restart it when it exists, so we don't want to just constantly stop and
    # restart if e.g. the Postgres goes down temporarily. Instead we want to
    # intelligently retry

    conn = None
    for attempt in range(5):
        if attempt > 0:
            sleep_time = 4 ** attempt
            print(f'Sleeping for {sleep_time} seconds..')
            time.sleep(sleep_time)

        print(f'Connecting to Postgres.. (attempt {attempt + 1}/5)')
        try:
            conn = psycopg2.connect('')
            break
        except psycopg2.OperationalError:
            traceback.print_exc()

    if conn is None:
        sys.exit(1)

    print('Success! Initializing logger')
    logger = Logger(os.environ['APPNAME'], 'main.py', conn)
    logger.prepare()
    logger.print(Level.INFO, 'Starting up')
    conn.commit()
    print('Logger successfully initialized')
    print('Initializing AMQP connection')

    # Until we setup the signal handlers we need to try/except to ensure
    # we report if we went down
    amqp = None
    try:
        parameters = pika.ConnectionParameters(
            os.environ['AMQP_HOST'],
            int(os.environ['AMQP_PORT']),
            os.environ['AMQP_VHOST'],
            pika.PlainCredentials(
                os.environ['AMQP_USERNAME'], os.environ['AMQP_PASSWORD']
            )
        )
        for attempt in range(5):
            if attempt > 0:
                sleep_time = 4 ** attempt
                print(f'Sleeping for {sleep_time} seconds..')
                logger.print(Level.WARN, 'Failed to connect to the AMQP server; will retry in {} seconds', sleep_time)
                logger.connection.commit()
                time.sleep(sleep_time)

            print(f'Connecting to the AMQP server.. (attempt {attempt + 1}/5)')
            try:
                amqp = pika.BlockingConnection(parameters)
            except pika.exceptions.AMQPConnectionError:
                traceback.print_exc()
                logger.exception(Level.WARN)
                logger.connection.commit()

        if amqp is None:
            logger.print(Level.ERROR, 'Failed to connect to the AMQP server (exhausted all attempts): shutting down')
            conn.commit()
            logger.close()
            conn.close()
            sys.exit(1)

        logger.print(Level.INFO, 'Successfully connected to the AMQP server!')
        print('Setting up signal handlers...')

        def receive_and_clean_shutdown(sig_num=None, frame=None):
            global shutdown_started
            global shutdown_listeners
            nonlocal logger
            nonlocal amqp
            if sig_num is not None:
                print(f'Received signal {sig_num}!')
                if shutdown_started:
                    print('Ignoring; already shutting down')
                    return
            else:
                if shutdown_started:
                    return
                print('A crash has been detected and we are attempting to shutdown cleanly')

            shutdown_started = True
            reporting_errors = True
            try:
                if sig_num is not None:
                    logger.print(Level.INFO, 'Received signal {}, clean shutdown started', sig_num)
                else:
                    logger.print(Level.ERROR, 'A crash has been detected and a clean shutdown has been initiated')
                logger.connection.commit()
            except:  # noqa: E722
                print('Failed to report the signal to the logger, continuing shutdown anyway')
                traceback.print_exc()
                reporting_errors = False

            print('Running through shutdown listeners...')
            for lst in shutdown_listeners:
                try:
                    lst()
                except:  # noqa: E722
                    print('Shutdown listener failed, continuing shutdown anyway')
                    traceback.print_exc()
                    if reporting_errors:
                        try:
                            logger.exception(Level.ERROR)
                            logger.connection.commit()
                        except:
                            print('Failed to report exception to the logger, disabling logger and continuing shutdown')
                            traceback.print_exc()
                            reporting_errors = False

            try:
                logger.close()
                logger.connection.close()
                amqp.close()
                print('Cleaning up resources finished normally, exiting status 0')
                sys.exit(0)
            except:  # noqa: E722
                print('Failed to successfully cleanup resources, exiting status 1')
                traceback.print_exc()
                sys.exit(1)

        signal.signal(signal.SIGINT, receive_and_clean_shutdown)
        signal.signal(signal.SIGTERM, receive_and_clean_shutdown)
        atexit.register(receive_and_clean_shutdown)
    except:  # noqa: E722
        print('Failed to connect to AMQP and register signals, exiting status 1')
        traceback.print_exc()
        try:
            logger.exception(Level.ERROR, 'Failed to connect to AMQP and register signal handlers')
            conn.commit()
        except:  # noqa: E722
            print('Failed to report the error, continuing shutdown anyway')
            traceback.print_exc()
        logger.close()
        conn.close()
        sys.exit(1)

    logger.print(Level.INFO, 'Initialization completed normally')
    conn.commit()
    print('Initialization completed normally. Either SIGINT or SIGTERM should '
          'be used to initiate a clean shutdown.')
    print('Logs will not be sent to STDOUT until shutdown. Monitor the '
          'postgres log table to follow progress.')
    try:
        handlers.manager.register_listeners(logger, amqp)
    except:  # noqa: E722
        print('register_listeners error')
        traceback.print_exc()
        try:
            logger.exception(Level.ERROR)
            logger.commit()
        except:  # noqa: E722
            print('Error while reporting error for register_listeners')
            traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
