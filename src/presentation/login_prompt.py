import getpass
import logging

logger = logging.getLogger(__name__)

# Prompts the user for login credentials


class InputException(Exception):
    pass


def prompt_email():
    logger.info("Prompting for email")

    try:
        email: str = input("Email: ")
    except Exception as e:
        raise InputException(
            f"Exception occured while trying to get email input from user: {e}"
        ) from e
    if not email:
        raise ValueError("Email must be provided")
    return email


def prompt_password():
    logger.info("Prompting for password")

    try:
        password = getpass.getpass("Password: ")
    except Exception as e:
        raise InputException(
            f"Exception occured while trying to get password input from user: {e}"
        ) from e

    if not password:
        raise ValueError("Password must be provided")
    return password


def prompt_both():
    # Prompt for login credentials
    email = prompt_email()
    password = prompt_password()
    return email, password
