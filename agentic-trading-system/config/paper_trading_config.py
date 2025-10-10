"""
Paper Trading Configuration

All settings for paper trading system
"""

PAPER_TRADING_CONFIG = {
    # Capital
    'initial_capital': 1000000,  # ₹10 lakhs

    # Watchlist (10 high-quality stocks)
    'watchlist': [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS',
        'INFY.NS',
        'ICICIBANK.NS',
        'BHARTIARTL.NS',
        'BAJFINANCE.NS',
        'TITAN.NS',
        'MARUTI.NS',
        'TATAMOTORS.NS'
    ],

    # Data stream settings
    'update_interval_seconds': 60,  # Scan every 60 seconds
    'cache_max_days': 1825,  # 5 years of historical data

    # Order execution
    'slippage_pct': 0.05,  # 0.05% slippage
    'use_realistic_costs': True,  # Use NSE transaction costs

    # Risk management
    'risk_management': {
        'max_position_size_pct': 5.0,  # Max 5% per position
        'max_portfolio_risk_pct': 2.0,  # Max 2% risk per trade
        'max_open_positions': 10,  # Max 10 concurrent positions
        'max_sector_exposure_pct': 30.0,  # Max 30% per sector
        'max_drawdown_pct': 10.0,  # Stop if 10% drawdown
        'daily_loss_limit_pct': 3.0,  # Stop trading if 3% daily loss
        'reduce_size_on_losses': True,  # Reduce size after losses
        'loss_streak_threshold': 3  # After 3 losses, reduce size
    },

    # Orchestrator configuration
    'orchestrator': {
        # Agent weights
        'weights': {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10,
            'risk_adjustment': 0.10
        },

        # Decision thresholds
        'buy_threshold': 70.0,
        'strong_buy_threshold': 85.0,
        'sell_threshold': 40.0,
        'max_position_size': 0.05,
        'initial_capital': 1000000,

        # Technical analysis config (5 YEARS)
        'technical_config': {
            'detect_patterns': True,
            'validate_patterns': True,  # Enable historical pattern validation
            'lookback_days': 1825,  # 5 years
            'min_pattern_confidence': 60.0,  # Lowered for fuzzy logic
            'aggressive_success_threshold': 0.70,  # 70% for aggressive targets
            'conservative_success_threshold': 0.55,  # 55% for conservative targets
            'min_risk_reward': 2.0,  # Minimum 2:1 risk/reward ratio
            # NO holding day limits - patterns validated against ALL future data
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2
        },

        # Backtest validation (5 YEARS)
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0,
            'min_trades': 10,
            'min_sharpe': 1.0,
            'max_drawdown': -20.0
        },

        # Fundamental analysis config
        'fundamental_config': {
            'use_perplexity': True,
            'use_llm': True,
            'llm_provider': 'openai',
            'llm_model': 'gpt-4-turbo'
        },

        # Sentiment analysis config
        'sentiment_config': {
            'news_lookback_days': 30,
            'use_perplexity': True
        },

        # Management quality config
        'management_config': {
            'quarters_to_analyze': 4,
            'use_llm': True,
            'llm_provider': 'anthropic',
            'llm_model': 'claude-3-5-sonnet-20241022'
        }
    }
}


# Test configuration (for faster testing)
TEST_CONFIG = {
    **PAPER_TRADING_CONFIG,

    'initial_capital': 100000,  # ₹1 lakh for testing

    'watchlist': [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS'
    ],

    'update_interval_seconds': 30,  # Faster updates for testing

    'orchestrator': {
        **PAPER_TRADING_CONFIG['orchestrator'],
        'initial_capital': 100000
    }
}
