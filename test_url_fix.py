from sqlalchemy.engine import make_url
from sqlalchemy import create_engine
import urllib.parse
import sys

# Simulated bad URL: Password "My@123Hamba"
# URL: postgresql://user:My@123Hamba@db.host.com:5432/db
bad_url = "postgresql://user:My@123Hamba@db.host.com:5432/db"

print(f"Testing URL: {bad_url}")

try:
    u = make_url(bad_url)
    print(f"Parsed Host: {u.host}")
    print(f"Parsed Password: {u.password}")
except Exception as e:
    print(f"Make URL failed: {e}")

# Proposed fix logic
try:
    if bad_url.count("@") > 1:
        print("Detected multiple '@'. Attempting fix...")
        prefix = "postgresql://"
        if bad_url.startswith(prefix):
            rest = bad_url[len(prefix):]
            # Split from the right to find the host separator
            if "@" in rest:
                creds, host_part = rest.rsplit("@", 1)
                if ":" in creds:
                    user, password = creds.split(":", 1)
                    # Encode password
                    fixed_password = urllib.parse.quote_plus(password)
                    fixed_url = f"{prefix}{user}:{fixed_password}@{host_part}"
                    print(f"Fixed URL: {fixed_url}")
                    
                    u2 = make_url(fixed_url)
                    print(f"Fixed Host: {u2.host}")
                    print(f"Fixed Password: {u2.password}")
except Exception as e:
    print(f"Fix failed: {e}")
