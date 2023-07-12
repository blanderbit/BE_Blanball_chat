def clear_global_vars(names):
    """Decorator that clears global variables after the function returns.

    Args:
        names: A list of global variable names to clear.

    Returns:
        A decorator that can be used to wrap a function.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Get the global variables from the context where the function is located.
                global_vars = [
                    name for name in names if name in globals()
                ]

                print(global_vars)

                # Clear the global variables.
                for name in global_vars:
                    del globals()[name]

                # Execute the function.
                result = func(*args, **kwargs)

            finally:
                # Restore the global variables.
                for name in global_vars:
                    globals()[name] = getattr(func, name)

            return result

        return wrapper

    return decorator
