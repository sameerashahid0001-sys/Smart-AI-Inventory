"""
Ollama AI Integration Service
Handles communication with local Ollama API (http://localhost:11434).
Provides:
-Model discovery and health checks
-Executive Supply Chain Report Generation
-Context-aware Interactive AI Chat Copilot (explains predictions, math formulas, risks)
-Graceful algorithmic fallback when Ollama is offline
"""
import json
import requests
from typing import List, Dict, Any, Optional
class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        
        #Verifies if Ollama is running and lists installed models.
        
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "connected": True,
                    "models": models,
                    "default_model": models[0] if models else "llama3",
                    "message": "Ollama server is active."
                }
            return {
                "connected": False,
                "models": [],
                "default_model": "llama3",
                "message": f"Ollama returned HTTP status {res.status_code}"
            }
        except Exception as e:
            return {
                "connected": False,
                "models": [],
                "default_model": "llama3",
                "message": f"Ollama is not running locally on {self.base_url} ({str(e)}). Run 'ollama serve' or start Ollama desktop."
            }

    def generate_executive_report(
        self,
        summary_stats: Dict[str, Any],
        items: List[Dict[str, Any]],
        model: str = "llama3"
    ) -> Dict[str, Any]:
        #Generates an in-depth AI Executive Inventory Report.
    
        # Filter high-priority subsets for LLM context
        critical_items = [it for it in items if it.get("risk_level") in ["CRITICAL", "HIGH"]]
        reorder_items = [it for it in items if it.get("needs_reorder")]
        overstock_items = [it for it in items if it.get("risk_level") == "OVERSTOCK"]

        # Prepare compact payload for the prompt
        critical_summary = [
            f"- {it['sku']} ({it['name']}): Stock={it['current_stock']}, Pred.Demand={it['next_period_forecast']}, ROP={it['reorder_point']}, OrderQty={it['recommended_order_qty']}, Cost=${it['reorder_investment']}"
            for it in critical_items[:8]
        ]
        overstock_summary = [
            f"- {it['sku']} ({it['name']}): Stock={it['current_stock']}, Pred.Demand={it['next_period_forecast']}, DOI={it['days_of_inventory']} days, TiedUpCapital=${it['stock_value']}"
            for it in overstock_items[:5]
        ]

        prompt = f"""You are a Chief Supply Chain & Inventory Analytics AI Officer.
Analyze the following inventory prediction dataset and generate a comprehensive, executive-ready inventory report in clean Markdown format.
SUMMARY METRICS:
- Total SKUs Analyzed: {summary_stats.get('total_items')}
- Items Needing Reorder: {summary_stats.get('reorder_needed_count')}
- Critical Stockout Risks: {summary_stats.get('critical_risk_count')}
- Overstocked Items: {summary_stats.get('overstock_count')}
- Total Current Stock Value: ${summary_stats.get('total_stock_value', 0):,.2f}
- Required Reorder Capital: ${summary_stats.get('total_reorder_investment', 0):,.2f}
- Forecasting Method Used: {summary_stats.get('method_used', 'Weighted Mean')}
- Target Service Level: {summary_stats.get('service_level_pct', 95)}%
CRITICAL STOCKOUT RISKS (Urgent Action Required):
{chr(10).join(critical_summary) if critical_summary else "No critical stockouts detected."}
OVERSTOCKED ITEMS (Excess Working Capital):
{chr(10).join(overstock_summary) if overstock_summary else "No severe overstocks detected."}
INSTRUCTIONS FOR THE REPORT:
1. Executive Summary: High-level health score of inventory and key financial risks.
2. Immediate Action Plan (Next 24-48 Hours): Specific Purchase Orders (POs) to execute with exact SKU numbers, quantities, and cost justification.
3. Overstock & Cash Flow Optimization: Recommendations to liquidate or reallocate capital from overstocked lines.
4. Mathematical Methodology & Accuracy: Explain how the {summary_stats.get('method_used', 'Weighted Mean')} method and Reorder Point (ROP = d*L + SS) protect the business against supply delays.
5. Strategic Supplier & Lead Time Recommendations: Advice on supplier renegotiation, safety stock adjustments, and buffer management.
Tone: Crisp, authoritative, data-driven, and actionable. Use bullet points, bold text, and markdown tables where appropriate.
"""

        # Attempt Ollama call
        try:
            res = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1500
                    }
                },
                timeout=60
            )
            if res.status_code == 200:
                response_text = res.json().get("response", "").strip()
                return {
                    "success": True,
                    "report_markdown": response_text,
                    "source": f"Ollama ({model})"
                }
        except Exception as e:
            # Fall through to analytical fallback
            pass

        # Fallback report generator if Ollama is not yet started
        fallback_report = self._generate_rule_based_report(summary_stats, items, critical_items, overstock_items)
        return {
            "success": True,
            "report_markdown": fallback_report,
            "source": "Algorithmic Supply Chain Engine (Start Ollama for full LLM synthesis)"
        }

    def chat_with_copilot(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        summary_stats: Dict[str, Any],
        items: List[Dict[str, Any]],
        model: str = "llama3"
    ) -> Dict[str, Any]:
        """
        Interactive Q&A Copilot that answers user queries about predictions, math, or specific SKUs.
        """
        # Build contextual data string for items
        items_context = []
        for it in items[:25]:
            items_context.append(
                f"SKU: {it['sku']} | Name: {it['name']} | Category: {it['category']} | Stock: {it['current_stock']} | "
                f"Pred.Demand: {it.get('next_period_forecast', 0)} | ROP: {it.get('reorder_point', 0)} | "
                f"SafetyStock: {it.get('safety_stock', 0)} | ReorderQty: {it.get('recommended_order_qty', 0)} | "
                f"Status: {it.get('status', 'Healthy')} | UnitCost: ${it.get('unit_cost', 0)} | LeadTime: {it.get('lead_time_days', 14)}d"
            )

        system_prompt = f"""You are the SmartInventory AI Assistant and Supply Chain Expert.
You have complete visibility into the current inventory forecast dataset and mathematical forecasting models.
ACTIVE FORECAST CONTEXT:
- Total Items: {summary_stats.get('total_items', len(items))}
- Method: {summary_stats.get('method_used', 'Weighted Mean')}
- Required Reorder Capital: ${summary_stats.get('total_reorder_investment', 0):,.2f}
- Reorder Items Count: {summary_stats.get('reorder_needed_count', 0)}
- Critical Risks: {summary_stats.get('critical_risk_count', 0)}
ITEM LEVEL PREDICTION DETAILS:
{chr(10).join(items_context)}
MATHEMATICAL DEFINITIONS:
1. Weighted Mean Prediction: Sum(w_i * D_i) / Sum(w_i), where recent historical sales get higher weights.
2. Holt's Exponential Smoothing: Models Level L_t = alpha*Y_t + (1-alpha)*(L_{{t-1}}+T_{{t-1}}) and Trend T_t = beta*(L_t - L_{{t-1}}) + (1-beta)*T_{{t-1}}.
3. Safety Stock (SS): SS = Z * sqrt(Lead_Time) * Daily_Demand_StdDev.
4. Reorder Point (ROP): ROP = (Daily_Demand * Lead_Time) + Safety_Stock. If Current Stock <= ROP, a reorder is triggered.
5. Recommended Order Qty: Target Stock (ROP + 1 Month Demand) - Current Stock.
When the user asks about a specific SKU, explain the exact numbers, why it was flagged, and step-by-step how the prediction and reorder quantity were computed.
Keep your answers clear, helpful, professional, and well-formatted with markdown.
"""

        # Format Ollama messages
        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            res = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=45
            )
            if res.status_code == 200:
                content = res.json().get("message", {}).get("content", "")
                return {"reply": content, "source": f"Ollama ({model})"}
        except Exception:
            pass

        # Smart fallback if Ollama is not active
        fallback_reply = self._rule_based_chat_fallback(user_message, items, summary_stats)
        return {"reply": fallback_reply, "source": "Analytical Rule Engine"}

    def _generate_rule_based_report(
        self,
        summary: Dict[str, Any],
        items: List[Dict[str, Any]],
        critical_items: List[Dict[str, Any]],
        overstock_items: List[Dict[str, Any]]
    ) -> str:
        """
        High quality structured analytical report generated when Ollama is offline.
        """
        lines = [
            " Executive Inventory & Demand Prediction Intelligence Report",
            "",
            " 1. Executive Summary",
            f"- Analyzed Portfolio: {summary.get('total_items', len(items))} SKUs across active catalog lines.",
            f"- Immediate Capital Required: ${summary.get('total_reorder_investment', 0):,.2f} across {summary.get('reorder_needed_count', 0)} flagged items.",
            f"- Current Inventory Asset Valuation: ${summary.get('total_stock_value', 0):,.2f}.",
            f"- Supply Chain Vulnerability: {len(critical_items)} SKUs are in critical stockout territory.",
            "",
            " 2.  Critical Stockout & Urgent Replenishment Action Plan",
            "The following items have breached safety stock thresholds and require immediate purchase orders to prevent revenue disruption:",
            "",
            "| SKU | Product Name | Stock | Pred. Demand | ROP | Rec. Order Qty | Est. PO Cost |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
        ]

        if critical_items:
            for it in critical_items:
                lines.append(
                    f"| **{it['sku']}** | {it['name']} | {int(it['current_stock'])} | {it['next_period_forecast']} | {it['reorder_point']} | **{int(it['recommended_order_qty'])} units** | ${it['reorder_investment']:,.2f} |"
                )
        else:
            lines.append("| - | No critical stockouts detected | - | - | - | - | - |")

        lines.extend([
            "",
            " 3.  Excess Working Capital & Overstock Mitigation",
            "Items with over 90 days of inventory remaining (DOI) tying up corporate cash:",
            "",
            "| SKU | Product Name | Current Stock | Days of Supply (DOI) | Tied Capital | Recommendation |",
            "| :--- | :--- | :---: | :---: | :---: | :--- |"
        ])

        if overstock_items:
            for it in overstock_items:
                lines.append(
                    f"| **{it['sku']}** | {it['name']} | {int(it['current_stock'])} | {it['days_of_inventory']} days | ${it['stock_value']:,.2f} | Promotional bundle / Flash sale |"
                )
        else:
            lines.append("| - | No severe overstocks detected | - | - | - | - |")

        lines.extend([
            "",
            " 4.  Mathematical Forecasting Methodology",
            f"1. Primary Demand Model: {summary.get('method_used', 'Weighted Mean Method')}. Recent sales periods are assigned progressively higher coefficients to capture recent market velocity.",
            "2. Safety Stock Buffer Formula: $SS = Z \\times \\sqrt{L} \\times \\sigma_d$, calibrated to the selected service level.",
            "3. Reorder Point (ROP): $ROP = (\\bar{d} \\times L) + SS$. Orders are automatically triggered whenever available inventory drops below this threshold.",
            "",
            "5. 💡 Supply Chain Strategic Directives",
            "- Consolidate Purchase Orders**: Group purchase orders by category and supplier to negotiate volume discounts on high-velocity items.",
            "- Lead Time Compression**: Work with key vendors to reduce lead times on critical items, which will exponentially decrease required safety stock holding costs.",
            "> Note: Connect and run Ollama (`ollama run llama3`) locally to enable dynamic deep AI commentary."
        ])
        return "\n".join(lines)

    def _rule_based_chat_fallback(self, query: str, items: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """
        Answers specific questions if Ollama is not active.
        """
        q_lower = query.lower()

        # Check if asking about a specific SKU
        for it in items:
            if it["sku"].lower() in q_lower or it["name"].lower() in q_lower:
                return (
                    f"Analysis for {it['sku']} - {it['name']}\n\n"
                    f"- Category: {it['category']}\n"
                    f"- Current Stock: {it['current_stock']} units\n"
                    f"- Predicted Next-Period Demand: {it.get('next_period_forecast', 0)} units\n"
                    f"- Lead Time: {it.get('lead_time_days', 14)} days\n"
                    f"- Safety Stock: {it.get('safety_stock', 0)} units\n"
                    f"- Reorder Point (ROP): {it.get('reorder_point', 0)} units\n"
                    f"- Current Status: {it.get('status', 'Healthy')}\n"
                    f"- Recommended Order Quantity: {it.get('recommended_order_qty', 0)} units (Estimated Investment: ${it.get('reorder_investment', 0):,.2f})\n\n"
                    f"How this was calculated:\n"
                    f"1. Daily demand was estimated at `{round(it.get('next_period_forecast', 0)/30, 2)} units/day`.\n"
                    f"2. Lead time demand is `Daily Demand × {it.get('lead_time_days', 14)} days = {it.get('lead_time_demand', 0)} units`.\n"
                    f"3. Adding safety stock of `{it.get('safety_stock', 0)} units` yielded an ROP of `{it.get('reorder_point', 0)}`.\n"
                    f"4. Since current stock is `{it['current_stock']}`, the system recommends ordering `{it.get('recommended_order_qty', 0)} units`."
                )

        if "method" in q_lower or "formula" in q_lower or "weighted mean" in q_lower:
            return (
                "Mathematical Forecasting Breakdown\n\n"
                "1. Weighted Mean / Weighted Moving Average (WMA):\n"
                "   $$\\hat{D} = \\frac{\\sum_{i=1}^n w_i \\cdot D_i}{\\sum w_i}$$\n"
                "   Recent sales periods receive larger weights (e.g. Month 12 gets weight 12, Month 1 gets weight 1).\n\n"
                "2. Holt's Linear Exponential Smoothing:\n"
                "   Tracks both baseline level $(\\alpha)$ and sales trend $(\\beta)$ to project rising or falling demand momentum.\n\n"
                "3. Reorder Point (ROP)**:\n"
                "   $$ROP = (d_{\\text{daily}} \\times \\text{Lead Time}) + (Z \\times \\sqrt{\\text{Lead Time}} \\times \\sigma_{\\text{daily}})$$"
            )

        if "stockout" in q_lower or "urgent" in q_lower or "risk" in q_lower or "reorder" in q_lower:
            reorder_list = [it for it in items if it.get("needs_reorder")]
            sku_str = ", ".join([f"**{it['sku']}** ({it['name']}: {int(it['recommended_order_qty'])} units)" for it in reorder_list[:5]])
            return (
                f"Reorder & Stockout Status\n\n"
                f"- Total items requiring immediate reorder: {len(reorder_list)}\n"
                f"- Estimated reorder procurement budget: ${summary.get('total_reorder_investment', 0):,.2f}\n"
                f"- Top items needing immediate PO: {sku_str if sku_str else 'None'}.\n\n"
                f"You can view all items with the 'Urgent Reorder' badge in the table above."
            )

        return (
            f"SmartInventory AI Copilot\n\n"
            f"Currently monitoring {len(items)} items with {summary.get('reorder_needed_count', 0)} reorder recommendations totaling ${summary.get('total_reorder_investment', 0):,.2f}.\n\n"
            f"You can ask me questions such as:\n"
            f"- 'Why is SKU-101 flagged for reorder?'\n"
            f"- 'Explain how the weighted mean formula was calculated'\n"
            f"- 'Which items are overstocked?'\n"
            f"- 'How much budget do I need to restock all critical items?'\n\n"
            f"(Tip: Start Ollama with `ollama run llama3` for full LLM natural language generation!)*"
        )