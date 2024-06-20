import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from lib.logging import get_logger

local_logger = get_logger(__name__)

def decode_jwt(token: str) -> dict:
    try:
        with open('storage/oauth-public.key', "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
            
        decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience="1",)
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception as err:
        local_logger.error(f"Error decodeJWT: {err}")
        return {}


def decode_jwt_general(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False, 'verify_aud': False})
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception as err:
        local_logger.error(f"Error decode_jwt_general: {err}")
        return None

