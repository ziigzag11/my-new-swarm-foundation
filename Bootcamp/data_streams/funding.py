import asyncio
import json
import curses  # For real-time terminal UI
from datetime import datetime
from websockets import connect
import os

# Symbols to track
symbols = ['btcusdt', 'ethusdt', 'solusdt', 'wifusdt']
websocket_url_base = 'wss://fstream.binance.com/ws/'
csv_folder = 'C:/Users/erikn/Desktop/Bootcamp/live_data_csv'
csv_filename = os.path.join(csv_folder, 'binance_bigliqs.csv')

if not os.path.exists(csv_folder):
    os.makedirs(csv_folder)

# Shared data storage for funding rates
funding_data = {symbol: "Waiting..." for symbol in symbols}

for symbol in symbols:
    csv_filename = os.path.join(csv_folder, f'{symbol}_funding.csv')
    if not os.path.isfile(csv_filename):
        with open(csv_filename, 'w') as f:
            f.write('Event Time, Symbol, Funding Rate, Yearly Funding Rate\n')

async def binance_funding_stream(symbol):
    """Fetch live funding rates from Binance and update global data."""
    websocket_url = f'{websocket_url_base}{symbol}@markPrice'

    while True:
        try:
            async with connect(websocket_url) as websocket:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    event_time = datetime.fromtimestamp(data['E'] / 1000).strftime("%H:%M:%S")
                    funding_rate = float(data['r'])
                    yearly_funding_rate = (funding_rate * 3 * 365) * 100

                    # Store the latest funding rate
                    funding_data[symbol] = f"{event_time}  {symbol.upper()}  {yearly_funding_rate:.2f}%"

                    # Save to CSV
                    csv_filename = os.path.join(csv_folder, f'{symbol}_funding.csv')
                    with open(csv_filename, 'a') as f:
                        f.write(f"{event_time}, {symbol.upper()}, {funding_rate}, {yearly_funding_rate}\n")

        except Exception as e:
            funding_data[symbol] = f"Error: {e}. Reconnecting..."
            await asyncio.sleep(5)  # Retry after delay

async def display_funding_rates(stdscr):
    """Curses-based UI to display funding rates in real-time."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(100)  # Refresh rate

    # Set up color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)    # High funding
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW) # Medium-high funding
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Medium funding
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Low funding
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Binance Funding Rates (Live Updates)", curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * 40)

        for idx, symbol in enumerate(symbols):
            rate_text = funding_data[symbol]

            # Determine the color based on funding rate
            try:
                rate_value = float(rate_text.split()[-1][:-1])  # Extract numerical value
                if rate_value > 50:
                    color = curses.color_pair(1)
                elif rate_value > 30:
                    color = curses.color_pair(2)
                elif rate_value > 5:
                    color = curses.color_pair(3)
                elif rate_value < -10:
                    color = curses.color_pair(4)
                else:
                    color = curses.color_pair(5)
            except ValueError:
                color = curses.color_pair(5)  # Default color if parsing fails

            # Display funding rate in the UI
            stdscr.addstr(3 + idx, 0, rate_text, color)

        stdscr.refresh()
        await asyncio.sleep(1)  # Refresh every second

async def main():
    """Run both the WebSocket fetchers and UI display."""
    tasks = [binance_funding_stream(symbol) for symbol in symbols]
    tasks.append(curses.wrapper(display_funding_rates))  # Run curses UI
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
