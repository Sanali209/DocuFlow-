import pytest
import hmac
import hashlib
from docuflow.infrastructure.security import HMACSigner

def test_hmac_signer_generates_valid_signature():
    """TDD: Verify that HMACSigner creates a verifiable SHA256 hex digest."""
    secret = "test_secret_key"
    payload = '{"cmd": "SYNC", "node": "NODE_A"}'
    
    signer = HMACSigner(secret)
    signature = signer.sign(payload)
    
    # Manually verify
    expected = hmac.new(
        secret.encode(), 
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    assert signature == expected
    assert signer.verify(payload, signature) is True

def test_hmac_signer_rejects_tampered_payload():
    """TDD: Verify that HMACSigner detects unauthorized payload modifications."""
    secret = "test_secret_key"
    payload = '{"cmd": "SYNC", "node": "NODE_A"}'
    
    signer = HMACSigner(secret)
    signature = signer.sign(payload)
    
    # Tamper with payload
    tampered_payload = '{"cmd": "SYNC", "node": "NODE_B"}'
    
    assert signer.verify(tampered_payload, signature) is False

def test_hmac_signer_rejects_wrong_signature():
    """TDD: Verify that HMACSigner rejects invalid signatures."""
    signer = HMACSigner("secret")
    payload = "data"
    
    assert signer.verify(payload, "invalid_signature") is False

def test_hmac_signer_handles_empty_secret():
    """TDD: Verify behavior with empty or missing secrets (should still sign consistently)."""
    signer = HMACSigner("")
    payload = "data"
    signature = signer.sign(payload)
    assert signer.verify(payload, signature) is True
