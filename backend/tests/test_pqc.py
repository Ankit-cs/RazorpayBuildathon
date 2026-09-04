import unittest
from app.core.pqc import pqc_engine

class TestPQCEngine(unittest.TestCase):
    def test_pqc_signature_generation_and_verification(self):
        mandate = {
            "order_id": "order_test_12345",
            "item_name": "KeyChron K2 Pro Mechanical Keyboard",
            "total_amount_inr": 4049.0,
            "merchant_name": "NovaTech Gear",
            "policy_bounds": {
                "max_budget_inr": 5000.0,
                "max_shipping_inr": 200.0
            }
        }
        cert = pqc_engine.sign_purchase_mandate(
            order_id=mandate["order_id"],
            item_name=mandate["item_name"],
            total_amount_inr=mandate["total_amount_inr"],
            merchant_name=mandate["merchant_name"],
            policy_bounds=mandate["policy_bounds"]
        )

        self.assertIsNotNone(cert.signature)
        self.assertTrue(cert.signature.startswith("mldsa65_sig_"))
        self.assertTrue(cert.public_key_fingerprint.startswith("pk_mldsa65_"))

        # Verify valid certificate
        valid, msg = pqc_engine.verify_mandate_signature({
            "scheme": cert.scheme,
            "signature": cert.signature,
            "sha3_512_digest": cert.sha3_512_digest,
            "mandate_payload": cert.mandate_payload
        })
        self.assertTrue(valid)
        self.assertIn("Valid", msg)

    def test_tampered_mandate_detection(self):
        cert = pqc_engine.sign_purchase_mandate(
            order_id="order_test_secure",
            item_name="Smart Dock",
            total_amount_inr=2500.0,
            merchant_name="DevDesk Supplies",
            policy_bounds={"max_budget_inr": 3000.0}
        )

        # Adversary attempts to tamper with the purchase amount
        tampered_payload = dict(cert.mandate_payload)
        tampered_payload["total_amount_inr"] = 8500.0  # Spiked price!

        valid, msg = pqc_engine.verify_mandate_signature({
            "scheme": cert.scheme,
            "signature": cert.signature,
            "sha3_512_digest": cert.sha3_512_digest,
            "mandate_payload": tampered_payload
        })
        self.assertFalse(valid)
        self.assertIn("tampered", msg.lower())

if __name__ == "__main__":
    unittest.main()
