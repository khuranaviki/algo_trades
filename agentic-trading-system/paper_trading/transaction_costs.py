"""
Transaction cost modeling

Realistic Indian stock market transaction costs based on NSE 2025 structure
"""

from typing import Dict


class TransactionCostModel:
    """Realistic Indian stock market transaction costs"""

    # NSE cost structure (as of 2025)
    BROKERAGE_PCT = 0.03  # 0.03% or ₹20 per order (whichever lower)
    BROKERAGE_FLAT_MAX = 20.0  # Maximum ₹20 per order

    STT_SELL_PCT = 0.025  # 0.025% on sell side (delivery)
    STT_BUY_PCT = 0.0  # No STT on buy side for delivery

    EXCHANGE_CHARGES_PCT = 0.00325  # 0.00325%
    GST_PCT = 0.18  # 18% on brokerage + exchange charges
    SEBI_CHARGES_PCT = 0.0001  # ₹10 per crore
    STAMP_DUTY_BUY_PCT = 0.015  # 0.015% on buy side
    STAMP_DUTY_SELL_PCT = 0.0  # No stamp duty on sell

    @classmethod
    def calculate_total_cost(cls, order_value: float, action: str) -> Dict[str, float]:
        """
        Calculate all transaction costs for an order

        Args:
            order_value: Total order value in rupees
            action: 'BUY' or 'SELL'

        Returns:
            Dict with breakdown of all costs
        """
        costs = {}

        # 1. Brokerage (lower of 0.03% or ₹20)
        brokerage_pct = order_value * cls.BROKERAGE_PCT / 100
        costs['brokerage'] = min(brokerage_pct, cls.BROKERAGE_FLAT_MAX)

        # 2. STT (Securities Transaction Tax)
        if action == 'SELL':
            costs['stt'] = order_value * cls.STT_SELL_PCT / 100
        else:
            costs['stt'] = 0.0

        # 3. Exchange charges
        costs['exchange'] = order_value * cls.EXCHANGE_CHARGES_PCT / 100

        # 4. GST (on brokerage + exchange charges)
        taxable_amount = costs['brokerage'] + costs['exchange']
        costs['gst'] = taxable_amount * cls.GST_PCT

        # 5. SEBI charges
        costs['sebi'] = order_value * cls.SEBI_CHARGES_PCT / 100

        # 6. Stamp duty
        if action == 'BUY':
            costs['stamp'] = order_value * cls.STAMP_DUTY_BUY_PCT / 100
        else:
            costs['stamp'] = 0.0

        # Total
        costs['total'] = sum(costs.values())
        costs['percentage'] = (costs['total'] / order_value) * 100 if order_value > 0 else 0.0

        return costs

    @classmethod
    def get_summary(cls, order_value: float, action: str) -> str:
        """Get human-readable summary of costs"""
        costs = cls.calculate_total_cost(order_value, action)

        summary = f"""
Transaction Costs ({action}):
Order Value: ₹{order_value:,.2f}

Breakdown:
  Brokerage:       ₹{costs['brokerage']:,.2f}
  STT:             ₹{costs['stt']:,.2f}
  Exchange:        ₹{costs['exchange']:,.2f}
  GST:             ₹{costs['gst']:,.2f}
  SEBI:            ₹{costs['sebi']:,.2f}
  Stamp Duty:      ₹{costs['stamp']:,.2f}
  ─────────────────────────
  TOTAL:           ₹{costs['total']:,.2f} ({costs['percentage']:.3f}%)
"""
        return summary


# Example usage and validation
if __name__ == '__main__':
    print("=" * 60)
    print("NSE Transaction Cost Calculator - 2025")
    print("=" * 60)

    # Test case 1: BUY ₹1,00,000 worth of shares
    print("\nTest Case 1: BUY ₹1,00,000")
    print("-" * 60)
    costs_buy = TransactionCostModel.calculate_total_cost(100000, 'BUY')
    print(TransactionCostModel.get_summary(100000, 'BUY'))

    # Test case 2: SELL ₹1,00,000 worth of shares
    print("\nTest Case 2: SELL ₹1,00,000")
    print("-" * 60)
    costs_sell = TransactionCostModel.calculate_total_cost(100000, 'SELL')
    print(TransactionCostModel.get_summary(100000, 'SELL'))

    # Test case 3: Small order (₹10,000)
    print("\nTest Case 3: BUY ₹10,000 (small order)")
    print("-" * 60)
    costs_small = TransactionCostModel.calculate_total_cost(10000, 'BUY')
    print(TransactionCostModel.get_summary(10000, 'BUY'))

    # Round-trip cost
    print("\n" + "=" * 60)
    print("ROUND-TRIP COST (BUY + SELL ₹1,00,000)")
    print("=" * 60)
    total_roundtrip = costs_buy['total'] + costs_sell['total']
    roundtrip_pct = (total_roundtrip / 100000) * 100
    print(f"\nTotal Cost: ₹{total_roundtrip:,.2f} ({roundtrip_pct:.3f}%)")
    print(f"\nThis means you need {roundtrip_pct:.2f}% profit just to break even!")
