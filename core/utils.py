import time
from functools import wraps
import logging
import sys

def retry(environment="test",
          number_of_retries=5, 
          initial_timeout=60, 
          exit_on_error=False, 
          step="", 
          non_retrievable_exception=(), 
          verbose=True):
    logger = logging.getLogger()

    def inner_function(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            if environment == 'test':  # do not execute retry decorator for local tests and test environment
                return function(*args, **kwargs)

            result = None
            for retry_count in range(1, number_of_retries + 1):
                try:
                    if verbose:  # some methods may spam logs
                        logger.info(f'Executing function {wrapper.__name__}')
                    result = function(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f'Execution attemp failed {retry_count} of {number_of_retries}! Error type: {type(e).__name__}\nError: {e}')
                    is_non_retrievable_exception = non_retrievable_exception and isinstance(
                        e, non_retrievable_exception)
                    if retry_count >= (number_of_retries) or is_non_retrievable_exception:
                        logger.error(f'Execution failed with non_retrievable_exception') if is_non_retrievable_exception else logger.error(
                            f'Execution failed after {number_of_retries} attempts')

                        if exit_on_error:
                            sys.exit(1)
                        else:
                            raise Exception()
                    else:
                        timeout = initial_timeout * retry_count
                        logger.info(f"Retrying in {timeout} seconds...") 
                        time.sleep(timeout)
                        logger.info(f"Attempt #{retry_count+1} ...")
                else:
                    break
            return result
        return wrapper
    return inner_function
