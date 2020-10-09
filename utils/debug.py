def debug(verbosity: int = 0):

    def inner(function):
        def wrapper(*args, **kwargs):
            if verbosity == 1:
                print("Hello!14w")
                print(function.__name__)
            elif verbosity == 1:
                print("ah")
            function(*args, **kwargs)
        return wrapper
    return inner
