import time


def debug(verbose: bool = False):
    def inner(function):
        def wrapper(*args, **kwargs):
            if verbose:
                log(f"Entering {function.__name__}")

                # For calculating the time elapsed in the function
                startTime = time.perf_counter()

                # Run decorated function, grabbing the returned value
                _return = function(*args, **kwargs)

                endTime = time.perf_counter()

                log(f"Returning {_return} - {type(_return)}", function)
                log(f"Elapsed time: {round(endTime*1000 - startTime*1000, 5)}ms", function)
                log(f"Exiting {function.__name__}")

        return wrapper

    return inner


def log(string, function: callable = None):
    if not function:
        print(f"[DEBUG] {string}")
    else:
        print(f"[DEBUG] [{function.__name__} @ {function.__module__}] {string}")
