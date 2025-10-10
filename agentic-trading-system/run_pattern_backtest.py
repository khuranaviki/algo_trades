#!/usr/bin/env python3
"""
Comprehensive Pattern Backtest with Detailed Explanations

Tests all v40 stocks with 5 years of data and provides detailed pattern analysis
"""

import asyncio
import sys
from datetime import datetime, timedelta
from agents.technical_analyst import TechnicalAnalyst
import yfinance as yf

# V40 Watchlist
V40_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS',
    'BAJFINANCE.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'HCLTECH.NS', 'TITAN.NS',
    'KOTAKBANK.NS', 'ULTRACEMCO.NS', 'AXISBANK.NS', 'SUNPHARMA.NS', 'NESTLEIND.NS',
    'WIPRO.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS',
    'TATASTEEL.NS', 'TECHM.NS', 'ADANIPORTS.NS', 'INDUSINDBK.NS', 'JSWSTEEL.NS',
    'BAJAJFINSV.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'BRITANNIA.NS', 'COALINDIA.NS',
    'GRASIM.NS', 'HINDALCO.NS', 'BPCL.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS'
]

async def analyze_all_stocks():
    """Analyze all v40 stocks with 5-year data"""
    
    print("="*100)
    print(" "*30 + "V40 PATTERN BACKTEST")
    print(" "*25 + "5-Year Technical Analysis")
    print("="*100)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(V40_STOCKS)}")
    print(f"Lookback: 5 years")
    print("\n" + "="*100)
    
    # Initialize analyzer
    config = {
        'lookback_days': 1825,  # 5 years
        'detect_patterns': True,
        'min_pattern_confidence': 60.0
    }
    
    analyst = TechnicalAnalyst(config)
    
    # Track patterns found
    patterns_found = {
        'CWH': [],
        'RHS': [],
        'Golden Cross': [],
        'Breakout': []
    }
    
    entry_signals = []
    
    # Analyze each stock
    for i, ticker in enumerate(V40_STOCKS, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(V40_STOCKS)}] 📊 {ticker}")
        print('='*100)
        
        try:
            # Run analysis
            result = await analyst.analyze(ticker, {})
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            # Get current price data for dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1825)
            stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
            
            current_price = result['indicators']['price']['current']
            
            print(f"\n💰 Current Price: ₹{current_price:,.2f}")
            print(f"📊 Technical Score: {result['score']}/100")
            print(f"   - Trend: {result['trend']['score']}/100")
            print(f"   - Momentum: {result['momentum']['score']}/100")
            print(f"   - Volume: {result['volume']['score']}/100")
            print(f"   - Volatility: {result['volatility']['score']}/100")
            
            # Show moving averages
            sma_20 = result['indicators']['price'].get('sma_20')
            sma_50 = result['indicators']['price'].get('sma_50')
            sma_200 = result['indicators']['price'].get('sma_200')
            
            print(f"\n📈 Moving Averages:")
            if sma_20:
                print(f"   - SMA-20:  ₹{sma_20:,.2f} ({((current_price/sma_20-1)*100):+.1f}%)")
            if sma_50:
                print(f"   - SMA-50:  ₹{sma_50:,.2f} ({((current_price/sma_50-1)*100):+.1f}%)")
            if sma_200:
                print(f"   - SMA-200: ₹{sma_200:,.2f} ({((current_price/sma_200-1)*100):+.1f}%)")
            
            # Analyze patterns
            patterns = result.get('patterns', [])
            
            if patterns:
                print(f"\n🎯 {len(patterns)} PATTERN(S) DETECTED:")
                print("="*100)
                
                for pattern in patterns:
                    pattern_type = pattern['type']
                    patterns_found[pattern_type].append(ticker)
                    
                    print(f"\n📐 Pattern: {pattern['name']}")
                    print(f"   Confidence: {pattern['confidence']}%")
                    
                    # Detailed CUP WITH HANDLE analysis
                    if pattern_type == 'CWH':
                        print(f"\n   ☕ CUP FORMATION:")
                        print(f"      - Depth: {pattern['cup_depth_pct']:.1f}%")
                        
                        # Get cup dates from last 90 days
                        recent_90 = stock_data.tail(90)
                        cup_section = recent_90.iloc[:-20]
                        
                        cup_high_date = cup_section['High'].idxmax().date()
                        cup_low_date = cup_section['Low'].idxmin().date()
                        cup_high = cup_section['High'].max()
                        cup_low = cup_section['Low'].min()
                        
                        print(f"      - Cup High: ₹{cup_high:,.2f} on {cup_high_date}")
                        print(f"      - Cup Low:  ₹{cup_low:,.2f} on {cup_low_date}")
                        print(f"      - U-Shape: {pattern.get('u_shape_quality', 'N/A')}")
                        
                        print(f"\n   🔧 HANDLE FORMATION:")
                        print(f"      - Position: {pattern.get('handle_position', 'N/A')}")
                        print(f"      - Depth: {pattern['handle_depth_pct']:.1f}%")
                        
                        handle_section = recent_90.tail(20)
                        handle_high_date = handle_section['High'].idxmax().date()
                        handle_low_date = handle_section['Low'].idxmin().date()
                        handle_high = handle_section['High'].max()
                        handle_low = handle_section['Low'].min()
                        
                        print(f"      - Handle High: ₹{handle_high:,.2f} on {handle_high_date}")
                        print(f"      - Handle Low:  ₹{handle_low:,.2f} on {handle_low_date}")
                        
                        print(f"\n   🎯 ENTRY & TARGETS:")
                        print(f"      - Entry Type: {pattern.get('entry_type', 'N/A')}")
                        print(f"      - Resistance: ₹{pattern.get('resistance', 0):,.2f}")
                        print(f"      - Target (Conservative): ₹{pattern.get('target_conservative', 0):,.2f}")
                        print(f"      - Target (Aggressive): ₹{pattern.get('target_aggressive', 0):,.2f}")
                        
                        if pattern.get('entry_ready'):
                            print(f"\n   ✅ ENTRY SIGNAL: Ready to enter!")
                            entry_signals.append({
                                'ticker': ticker,
                                'pattern': 'Cup with Handle',
                                'entry': current_price,
                                'target': pattern.get('target_conservative', 0)
                            })
                    
                    # Detailed REVERSE HEAD & SHOULDERS analysis
                    elif pattern_type == 'RHS':
                        print(f"\n   👤 STRUCTURE:")
                        print(f"      - Head Depth: {pattern['head_depth_pct']:.1f}%")
                        print(f"      - Shoulder Symmetry: {pattern['shoulder_symmetry_pct']:.1f}%")
                        
                        # Get RHS dates from last 60 days
                        recent_60 = stock_data.tail(60)
                        
                        left_section = recent_60.iloc[0:20]
                        mid_section = recent_60.iloc[15:35]
                        right_section = recent_60.iloc[30:60]
                        
                        left_low = left_section['Low'].min()
                        left_low_date = left_section['Low'].idxmin().date()
                        
                        head_low = mid_section['Low'].min()
                        head_low_date = mid_section['Low'].idxmin().date()
                        
                        right_low = right_section['Low'].min()
                        right_low_date = right_section['Low'].idxmin().date()
                        
                        print(f"\n      - Left Shoulder:  ₹{left_low:,.2f} on {left_low_date}")
                        print(f"      - Head (Lowest):  ₹{head_low:,.2f} on {head_low_date}")
                        print(f"      - Right Shoulder: ₹{right_low:,.2f} on {right_low_date}")
                        
                        print(f"\n   📏 NECKLINE & TARGETS:")
                        neckline = pattern['neckline']
                        target = pattern['target']
                        
                        print(f"      - Neckline: ₹{neckline:,.2f}")
                        print(f"      - Distance to Neckline: {pattern['distance_to_neckline_pct']:+.1f}%")
                        print(f"      - Target: ₹{target:,.2f}")
                        print(f"      - Potential Gain: {pattern['potential_gain_pct']:+.1f}%")
                        
                        print(f"\n   🎯 ENTRY:")
                        print(f"      - Entry Type: {pattern.get('entry_type', 'N/A')}")
                        
                        if pattern.get('entry_ready'):
                            print(f"\n   ✅ ENTRY SIGNAL: Ready to enter!")
                            entry_signals.append({
                                'ticker': ticker,
                                'pattern': 'Reverse Head & Shoulders',
                                'entry': current_price,
                                'target': target
                            })
                    
                    # Other patterns
                    else:
                        for key, value in pattern.items():
                            if key not in ['type', 'name', 'confidence', 'detected_at', 'entry_price']:
                                print(f"      - {key}: {value}")
            
            else:
                print(f"\n❌ No patterns detected")
                print(f"   Highest technical score needed: 70/100 for BUY")
            
            # Show mean reversion setup
            if result['trend']['score'] >= 70:
                print(f"\n💡 MEAN REVERSION SETUP:")
                for signal in result['trend']['signals']:
                    print(f"   - {signal}")
        
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n\n{'='*100}")
    print(" "*35 + "SUMMARY")
    print('='*100)
    
    print(f"\n📊 PATTERNS DETECTED:")
    for pattern_type, tickers in patterns_found.items():
        if tickers:
            print(f"\n{pattern_type}:")
            for ticker in tickers:
                print(f"   - {ticker}")
    
    if entry_signals:
        print(f"\n\n✅ ENTRY SIGNALS ({len(entry_signals)} stocks):")
        print("="*100)
        
        for signal in entry_signals:
            potential_gain = ((signal['target'] / signal['entry']) - 1) * 100
            print(f"\n🎯 {signal['ticker']} - {signal['pattern']}")
            print(f"   Entry: ₹{signal['entry']:,.2f}")
            print(f"   Target: ₹{signal['target']:,.2f}")
            print(f"   Potential Gain: {potential_gain:+.1f}%")
    else:
        print(f"\n❌ No entry signals detected in current market conditions")
    
    print("\n" + "="*100)
    print("Analysis complete!")
    print("="*100 + "\n")

if __name__ == '__main__':
    try:
        asyncio.run(analyze_all_stocks())
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
