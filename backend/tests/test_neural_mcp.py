import unittest
from app.core.neural_engine import neural_core
from app.api.routes_mcp import list_mcp_tools, execute_mcp_tool_call

class TestNeuralAndMCPEngine(unittest.TestCase):
    def test_dense_vector_embedding_cosine_similarity(self):
        query = "mechanical keyboard"
        item_a = "KeyChron Mechanical Keyboard"
        item_b = "Wireless Noise Cancelling Earbuds"

        vec_q = neural_core.dense_vector.generate_embedding(query)
        vec_a = neural_core.dense_vector.generate_embedding(item_a)
        vec_b = neural_core.dense_vector.generate_embedding(item_b)

        sim_a = neural_core.dense_vector.cosine_similarity(vec_q, vec_a)
        sim_b = neural_core.dense_vector.cosine_similarity(vec_q, vec_b)

        self.assertEqual(len(vec_q), 64)
        self.assertGreater(sim_a, 0.5)

    def test_reinforcement_learning_bandit_arm_selection(self):
        decision = neural_core.bandit_rl.select_optimal_arm("BALANCED", budget_headroom_inr=1500.0)
        self.assertIn("selected_strategy", decision)
        self.assertIn("expected_conversion_probability", decision)
        self.assertGreater(decision["expected_conversion_probability"], 0.5)

    def test_neural_fraud_autoencoder_reconstruction(self):
        mse_loss, is_anomaly = neural_core.autoencoder.compute_reconstruction_loss(
            amount_inr=4000.0,
            velocity_per_min=1,
            geo_trust=0.98
        )
        self.assertIsInstance(mse_loss, float)
        self.assertFalse(is_anomaly)

    def test_mcp_tools_manifest_and_execution(self):
        manifest = list_mcp_tools()
        self.assertIn("tools", manifest)
        self.assertGreaterEqual(len(manifest["tools"]), 4)

        # Test execute discover_federated_catalog tool
        res = execute_mcp_tool_call({
            "tool_name": "discover_federated_catalog",
            "arguments": {"query": "keyboard", "max_budget_inr": 5000}
        })
        self.assertEqual(res["status"], "success")

if __name__ == "__main__":
    unittest.main()
