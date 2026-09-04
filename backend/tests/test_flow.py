import unittest
from app.core.policy_engine import SpendingPolicy, policy_engine
from app.services.catalog_service import catalog_service
from app.services.razorpay_service import razorpay_service
from app.agents.buyer_agent import buyer_agent, BuyerProcurementRequest
from app.core.audit_ledger import audit_ledger
from app.api.routes_agent import chat_with_agent, get_live_metrics

class TestVerityFlow(unittest.TestCase):
    def setUp(self):
        catalog_service.reset_catalog()
        audit_ledger.clear()

    def test_policy_engine_invariants_pass(self):
        policy = SpendingPolicy(max_budget_inr=5000.0, max_shipping_inr=200.0)
        res = policy_engine.evaluate(
            policy=policy,
            item_title="KeyChron K2 Pro Mechanical Keyboard",
            category="Electronics",
            base_price_inr=3899.0,
            shipping_inr=150.0,
            warranty_months=12
        )
        self.assertTrue(res.passed)
        self.assertEqual(len(res.violations), 0)

    def test_policy_engine_invariants_fail_on_budget_breach(self):
        policy = SpendingPolicy(max_budget_inr=3000.0)
        res = policy_engine.evaluate(
            policy=policy,
            item_title="AuraSound Flow ANC Headphones",
            category="Electronics",
            base_price_inr=4499.0,
            shipping_inr=0.0,
            warranty_months=12
        )
        self.assertFalse(res.passed)
        self.assertTrue(any("Budget Invariant Breach" in v for v in res.violations))

    def test_razorpay_order_creation_and_signature_check(self):
        order = razorpay_service.create_order(amount_inr=3999.0)
        self.assertIn("id", order)
        self.assertTrue(order["id"].startswith("order_"))
        self.assertEqual(order["amount"], 399900)

        # Signature verification check
        valid = razorpay_service.verify_payment_signature(
            razorpay_order_id=order["id"],
            razorpay_payment_id="pay_test_12345",
            razorpay_signature="sig_mock_valid_123"
        )
        self.assertTrue(valid)

    def test_autonomous_procurement_success_flow(self):
        req = BuyerProcurementRequest(
            user_prompt="Buy a wireless mechanical keyboard for programming",
            spending_policy=SpendingPolicy(max_budget_inr=4500.0)
        )
        response = buyer_agent.execute_autonomous_purchase(req)
        self.assertTrue(response.success)
        self.assertEqual(response.status, "ORDER_COMPLETED")
        self.assertIsNotNone(response.final_order)
        self.assertIn("order_", response.final_order["order_id"])

    def test_graceful_failure_handling_on_price_spike(self):
        req = BuyerProcurementRequest(
            user_prompt="Buy a mechanical keyboard with brown switches",
            spending_policy=SpendingPolicy(max_budget_inr=4500.0),
            force_failure_simulation="PRICE_SPIKE"
        )
        response = buyer_agent.execute_autonomous_purchase(req)
        self.assertFalse(response.success)
        self.assertEqual(response.status, "RECOVERED_WITH_COUNTER_OFFER")
        self.assertIsNotNone(response.recovery_plan)
        self.assertIn("alternative_product", response.recovery_plan)

    def test_multi_merchant_comparison_finds_best_deal(self):
        comparison = catalog_service.compare_across_merchants("keyboard", max_price=5000.0)
        self.assertGreater(comparison["merchants_compared"], 0)
        self.assertIsNotNone(comparison["best_deal"])
        self.assertIn("total_cost_inr", comparison["best_deal"])

    def test_chat_intent_detection(self):
        chat_resp = chat_with_agent({"message": "Buy a mechanical keyboard under 4500", "budget": 4500})
        self.assertEqual(chat_resp["role"], "agent")
        self.assertIn("data", chat_resp)
        self.assertTrue(len(chat_resp["content"]) > 0)

    def test_metrics_aggregation(self):
        # Run a purchase to generate metrics
        req = BuyerProcurementRequest(
            user_prompt="Get headphones",
            spending_policy=SpendingPolicy(max_budget_inr=6000.0)
        )
        buyer_agent.execute_autonomous_purchase(req)
        metrics = get_live_metrics()
        self.assertGreaterEqual(metrics["total_purchases_attempted"], 1)

    def test_vulcan_agentic_protocol_vap_attestation(self):
        from app.api.routes_agent import test_vap_attestation
        res = test_vap_attestation({
            "agent_id": "Agent_007",
            "user_identity": "cfo_test",
            "amount_inr": 3500.0,
            "budget_limit_inr": 4000.0
        })
        self.assertTrue(res["bot_fraud_bypass_approved"])
        self.assertEqual(res["vulcan_agent_trust_tier"], "TIER_1_VERIFIED_AUTONOMOUS_AGENT")
        self.assertTrue(res["popi_token"].startswith("popi_jwt_"))

    def test_split_settlement_route_planning(self):
        from app.api.routes_agent import test_split_settlement
        res = test_split_settlement({
            "primary_item": {"product_name": "Keyboard", "merchant_name": "NovaTech Gear", "price_inr": 3899.0, "shipping_cost_inr": 150.0},
            "accessory_item": {"name": "Cable", "merchant_name": "DevDesk Supply Co.", "bundle_price_inr": 499.0}
        })
        self.assertEqual(res["transfers_count"], 2)
        self.assertEqual(res["total_settlement_inr"], 4548.0)
        self.assertIn("Atomic", res["settlement_guarantee"])

    def test_surge_interception_and_counter_offer(self):
        from app.api.routes_agent import test_surge_interception
        res = test_surge_interception({
            "base_price_inr": 3899.0,
            "surge_price_inr": 5200.0,
            "budget_limit_inr": 4500.0,
            "item_title": "KeyChron K2 Pro Mechanical Keyboard"
        })
        self.assertTrue(res["policy_invariant_triggered"])
        self.assertEqual(res["verdict"], "REJECTED_BY_DETERMINISTIC_GATE")
        self.assertIsNotNone(res["counter_offer"])

    def test_quantum_merkle_proof(self):
        from app.api.routes_agent import get_quantum_merkle_proof
        proof = get_quantum_merkle_proof()
        self.assertIn("ML-DSA-65", proof["nist_standard"])
        self.assertTrue(proof["audit_tamper_evident"])

    def test_mcp_tool_execution(self):
        from app.api.routes_agent import test_mcp_tool_execution
        res = test_mcp_tool_execution({
            "tool_name": "discover_federated_catalog",
            "arguments": {"query": "keyboard", "max_budget_inr": 5000}
        })
        self.assertEqual(res["json_rpc_version"], "2.0")
        self.assertEqual(res["tool_called"], "discover_federated_catalog")
        self.assertEqual(res["response"]["status"], "success")

if __name__ == "__main__":
    unittest.main()

