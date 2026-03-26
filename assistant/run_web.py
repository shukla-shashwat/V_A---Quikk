# run_web.py
"""
Launch Qwikk web interface
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        import uvicorn
    except ImportError:
        print("Installing required packages...")
        os.system("pip install fastapi uvicorn websockets")
        import uvicorn
    
    from web.server import app
    
    print("""
    ╔═══════════════════════════════════════════╗
    ║                                           ║
    ║     ⚡  Q W I K K  ⚡                      ║
    ║                                           ║
    ║     Your Gen-Z AI Assistant               ║
    ║                                           ║
    ║     Open: http://127.0.0.1:8000          ║
    ║                                           ║
    ║     Press Ctrl+C to stop                  ║
    ║                                           ║
    ╚═══════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
