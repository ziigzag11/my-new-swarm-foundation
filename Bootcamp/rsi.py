############ Coding RSI Indicator 2024

# RSI Indicator with Live Market Data
import ccxt
import time
import pandas as pd
import curses  # For real-time terminal UI
from ta.momentum import RSIIndicator

# Initialize Kraken API
try:
    kraken = ccxt.kraken({
        'enableRateLimit': True,
        'apiKey': 'kf.key["apiKey"]',
        'secret': 'secret',
    })
except Exception as e:
    print(f"⚠️ Error initializing Kraken API: {e}")
    kraken = None

# Symbol to track
SYMBOL = 'BTC/USD'
TIMEFRAME = '15m'
LIMIT = 100
RSI_PERIOD = 14

def fetch_order_book(symbol=SYMBOL):
    """Fetch the latest bid/ask price from Kraken order book."""
    if not kraken:
        return None, None

    try:
        ob = kraken.fetch_order_book(symbol)
        bid = ob['bids'][0][0]
        ask = ob['asks'][0][0]
        return ask, bid
    except Exception as e:
        print(f"⚠️ Error fetching order book: {e}")
        return None, None

def df_rsi(symbol=SYMBOL, timeframe=TIMEFRAME, limit=LIMIT):
    """Fetch RSI values for the given symbol and timeframe."""
    try:
        if not kraken:
            return None

        bars = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Compute RSI
        rsi = RSIIndicator(df['close'], window=RSI_PERIOD)
        df['rsi'] = rsi.rsi()

        # Determine RSI signal
        df['rsi_signal'] = df['rsi'].apply(lambda x: 'BUY' if x < 30 else 'SELL' if x > 70 else 'HOLD')

        return df
    except Exception as e:
        print(f"⚠️ Error fetching RSI: {e}")
        return None

# Live terminal UI using curses
def display_rsi_monitor(stdscr):
    """Display live terminal with updated RSI and market data."""
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
        stdscr.addstr(0, 0, "Kraken Live Monitor (RSI & Market Data)", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * 60)

        # Fetch the latest RSI and market signals
        rsi_data = df_rsi(SYMBOL)
        if rsi_data is None:
            stdscr.addstr(3, 0, "⚠️ Error fetching RSI data.")
            stdscr.refresh()
            time.sleep(2)
            continue
        
        latest_rsi = rsi_data.iloc[-1]
        rsi_value = latest_rsi['rsi']
        rsi_signal = latest_rsi['rsi_signal']

        # Fetch the latest bid/ask prices
        ask, bid = fetch_order_book(SYMBOL)

        # Determine the color for Buy/Sell signals
        if rsi_signal == 'BUY':
            signal_color = curses.color_pair(2)  # Black on Green for BUY
        elif rsi_signal == 'SELL':
            signal_color = curses.color_pair(1)  # White on Red for SELL
        else:
            signal_color = curses.color_pair(3)  # Yellow for HOLD

        # Display RSI values and market signals
        stdscr.addstr(3, 0, f"RSI ({SYMBOL}): {rsi_value:.2f} | Signal: {rsi_signal} ", signal_color)

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
    curses.wrapper(display_rsi_monitor)  # Ensures proper initialization

if __name__ == "__main__":
    main()
