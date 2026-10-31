"""Print a bcrypt hash for PANEL_PASSWORD_HASH.

    docker run --rm -it mcpanel:local python hashpw.py
"""
import getpass

import bcrypt

password = getpass.getpass("New password: ")
if password != getpass.getpass("Again: "):
    raise SystemExit("Passwords don't match.")
if not password:
    raise SystemExit("Password is empty.")
print(bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode())
