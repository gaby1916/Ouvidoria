import hashlib
import hmac
import base64
import json
import os

JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-dev-secret')

def make_mini_token(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=')
    payload_b = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).rstrip(b'=')
    signing_input = header_b + b'.' + payload_b
    sig = hmac.new(JWT_SECRET.encode(), signing_input, digestmod=hashlib.sha256).digest()
    sig_b = base64.urlsafe_b64encode(sig).rstrip(b'=')
    return signing_input.decode() + '.' + sig_b.decode()

def parse_mini_token(token: str) -> dict | None:
    try:
        header_b, payload_b, sig_b = token.split('.')
        signing_input = (header_b + '.' + payload_b).encode()
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(JWT_SECRET.encode(), signing_input, digestmod=hashlib.sha256).digest()
        ).rstrip(b'=').decode()
        if hmac.compare_digest(expected_sig, sig_b):
            payload_json = base64.urlsafe_b64decode(payload_b + '=' * (-len(payload_b) % 4))
            return json.loads(payload_json)
    except Exception:
        return None
    return None
