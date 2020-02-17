"""This module is responsible for detecting handlers within this package and
forwarding the appropriate jobs to them.
"""
import main


def register_listeners(logger, amqp):
    logger = logger.with_iden('handlers/manager.py')

    logger.print(Level.TRACE, 'Finding listeners...')
    # TODO find listeners
    logger.connection.commit()
    logger.print(Level.TRACE, 'Listeners found, consuming events..')
    logger.connection.commit()
    # TODO actually do stuff
