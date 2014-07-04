# recipe courtesy of Guido
# https://mail.python.org/pipermail/python-dev/2008-January/076194.html

def add_method(cls, func):
    """Adds a new method to a class.
    Attempting to overwrite an existing method raises an exception."""
    if getattr(cls, func.__name__, None):
        raise Exception('Method %s already exists.' % (func.__name__))
    setattr(cls, func.__name__, func)

def new_method(cls):
    """Decorator: adds a new method to a class."""
    def decorator(func):
        add_method(cls, func)
        return func
    return decorator
