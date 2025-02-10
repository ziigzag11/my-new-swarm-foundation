import subprocess
import time

# List of all data stream scripts
scripts = [
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/recent_trades.py",
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/funding.py",
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/huge_trades.py",
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/funding.py",
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/liquidation_data.py",
    "c:/Users/erikn/Desktop/Bootcamp/data_streams/big_liquids.py"
]

# Start each script in a separate terminal
processes = []
for script in scripts:
    print(f"🚀 Starting {script} in a new terminal...")
    process = subprocess.Popen(["start", "cmd", "/k", "python", script], shell=True)
    processes.append(process)
    time.sleep(5)  # Small delay to avoid startup conflicts
    print(f"✅ Successfully started {script}")

print("✅ All data streams are running. Press Ctrl+C to stop.")

# Keep the script alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopping all data streams...")
    for process in processes:
        process.terminate()
    print("✅ All processes stopped.")
