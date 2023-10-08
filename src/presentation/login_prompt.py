import getpass

# Prompts the user for login credentials


def prompt_email():
    email: str = input("Email: ")
    if not email:
        raise ValueError("Email must be provided")
    return email


def prompt_password():
    password = getpass.getpass("Password: ")
    if not password:
        raise ValueError("Password must be provided")
    return password


def prompt_both():
    # Prompt for login credentials
    email = prompt_email()
    password = prompt_password()
    return email, password
