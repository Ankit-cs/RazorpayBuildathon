import os
import json
import base64
import hashlib
from typing import Tuple, Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from pydantic import BaseModel

class KeyPair(BaseModel):
    privateKeyPem: str
    publicKeyPem: str
    fingerprint: str
    ephemeral: bool

_cached: Optional[KeyPair] = None

def fingerprint_of(public_key_pem: str) -> str:
    public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return hashlib.sha256(der).hexdigest()[:16]

def generate_key_pair() -> Tuple[str, str]:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem

def load_keys(state_dir: Optional[str]) -> KeyPair:
    global _cached
    if _cached is not None:
        return _cached
        
    if state_dir is None:
        priv, pub = generate_key_pair()
        _cached = KeyPair(privateKeyPem=priv, publicKeyPem=pub, fingerprint=fingerprint_of(pub), ephemeral=True)
        return _cached
        
    dir_path = os.path.join(state_dir, "keys")
    file_path = os.path.join(dir_path, "merchant.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            
            # verify it loads
            serialization.load_pem_private_key(raw["privateKeyPem"].encode('utf-8'), password=None)
            _cached = KeyPair(
                privateKeyPem=raw["privateKeyPem"],
                publicKeyPem=raw["publicKeyPem"],
                fingerprint=fingerprint_of(raw["publicKeyPem"]),
                ephemeral=False
            )
            return _cached
            
        os.makedirs(dir_path, exist_ok=True)
        priv, pub = generate_key_pair()
        
        import time
        record = {
            "createdAtMs": int(time.time() * 1000),
            "privateKeyPem": priv,
            "publicKeyPem": pub,
            "note": "TEST-ONLY demo key. Rotate for any real deployment."
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
            
        _cached = KeyPair(privateKeyPem=priv, publicKeyPem=pub, fingerprint=fingerprint_of(pub), ephemeral=False)
        return _cached
        
    except Exception:
        priv, pub = generate_key_pair()
        _cached = KeyPair(privateKeyPem=priv, publicKeyPem=pub, fingerprint=fingerprint_of(pub), ephemeral=True)
        return _cached

def reset_key_cache() -> None:
    global _cached
    _cached = None
