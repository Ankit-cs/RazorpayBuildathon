import json
from typing import Any, Dict, List

class CanonicalError(Exception):
    def __init__(self, path: str, reason: str):
        super().__init__(f"canonical JSON refused at {path or '<root>'}: {reason}")

def canonical_json(value: Any) -> str:
    return _serialize(value, "")

def _serialize(value: Any, path: str) -> str:
    if value is None:
        return "null"
    
    if isinstance(value, bool):
        return "true" if value else "false"
    
    if isinstance(value, (int, float)):
        return _serialize_number(value, path)
    
    if isinstance(value, str):
        return json.dumps(value)
    
    if isinstance(value, list):
        return _serialize_array(value, path)
        
    if isinstance(value, dict):
        return _serialize_object(value, path)
        
    raise CanonicalError(path, f"{type(value).__name__} is not representable")

def _serialize_number(n: float, path: str) -> str:
    # Python int is unlimited precision, and float is double.
    # Money must be safe integer.
    import math
    if not math.isfinite(n):
        raise CanonicalError(path, "non-finite number")
    if not isinstance(n, int):
        if not n.is_integer():
            raise CanonicalError(path, "non-integer number — money must be integer paise")
        n = int(n)
    
    # Safe integer check (JS Number.MAX_SAFE_INTEGER is 9007199254740991)
    if abs(n) > 9007199254740991:
        raise CanonicalError(path, "number exceeds safe integer bounds")
        
    return str(n)

def _serialize_object(obj: Dict[str, Any], path: str) -> str:
    keys = sorted([k for k in obj.keys() if obj[k] is not None])
    parts = []
    for k in keys:
        child_path = f"{path}.{k}" if path else k
        parts.append(f"{json.dumps(k)}:{_serialize(obj[k], child_path)}")
    return "{" + ",".join(parts) + "}"

def _serialize_array(arr: List[Any], path: str) -> str:
    parts = [_serialize(v, f"{path}[{i}]") for i, v in enumerate(arr)]
    return "[" + ",".join(parts) + "]"

def stable_stringify(value: Any) -> str:
    return _lenient(value)

def _lenient(value: Any) -> str:
    if value is None:
        return "null"
    
    if isinstance(value, bool):
        return "true" if value else "false"
        
    if isinstance(value, (int, float)):
        import math
        if math.isfinite(value):
            # To match JS String(number):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        return "null"
        
    if isinstance(value, str):
        return json.dumps(value)
        
    if isinstance(value, list):
        parts = [_lenient(v) for v in value]
        return "[" + ",".join(parts) + "]"
        
    if isinstance(value, dict):
        keys = sorted([k for k in value.keys() if value.get(k) is not None])
        parts = [f"{json.dumps(k)}:{_lenient(value[k])}" for k in keys]
        return "{" + ",".join(parts) + "}"
        
    return "null"
