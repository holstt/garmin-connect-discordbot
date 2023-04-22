# Prompts the user for login credentials and returns them as a tuple.
import getpass


# Prompts the user for login credentials
class LoginPrompt:
    def show(self):
        # Prompt for login credentials
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        # Throw if either is empty
        if not email or not password:
            raise ValueError("Email and password must be provided")

        return email, password
