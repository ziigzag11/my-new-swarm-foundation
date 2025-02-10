############# VWAP Indicator 2024

import ccxt
import key_file as k
import time
import pandas as pd
import curses  # For real-time terminal UI

# Initialize Kraken API
try:
    kraken = ccxt.kraken({
        'enableRateLimit': True,
        'apiKey': k.key["apiKey"],
        'secret': k.secret["secret"],
    })
    
    print("✅ Kraken API Initialized Successfully!")
except Exception as e:
    print(f"⚠️ Error initializing Kraken API: {e}")
    kraken = None  # Prevent crashes if API fails

# Constants
USER_SYMBOL = 'BTC/USD'  # This is what you input
TIMEFRAME = '15m'
LIMIT = 100

def get_kraken_symbol(user_symbol):
    """Convert user symbol (BTC/USD) to Kraken's format dynamically."""
    try:
        if not kraken:
            print("⚠️ Kraken API not initialized.")
            return None

        markets = kraken.load_markets()
        for market in markets:
            if user_symbol in market or market.replace("/", "") == user_symbol.replace("/", ""):
                print(f"✅ Using Kraken symbol: {market}")
                return market
        
        print(f"⚠️ No matching symbol found for {user_symbol}. Check Kraken's available pairs.")
        return None
    except Exception as e:
        print(f"⚠️ Error loading Kraken markets: {e}")
        return None

# Dynamically fetch the correct symbol
KRAKEN_SYMBOL = get_kraken_symbol(USER_SYMBOL)

def fetch_order_book(symbol=KRAKEN_SYMBOL):
    """Fetch the latest bid/ask price from Kraken order book."""
    if not kraken or not symbol:
        return None, None

    try:
        ob = kraken.fetch_order_book(symbol)
        bid = ob['bids'][0][0]
        ask = ob['asks'][0][0]
        return ask, bid
    except Exception as e:
        print(f"⚠️ Error fetching order book: {e}")
        return None, None

def get_df_vwap(symbol=KRAKEN_SYMBOL, timeframe=TIMEFRAME, limit=LIMIT):
    """Fetch OHLCV data and calculate VWAP."""
    try:
        if not kraken or not symbol:
            return None

        bars = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not bars:
            print(f"⚠️ No OHLCV data received for {symbol}.")
            return None

        df_vwap = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_vwap['timestamp'] = pd.to_datetime(df_vwap['timestamp'], unit='ms')

        # Compute VWAP
        df_vwap['volXclose'] = df_vwap['close'] * df_vwap['volume']
        df_vwap['cum_vol'] = df_vwap['volume'].cumsum()
        df_vwap['cum_volXclose'] = (df_vwap['volume'] * (df_vwap['high'] + df_vwap['low'] + df_vwap['close']) / 3).cumsum()
        df_vwap['VWAP'] = df_vwap['cum_volXclose'] / df_vwap['cum_vol']

        df_vwap = df_vwap.fillna(0)
        return df_vwap

    except Exception as e:
        print(f"⚠️ Error fetching VWAP data for {symbol}: {e}")
        return None

# Live terminal UI using curses
def display_vwap_monitor(stdscr):
    """Display live terminal with updated VWAP and market data."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Non-blocking getch
    stdscr.timeout(100)  # Refresh rate

    # Set up color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)    # White on Red (SELL)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Black on Green (BUY)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW) # Yellow (Neutral)

    while True:
        stdscr.clear()

        # Display header
        stdscr.addstr(0, 0, "Kraken Live Monitor (VWAP & Market Data)", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * 60)

        # Fetch the latest VWAP data
        vwap_data = get_df_vwap(KRAKEN_SYMBOL)
        if vwap_data is None:
            stdscr.addstr(3, 0, "⚠️ Error fetching VWAP data.")
            stdscr.refresh()
            time.sleep(2)
            continue

        latest_vwap = vwap_data.iloc[-1]
        vwap_value = latest_vwap['VWAP']

        # Fetch the latest bid/ask prices
        ask, bid = fetch_order_book(KRAKEN_SYMBOL)

        # Determine VWAP trend (above/below)
        if bid is None or ask is None:
            vwap_signal = "⚠️ No Market Data"
            trend_color = curses.color_pair(3)
        elif bid > vwap_value:
            trend_color = curses.color_pair(2)  # Green for bullish trend
            vwap_signal = "BUY"
        elif bid < vwap_value:
            trend_color = curses.color_pair(1)  # Red for bearish trend
            vwap_signal = "SELL"
        else:
            trend_color = curses.color_pair(3)  # Yellow for neutral
            vwap_signal = "HOLD"

        # Display VWAP values and market signals
        stdscr.addstr(3, 0, f"VWAP ({KRAKEN_SYMBOL}): {vwap_value:.2f} | Signal: {vwap_signal} ", trend_color)

        # Display current ask and bid prices
        stdscr.addstr(4, 0, f"Bid: {bid:.2f} | Ask: {ask:.2f}", curses.color_pair(3))

        # Add some space for better readability
        stdscr.addstr(5, 0, "=" * 60)

        # Refresh the screen
        stdscr.refresh()
        time.sleep(1)  # Sleep for a second before refreshing

# Run curses and monitor loop
def main():
    """Run the live terminal interface inside curses."""
    curses.wrapper(display_vwap_monitor)  # Ensures proper initialization

if __name__ == "__main__":
    main()
