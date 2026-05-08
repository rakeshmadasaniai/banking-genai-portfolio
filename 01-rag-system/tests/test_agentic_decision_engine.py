from __future__ import annotations

import unittest

from core.agentic_runtime import AgenticRuntime


class DecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = AgenticRuntime(retriever=None, uploaded_docs=[])

    def test_structuring_preflight(self) -> None:
        out = self.agent._decision_preflight_tool(
            user_query="We saw 12 cash deposits just under $10,000 and manager said ignore it.",
            chat_history_summary="",
        )
        self.assertIn("possible_structuring", out["triggers"])
        self.assertIn("manager_override_red_flag", out["triggers"])
        self.assertFalse(out["should_ask_clarification"])

    def test_scam_preflight(self) -> None:
        out = self.agent._decision_preflight_tool(
            user_query="My friend says this forex signal can double money in 3 months with guaranteed return.",
            chat_history_summary="",
        )
        self.assertIn("likely_investment_scam", out["triggers"])
        self.assertEqual(out["action"], "refuse_high_risk_investment")

    def test_sanctions_preflight(self) -> None:
        out = self.agent._decision_preflight_tool(
            user_query="Can we process a transfer to Iran if customer says it is humanitarian?",
            chat_history_summary="",
        )
        self.assertIn("sanctions_screening", out["triggers"])
        self.assertEqual(out["action"], "sanctions_review")

    def test_life_event_terminal_detected(self) -> None:
        out = self.agent._risk_profile_tool(
            user_query="I was diagnosed terminally ill and have 18 months to live.",
            chat_history_summary="",
        )
        self.assertEqual(out.get("life_event"), "medical_terminal")
        self.assertTrue(out.get("enough_information"))

    def test_short_horizon_forces_conservative(self) -> None:
        out = self.agent._risk_profile_tool(
            user_query="I need this money in 6 months.",
            chat_history_summary="",
        )
        self.assertEqual(out.get("risk_profile"), "conservative")
        self.assertEqual(out.get("signals", {}).get("liquidity_need"), "high")

    def test_required_return_tool(self) -> None:
        out = self.agent._required_return_tool(principal=200000, target=1000000, years=2)
        self.assertEqual(out.get("status"), "success")
        self.assertGreater(float(out.get("required_annual_return_pct", 0)), 100.0)


if __name__ == "__main__":
    unittest.main()
