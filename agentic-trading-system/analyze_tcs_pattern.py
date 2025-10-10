#!/usr/bin/env python3
"""Analyze TCS pattern with exact dates"""

import asyncio
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

async def analyze_tcs_pattern():
    """Show exact dates of TCS cup and handle formation"""
    
    print("="*80)
    print("TCS.NS CUP & HANDLE PATTERN ANALYSIS")
    print("="*80)
    
    # Get 365 days of data
    ticker = yf.Ticker('TCS.NS')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = ticker.history(start=start_date, end=end_date, interval='1d')
    
    if data.empty:
        print("❌ No data available")
        return
    
    print(f"\n📊 Data Range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"Total days: {len(data)}")
    
    # Last 90 days for pattern
    recent_90 = data.tail(90)
    
    print(f"\n🔍 Pattern Window (Last 90 days):")
    print(f"   Start: {recent_90.index[0].date()}")
    print(f"   End: {recent_90.index[-1].date()}")
    
    # CUP FORMATION (first 70 days, excluding handle)
    cup_section = recent_90.iloc[:-20]
    
    print(f"\n☕ CUP FORMATION:")
    print(f"   Period: {cup_section.index[0].date()} to {cup_section.index[-1].date()}")
    print(f"   Days: {len(cup_section)}")
    
    # Find highest and lowest points in cup
    highest_idx = cup_section['High'].idxmax()
    lowest_idx = cup_section['Low'].idxmin()
    highest_price = cup_section['High'].max()
    lowest_price = cup_section['Low'].min()
    
    print(f"\n   📈 Cup High:")
    print(f"      Date: {highest_idx.date()}")
    print(f"      Price: ₹{highest_price:.2f}")
    
    print(f"\n   📉 Cup Low (Bottom):")
    print(f"      Date: {lowest_idx.date()}")
    print(f"      Price: ₹{lowest_price:.2f}")
    
    depth = (highest_price - lowest_price) / highest_price
    print(f"\n   Depth: {depth*100:.1f}%")
    
    # Analyze cup shape (left side vs right side)
    mid_point = len(cup_section) // 2
    left_side = cup_section.iloc[:mid_point]
    right_side = cup_section.iloc[mid_point:]
    
    print(f"\n   Left Side: {left_side.index[0].date()} to {left_side.index[-1].date()}")
    print(f"      Start: ₹{left_side['Close'].iloc[0]:.2f}")
    print(f"      End: ₹{left_side['Close'].iloc[-1]:.2f}")
    
    print(f"\n   Right Side: {right_side.index[0].date()} to {right_side.index[-1].date()}")
    print(f"      Start: ₹{right_side['Close'].iloc[0]:.2f}")
    print(f"      End: ₹{right_side['Close'].iloc[-1]:.2f}")
    
    # HANDLE FORMATION (last 20 days)
    handle_section = recent_90.tail(20)
    
    print(f"\n🔧 HANDLE FORMATION:")
    print(f"   Period: {handle_section.index[0].date()} to {handle_section.index[-1].date()}")
    print(f"   Days: {len(handle_section)}")
    
    handle_high = handle_section['High'].max()
    handle_low = handle_section['Low'].min()
    current_price = data['Close'].iloc[-1]
    
    handle_high_idx = handle_section['High'].idxmax()
    handle_low_idx = handle_section['Low'].idxmin()
    
    print(f"\n   📈 Handle High:")
    print(f"      Date: {handle_high_idx.date()}")
    print(f"      Price: ₹{handle_high:.2f}")
    
    print(f"\n   📉 Handle Low:")
    print(f"      Date: {handle_low_idx.date()}")
    print(f"      Price: ₹{handle_low:.2f}")
    
    handle_depth = (handle_high - handle_low) / handle_high
    print(f"\n   Handle Depth: {handle_depth*100:.1f}%")
    
    print(f"\n   💰 Current Price: ₹{current_price:.2f}")
    print(f"   Distance to Handle High: {((current_price/handle_high - 1)*100):.1f}%")
    
    # Volume analysis
    cup_volume = cup_section['Volume'].mean()
    handle_volume = handle_section['Volume'].mean()
    volume_change = (handle_volume / cup_volume - 1) * 100
    
    print(f"\n📊 VOLUME ANALYSIS:")
    print(f"   Cup avg volume: {cup_volume:,.0f}")
    print(f"   Handle avg volume: {handle_volume:,.0f}")
    print(f"   Change: {volume_change:+.1f}%")
    
    # Show last 10 days detail
    print(f"\n📅 LAST 10 TRADING DAYS:")
    print(f"{'Date':<12} {'Close':>10} {'Volume':>12} {'Change':>8}")
    print("-" * 50)
    
    last_10 = data.tail(10)
    for idx, row in last_10.iterrows():
        prev_close = data.loc[:idx]['Close'].iloc[-2] if len(data.loc[:idx]) > 1 else row['Close']
        change = ((row['Close'] / prev_close - 1) * 100) if prev_close > 0 else 0
        print(f"{idx.date()!s:<12} ₹{row['Close']:>8.2f} {row['Volume']:>12,.0f} {change:>7.1f}%")
    
    print("\n" + "="*80)
    
    # Pattern validity
    print("\n🎯 PATTERN ASSESSMENT:")
    
    if 0.08 <= depth <= 0.40:
        print(f"   ✅ Cup depth {depth*100:.1f}% is valid (8-40% range)")
    else:
        print(f"   ❌ Cup depth {depth*100:.1f}% is out of range")
    
    if handle_depth < 0.20:
        print(f"   ✅ Handle depth {handle_depth*100:.1f}% is acceptable (<20%)")
    else:
        print(f"   ⚠️  Handle depth {handle_depth*100:.1f}% is deep")
    
    # Check if handle is in upper portion
    handle_position = (handle_low - lowest_price) / (highest_price - lowest_price) if (highest_price - lowest_price) > 0 else 0
    if handle_position > 0.5:
        print(f"   ✅ Handle in upper {handle_position*100:.0f}% of cup (good position)")
    else:
        print(f"   ⚠️  Handle in lower portion (position: {handle_position*100:.0f}%)")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    asyncio.run(analyze_tcs_pattern())
