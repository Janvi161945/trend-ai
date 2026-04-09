import os
from datetime import datetime
from .config import LOG_PATH

def log_event(message, level="INFO"):
    """Log an event to the app.log file and terminal."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [{level}] {message}"
    
    # Print to terminal
    print(formatted_message)
    
    # Write to file
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(formatted_message + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def get_recent_logs(limit=50):
    """Read recent logs from the file."""
    if not os.path.exists(LOG_PATH):
        return ["No logs found yet. Start a refresh to generate activity."]
    
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            return lines[-limit:]
    except Exception as e:
        return [f"Error reading logs: {e}"]

def clear_logs():
    """Clear the log file."""
    if os.path.exists(LOG_PATH):
        try:
            os.remove(LOG_PATH)
        except:
            pass
