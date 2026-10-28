import sys
import os
import platform
import socket
import datetime

def main():
    print("=" * 50)
    print("  ULTRON Windows Tool v1.0")
    print("=" * 50)
    print(f"OS       : {platform.system()} {platform.release()}")
    print(f"Machine  : {platform.machine()}")
    print(f"Hostname : {socket.gethostname()}")
    print(f"User     : {os.getenv('USERNAME', os.getenv('USER', 'unknown'))}")
    print(f"Time     : {datetime.datetime.now()}")
    print(f"Python   : {sys.version.split()[0]}")
    print("=" * 50)
    print("Tool ready. Press Enter to exit.")
    input()

if __name__ == "__main__":
    main()
