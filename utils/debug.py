

def debug(verbosity: int = 0):

    def inner(function):
        def wrapper(*args, **kwargs):
            if verbosity == 1:
                log("")
            elif verbosity == 2:
                log(function.__name__)
            function(*args, **kwargs)
        return wrapper
    return inner


def log(string):
    print(f"[DEBUG] {string}")