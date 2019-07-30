"""
custom exceptions for internal use, so the various components dont exit(1) the process
"""
# pylint: disable=C0103
# pylint: disable=W0107


class PasswordFileNotFound(Exception):
    """
    Gets raised if the password (pw.txt) is not found in the project root directory
    """
    pass


class LoginError(Exception):
    """gets raised if something with the login fails. Probably due wrong credentials"""
    pass


class OrdersNotFound(Exception):
    """gets raised if 'orders.json' not found in th project root directory"""
    pass
