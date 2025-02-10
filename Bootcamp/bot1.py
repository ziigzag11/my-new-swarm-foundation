############# Trading Bot #1 - Reinforcement Learning + R-Factor 2024

import ccxt
import pandas as pd
import numpy as np
import key_file as ds
import time
import schedule
from datetime import datetime

# Initialize Kraken API
kraken = ccxt.kraken({
    'enableRateLimit': True,
    'apiKey': ds.key["apiKey"],
    'secret': ds.secret["secret"],
})

# Bot Configuration
symbol = 'BTC/USD'
capital = 100  # Starting capital
risk_per_trade = 10  # Always risking $10 per trade
leverage = 5  # 5x leverage
r_factor = 2  # Always aiming for at least 1:2 risk-reward
min_win_rate = 35  # Aim for 35% win rate
trailing_stop = True  # Enable trailing stop in future

# Risk Management Formula
def calculate_position_size(entry, stop_loss):
    """
    Uses R-Factor to determine trade size.
    Position Size = Risk Amount / (Entry Price - Stop Loss)
    """
    risk_amount = risk_per_trade  # Fixed risk per trade
    pos_size = risk_amount / (entry - stop_loss)
    pos_size = round(pos_size, 6)  # Avoid too many decimal places

    # Adjust for leverage
    leverage_used = pos_size * entry / leverage
    return pos_size, leverage_used

# Fetch Market Data
def fetch_sma(timeframe, period=20):
    """
    Fetch Simple Moving Average (SMA) for the given timeframe.
    """
    bars = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=period)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['sma'] = df['close'].rolling(period).mean()
    return df

# Fetch Order Book Data
def get_bid_ask():
    """
    Fetches the best bid and ask prices from Kraken.
    """
    ob = kraken.fetch_order_book(symbol)
    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]
    return ask, bid

# Determine Trade Signal
def generate_signal():
    """
    Uses SMA and Order Book data to determine trade signals.
    """
    df_1d = fetch_sma('1d')
    df_15m = fetch_sma('15m')

    bid = get_bid_ask()[1]
    sma_1d = df_1d.iloc[-1]['sma']
    sma_15m = df_15m.iloc[-1]['sma']

    if bid > sma_1d and bid > sma_15m:
        return "BUY"
    elif bid < sma_1d and bid < sma_15m:
        return "SELL"
    else:
        return "HOLD"

# Open Positions
def execute_trade():
    """
    Opens a trade based on R-Factor, Risk Management & Trade Signals.
    """
    signal = generate_signal()
    ask, bid = get_bid_ask()

    # Define Stop Loss and Take Profit based on R-Factor
    if signal == "BUY":
        entry_price = ask
        stop_loss = entry_price * 0.99  # 1% below
        take_profit = entry_price * (1 + (r_factor * (entry_price - stop_loss) / entry_price))
    elif signal == "SELL":
        entry_price = bid
        stop_loss = entry_price * 1.01  # 1% above
        take_profit = entry_price * (1 - (r_factor * (entry_price - stop_loss) / entry_price))
    else:
        print("⚠️ No valid trade signal. Skipping trade.")
        return

    # Calculate Position Size
    pos_size, leverage_used = calculate_position_size(entry_price, stop_loss)

    print(f"🚀 Executing {signal} Trade: Entry={entry_price}, Stop Loss={stop_loss}, Take Profit={take_profit}, Size={pos_size}")

    # Place Order on Kraken
    if signal == "BUY":
        kraken.create_limit_buy_order(symbol, pos_size, entry_price, {'leverage': leverage})
    elif signal == "SELL":
        kraken.create_limit_sell_order(symbol, pos_size, entry_price, {'leverage': leverage})

    print(f"✅ Trade Executed: {symbol} {signal} @ {entry_price}")

# Trailing Stop Loss (Optional for Future)
def trailing_stop_loss():
    """
    Moves the Stop Loss to lock in profits if price moves favorably.
    """
    print("🛑 Trailing Stop Loss Not Yet Implemented")

# Close Positions Based on PNL
def close_positions():
    """
    Checks open positions and closes if Take Profit or Stop Loss is hit.
    """
    positions = kraken.fetch_positions()
    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['contracts']
        entry_price = float(pos['entryPrice'])
        current_price = get_bid_ask()[1] if side == "long" else get_bid_ask()[0]
        pnl_percentage = ((current_price - entry_price) / entry_price) * leverage * 100

        print(f"🔍 {symbol} {side} Position: Entry={entry_price}, Current={current_price}, PNL={pnl_percentage:.2f}%")

        # Close if Stop Loss or Take Profit is hit
        if pnl_percentage >= (r_factor * 100) or pnl_percentage <= -100:
            print(f"🔴 Closing {side} position on {symbol}")
            if side == "long":
                kraken.create_limit_sell_order(symbol, size, current_price)
            else:
                kraken.create_limit_buy_order(symbol, size, current_price)

# Schedule Bot Execution
schedule.every(30).seconds.do(execute_trade)
schedule.every(60).seconds.do(close_positions)

# Start the Trading Bot
if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"⚠️ Bot Error: {e}")
            time.sleep(30)
