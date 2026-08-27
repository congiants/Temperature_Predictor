import secrets
import hashlib
import hmac

#Generate tokens to be assigned to device
def generate_token():
    return secrets.token_urlsafe(32)

#Get the hash of a token
def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

#Verify a token
def verify_token(token, stored_hash):
    return hmac.compare_digest(stored_hash, hash_token(token)) 