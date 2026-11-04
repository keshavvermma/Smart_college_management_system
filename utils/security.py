"""
utils/security.py - password hashing (pure Python, no Streamlit needed).

We use PBKDF2-HMAC-SHA256 from Python's standard library:
  * a random 16-byte salt per password (same password -> different hash)
  * 260,000 iterations (makes brute-force guessing slow)
Stored format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
Plain-text passwords are never stored.
"""
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000


def hash_password(password: str, iterations: int = ITERATIONS, salt: bytes | None = None) -> str:
    """Return a salted hash string for the given password."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against a stored hash (constant-time comparison)."""
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# A valid hash of a random password, used so that a login attempt for an unknown
# username takes the same time as one for a real username.
DUMMY_HASH = hash_password(secrets.token_urlsafe(12), iterations=ITERATIONS)
