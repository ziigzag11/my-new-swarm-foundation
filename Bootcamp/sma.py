import asyncio
import ccxt
import time
import pandas as pd
import curses  # For real-time terminal UI

# Initialize Kraken API
kraken = ccxt.kraken({
    'enableRateLimit': True,
    'apiKey': 'kf.key["apiKey"]',
    'secret': 'secret',
})

# Symbol to track
symbol = 'BTC/USD'
size = 1
params = {'timeInForce': 'PostOnly'}

# Function to fetch current bid and ask prices
def ask_bid(symbol=symbol):
    ob = kraken.fetch_order_book(symbol)
    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]
    return ask, bid

# Function to get SMA values and market signals
def df_sma(symbol=symbol, timeframe='15m', limit=100, sma=20):
    bars = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df_sma = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    # Calculate SMA and generate signals
    df_sma[f'sma{sma}_{timeframe}'] = df_sma.close.rolling(sma).mean()
    bid = ask_bid(symbol)[1]
    
    # Buy or Sell signals based on the SMA
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] > bid, 'sig'] = 'SELL'
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] < bid, 'sig'] = 'BUY'

    return df_sma

# Live terminal UI using curses
def display_monitor(stdscr):
    """Display live terminal with updated SMA, PNL, and market data."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Non-blocking getch
    stdscr.timeout(100)  # Refresh rate

    # Set up color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)    # White on Red (SELL)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW) # Yellow (Medium)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Cyan (Neutral)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Black on Green (BUY)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default White on Black

    while True:
        stdscr.clear()

        # Display header
        stdscr.addstr(0, 0, "Kraken Live Monitor (SMA, Position, PNL)", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * 60)

        # Fetch the latest SMA and market signals
        sma_data = df_sma(symbol)
        latest_sma = sma_data.iloc[-1]
        sma_signal = latest_sma['sig']
        sma_value = latest_sma[f'sma20_15m']

        # Fetch the latest bid/ask prices
        ask, bid = ask_bid(symbol)

        # Determine the color for Buy/Sell signals
        if sma_signal == 'BUY':
            signal_color = curses.color_pair(4)  # Black on Green for BUY
        elif sma_signal == 'SELL':
            signal_color = curses.color_pair(1)  # White on Red for SELL
        else:
            signal_color = curses.color_pair(5)  # Default color for unknown

        # Display SMA and market signals
        stdscr.addstr(3, 0, f"SMA 20 ({symbol}): {sma_value:.2f} | Signal: {sma_signal} ", signal_color)

        # Display current ask and bid prices
        stdscr.addstr(4, 0, f"Bid: {bid:.2f} | Ask: {ask:.2f}", curses.color_pair(5))

        # Add some space for better readability
        stdscr.addstr(5, 0, "=" * 60)

        # Continuously monitor PNL and update
        pnl_percent = 10  # Replace with actual logic
        stdscr.addstr(6, 0, f"PNL: {pnl_percent:.2f}%", curses.color_pair(3))

        # Refresh the screen
        stdscr.refresh()
        time.sleep(1)  # Sleep for a second before refreshing

# Run curses and monitor loop
def main():
    """Run the live terminal interface inside curses."""
    curses.wrapper(display_monitor)  # Ensures proper initialization

if __name__ == "__main__":
    main()
