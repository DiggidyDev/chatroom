def debug(verbose: bool = False):
    def inner(function):
        def wrapper(*args, **kwargs):
            if verbose:
                log(f"Entering {function.__name__}")
                _return = function(*args, **kwargs)
                log(f"Returning {_return} - {type(_return)}")
                log(f"Exiting {function.__name__}")

        return wrapper

    return inner


def log(string):
    print(f"[DEBUG] {string}")
