'''
Fixed Coinbase Data Fetching Script
'''
import pandas as pd
import datetime
import os
import ccxt
import dontshare as d
from math import ceil
import time

# Extract API key values correctly
api_key = d.api_key["apiKey"] if isinstance(d.api_key, dict) else d.api_key
api_secret = d.api_secret["secret"] if isinstance(d.api_secret, dict) else d.api_secret

# Initialize Coinbase API
try:
    coinbase = ccxt.coinbase({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    print("✅ Coinbase API Initialized Successfully!")
except Exception as e:
    print(f"⚠️ Error initializing Coinbase API: {e}")
    coinbase = None  # Prevent script from crashing

# Set parameters
symbol = 'XRP/USD'  # May need to be changed dynamically
timeframe = '1h'
weeks = 100

# Function to convert timeframe to seconds
def timeframe_to_sec(timeframe):
    if 'm' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60
    elif 'h' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60 * 60
    elif 'd' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 24 * 60 * 60

def get_historical_data(symbol, timeframe, weeks):
    """Fetch historical OHLCV data from Coinbase."""
    
    # Check if data already exists
    filename = f'{symbol.replace("/", "-")}-{timeframe}-{weeks}wks-data.csv'
    if os.path.exists(filename):
        return pd.read_csv(filename)

    if not coinbase:
        print("⚠️ Coinbase API is not initialized. Exiting...")
        return None

    # Load market symbols and validate
    markets = coinbase.load_markets()
    if symbol not in markets:
        print(f"⚠️ Symbol {symbol} not found in Coinbase markets. Checking for alternative format...")
        for market in markets:
            if "BTC" in market and "USD" in market:
                print(f"✅ Using alternative market symbol: {market}")
                symbol = market
                break
        else:
            print("❌ No suitable symbol found. Exiting.")
            return None

    # Convert timeframe to granularity
    granularity = timeframe_to_sec(timeframe)

    # Calculate total historical time required
    total_time = weeks * 7 * 24 * 60 * 60  # Total time in seconds
    run_times = ceil(total_time / (granularity * 200))

    dataframe = pd.DataFrame()
    now = datetime.datetime.utcnow()

    for i in range(run_times):
        since = now - datetime.timedelta(seconds=granularity * 200 * (i + 1))
        since_timestamp = int(since.timestamp()) * 1000  # Convert to milliseconds

        print(f"📊 Fetching data since: {since} (Timestamp: {since_timestamp})")

        try:
            data = coinbase.fetch_ohlcv(symbol, timeframe, since=since_timestamp, limit=200)
            if not data:
                print("⚠️ No data returned for this time period.")
                continue

            df = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            dataframe = pd.concat([df, dataframe])

            # Respect API rate limits
            time.sleep(1.5)  # Adjust based on Coinbase's rate limits

        except Exception as e:
            print(f"⚠️ Error fetching data: {e}")
            time.sleep(5)  # Wait before retrying next batch

    if dataframe.empty:
        print("⚠️ No historical data fetched. Exiting...")
        return None

    dataframe.set_index('datetime', inplace=True)
    dataframe = dataframe[["open", "high", "low", "close", "volume"]]

    # Save to CSV
    filename = "C:/Users/erikn/Desktop/Bootcamp/historical_data.csv"
    filename = os.path.join("C:/Users/erikn/Desktop/Bootcamp/historical_data", f'{symbol.replace("/", "-")}-{timeframe}-{weeks}wks-data.csv')
    dataframe.to_csv(filename)
    print(f"✅ Data saved to {filename}")

    return dataframe

# Run the function and print the result
historical_data = get_historical_data(symbol, timeframe, weeks)
if historical_data is not None:
    print(historical_data.tail(5))  # Show the last 5 rows
