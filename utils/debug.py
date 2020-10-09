

def debug(verbosity: int = 0):

    def inner(function):
        def wrapper(*args, **kwargs):
            if verbosity == 2:
                log(f"Entering {function.__name__}")
                _return = function(*args, **kwargs)
                log(f"Returning {_return} - {type(_return)}")
                log(f"Exiting {function.__name__}")
        return wrapper
    return inner


def log(string):
    print(f"[DEBUG] {string}")
