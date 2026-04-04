import hmac
import hashlib

class HMACSigner:
    """Cryptographic utility for signing and verifying P2P message integrity.
    
    This class implements the HMAC-SHA256 protocol to ensure that files
    broadcast over the shared network (Samba/CIFS) have not been tampered
    with by unauthorized parties.
    
    Examples:
        >>> signer = HMACSigner("my_secret_key")
        >>> signature = signer.sign('{"data": "ping"}')
        >>> signer.verify('{"data": "ping"}', signature)
        True
        >>> signer.verify('{"data": "pong"}', signature)
        False
    """

    def __init__(self, secret: str):
        """Initialize the signer with a shared secret key.
        
        Args:
            secret: The string key used for HMAC calculation across all nodes.
        """
        self._secret_bytes = secret.encode("utf-8")

    def sign(self, payload: str) -> str:
        """Generate a digital signature for the given payload.
        
        Args:
            payload: The message content to be signed.
            
        Returns:
            A lowercase hexadecimal HMAC-SHA256 digest.
        """
        return hmac.new(
            self._secret_bytes,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def verify(self, payload: str, signature: str) -> bool:
        """Verify that the payload matches the provided signature.
        
        Args:
            payload: The message content to verify.
            signature: The hexadecimal digest to compare against.
            
        Returns:
            True if the signature is valid for the payload, False otherwise.
        """
        expected = self.sign(payload)
        # Use compare_digest to prevent timing attacks
        return hmac.compare_digest(expected, signature)
