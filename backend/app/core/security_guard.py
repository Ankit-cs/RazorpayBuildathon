import re
import time
from typing import Dict, Any, Tuple, Optional, Set

class SecurityGuard:
    """
    Security Guard Layer for VERITY Agentic Commerce.
    Enforces:
    1. Prompt-Injection Resistance (Adversarial override defense)
    2. Replay Protection & Transaction Idempotency
    3. Tool Execution Permission Boundaries
    4. Sensitive Financial Data Masking
    """
    def __init__(self):
        # In-memory idempotency cache: {idempotency_key: {"created_at": float, "response": Any}}
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = 3600  # 1 hour

        # Allowed tool boundaries for Autonomous Buyer Agent
        self._authorized_tools: Set[str] = {
            "discover_federated_catalog",
            "compare_offers",
            "get_product",
            "check_inventory",
            "calculate_total",
            "validate_policy",
            "negotiate_offer",
            "create_order",
            "get_order_status",
            "evaluate_policy_invariants",
            "sign_pqc_mandate",
            "create_razorpay_checkout_order"
        }

        # Known prompt injection & jailbreak patterns targeting financial agents
        self._injection_patterns = [
            r"(?i)ignore\s+(all\s+)?(previous\s+)?instructions",
            r"(?i)override\s+(policy|budget|limits|invariants)",
            r"(?i)system\s+prompt\s+override",
            r"(?i)you\s+are\s+now\s+(an\s+unbounded|DAN|jailbreak)",
            r"(?i)bypass\s+(security|checks|razorpay|gate)",
            r"(?i)transfer\s+all\s+(funds|money)\s+to",
            r"(?i)spend\s+unlimited",
            r"(?i)set\s+budget\s+to\s+(infinity|\d{8,})"
        ]

    def sanitize_and_check_prompt(self, prompt: str) -> Tuple[bool, str, Optional[str]]:
        """
        Scans prompt for prompt-injection attacks.
        Returns: (is_safe, sanitized_prompt, alert_reason)
        """
        if not prompt:
            return True, "", None

        for pattern in self._injection_patterns:
            if re.search(pattern, prompt):
                return False, prompt, f"Prompt injection threat detected matching pattern: {pattern}"

        # Clean control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', prompt).strip()
        return True, sanitized, None

    def check_idempotency(self, idempotency_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks if an operation with this idempotency key was already executed.
        Returns: (is_duplicate, cached_response_if_any)
        """
        if not idempotency_key:
            return False, None

        self._purge_expired_cache()
        if idempotency_key in self._idempotency_cache:
            entry = self._idempotency_cache[idempotency_key]
            return True, entry.get("response")

        return False, None

    def record_idempotency(self, idempotency_key: str, response: Dict[str, Any]):
        """Records an execution response under an idempotency key."""
        if idempotency_key:
            self._idempotency_cache[idempotency_key] = {
                "created_at": time.time(),
                "response": response
            }

    def validate_tool_permission(self, tool_name: str) -> bool:
        """Enforces agent tool permission boundaries."""
        return tool_name in self._authorized_tools

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Masks sensitive financial identifiers before logging or telemetry."""
        masked = {}
        for k, v in data.items():
            if isinstance(v, dict):
                masked[k] = self.mask_sensitive_data(v)
            elif isinstance(v, str):
                if any(sec in k.lower() for sec in ["secret", "token", "password", "key_secret"]):
                    masked[k] = v[:4] + "..." + v[-4:] if len(v) > 8 else "********"
                elif any(card in k.lower() for card in ["card_number", "account_number"]):
                    masked[k] = "•••• •••• •••• " + v[-4:] if len(v) >= 4 else "••••"
                else:
                    masked[k] = v
            else:
                masked[k] = v
        return masked

    def _purge_expired_cache(self):
        now = time.time()
        expired_keys = [k for k, v in self._idempotency_cache.items() if (now - v["created_at"]) > self._cache_ttl_seconds]
        for k in expired_keys:
            del self._idempotency_cache[k]

security_guard = SecurityGuard()
