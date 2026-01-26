#!/usr/bin/env python3
"""
Neovance AI Application Runner
Single script to start all services automatically
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_colored(message, color):
    print(f"{color}{message}{Colors.NC}")

def print_header():
    print_colored("Starting Neovance AI Application...", Colors.BLUE)
    print_colored("=" * 50, Colors.CYAN)

def check_requirements():
    """Check if required dependencies are available"""
    print_colored("Checking requirements...", Colors.YELLOW)
    
    # Check if we're in the right directory
    if not Path("backend/main.py").exists():
        print_colored("Error: backend/main.py not found. Run from Neovance-AI root directory.", Colors.RED)
        sys.exit(1)
    
    # Check virtual environment
    if not Path("venv/bin/activate").exists() and not Path("venv/Scripts/activate").exists():
        print_colored("Error: Virtual environment not found. Create with 'python -m venv venv'", Colors.RED)
        sys.exit(1)
    
    # Check if node_modules exists for frontend
    if not Path("frontend/dashboard/node_modules").exists():
        print_colored("Warning: node_modules not found. Run 'npm install' in frontend/dashboard", Colors.YELLOW)
    
    print_colored("Requirements check passed", Colors.GREEN)

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.script_dir = Path(__file__).parent.absolute()
        
    def run_command(self, command, cwd=None, name="Process"):
        """Run a command and track the process"""
        try:
            if cwd is None:
                cwd = self.script_dir
            
            print_colored(f"Starting {name}...", Colors.CYAN)
            print_colored(f"   Command: {' '.join(command) if isinstance(command, list) else command}", Colors.PURPLE)
            print_colored(f"   Directory: {cwd}", Colors.PURPLE)
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=isinstance(command, str)
            )
            
            self.processes.append({
                'process': process,
                'name': name,
                'command': command
            })
            
            return process
            
        except Exception as e:
            print_colored(f"Failed to start {name}: {e}", Colors.RED)
            return None
    
    def monitor_process(self, process_info):
        """Monitor a process and print its output"""
        process = process_info['process']
        name = process_info['name']
        
        try:
            for line in process.stdout:
                if line.strip():
                    print_colored(f"[{name}] {line.strip()}", Colors.CYAN)
        except Exception as e:
            print_colored(f"Error monitoring {name}: {e}", Colors.RED)
    
    def start_backend(self):
        """Start the backend API server"""
        # Get python executable from venv
        if os.name == 'nt':  # Windows
            python_exe = self.script_dir / "venv" / "Scripts" / "python.exe"
            activate_script = self.script_dir / "venv" / "Scripts" / "activate"
        else:  # Unix/Linux
            python_exe = self.script_dir / "venv" / "bin" / "python"
            activate_script = self.script_dir / "venv" / "bin" / "activate"
        
        # Command to run uvicorn
        command = [
            str(python_exe), "-m", "uvicorn", 
            "main:app", "--reload", "--port", "8000", "--host", "0.0.0.0"
        ]
        
        process = self.run_command(
            command, 
            cwd=self.script_dir / "backend",
            name="Backend API"
        )
        
        if process:
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(
                target=self.monitor_process, 
                args=[self.processes[-1]], 
                daemon=True
            )
            monitor_thread.start()
        
        return process
    
    def start_simulator(self):
        """Start the pathway simulator"""
        # Initialize data stream first
        data_dir = self.script_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        stream_file = data_dir / "stream.csv"
        with open(stream_file, 'w') as f:
            f.write("timestamp,mrn,hr,spo2,rr,temp,map,risk_score,status\n")
        
        print_colored("Initialized data stream", Colors.GREEN)
        
        # Get python executable from venv
        if os.name == 'nt':  # Windows
            python_exe = self.script_dir / "venv" / "Scripts" / "python.exe"
        else:  # Unix/Linux
            python_exe = self.script_dir / "venv" / "bin" / "python"
        
        command = [str(python_exe), "backend/pathway_simulator.py"]
        
        process = self.run_command(command, name="Pathway Simulator")
        
        if process:
            monitor_thread = threading.Thread(
                target=self.monitor_process, 
                args=[self.processes[-1]], 
                daemon=True
            )
            monitor_thread.start()
        
        return process
    
    def start_etl(self):
        """Start the pathway ETL"""
        # Get python executable from venv
        if os.name == 'nt':  # Windows
            python_exe = self.script_dir / "venv" / "Scripts" / "python.exe"
        else:  # Unix/Linux
            python_exe = self.script_dir / "venv" / "bin" / "python"
        
        command = [str(python_exe), "backend/pathway_etl.py"]
        
        process = self.run_command(command, name="Pathway ETL")
        
        if process:
            monitor_thread = threading.Thread(
                target=self.monitor_process, 
                args=[self.processes[-1]], 
                daemon=True
            )
            monitor_thread.start()
        
        return process
    
    def start_frontend(self):
        """Start the frontend development server"""
        frontend_dir = self.script_dir / "frontend" / "dashboard"
        
        if not frontend_dir.exists():
            print_colored("Frontend directory not found", Colors.RED)
            return None
        
        command = ["npm", "run", "dev"]
        
        process = self.run_command(
            command, 
            cwd=frontend_dir,
            name="Frontend"
        )
        
        if process:
            monitor_thread = threading.Thread(
                target=self.monitor_process, 
                args=[self.processes[-1]], 
                daemon=True
            )
            monitor_thread.start()
        
        return process
    
    def cleanup(self):
        """Terminate all processes"""
        print_colored("\nStopping all services...", Colors.YELLOW)
        
        for process_info in self.processes:
            try:
                process = process_info['process']
                name = process_info['name']
                
                if process.poll() is None:  # Process is still running
                    print_colored(f"   Stopping {name}...", Colors.YELLOW)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print_colored(f"   Force killing {name}...", Colors.RED)
                        process.kill()
                        
            except Exception as e:
                print_colored(f"   Error stopping process: {e}", Colors.RED)
        
        print_colored("All services stopped", Colors.GREEN)

def main():
    print_header()
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print_colored(f"Working directory: {script_dir}", Colors.PURPLE)
    
    # Check requirements
    check_requirements()
    
    # Initialize process manager
    pm = ProcessManager()
    
    def signal_handler(sig, frame):
        pm.cleanup()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start services in sequence
        print_colored("\nStarting Backend API...", Colors.GREEN)
        backend_process = pm.start_backend()
        if not backend_process:
            print_colored("Failed to start backend", Colors.RED)
            return
        
        print_colored("Waiting for backend to start...", Colors.YELLOW)
        time.sleep(5)
        
        print_colored("\nStarting Pathway Simulator...", Colors.GREEN)
        simulator_process = pm.start_simulator()
        
        time.sleep(2)
        
        print_colored("\nStarting Pathway ETL...", Colors.GREEN)
        etl_process = pm.start_etl()
        
        time.sleep(3)
        
        print_colored("\nStarting Frontend...", Colors.GREEN)
        frontend_process = pm.start_frontend()
        
        # Display status
        time.sleep(2)
        print_colored("\n" + "=" * 50, Colors.CYAN)
        print_colored("All services started!", Colors.BLUE)
        print_colored("Access your application:", Colors.BLUE)
        print_colored("   Frontend: http://localhost:3000", Colors.GREEN)
        print_colored("   Backend API: http://localhost:8000", Colors.GREEN)
        print_colored("   API Docs: http://localhost:8000/docs", Colors.GREEN)
        print_colored("\nPress Ctrl+C to stop all services", Colors.YELLOW)
        print_colored("=" * 50, Colors.CYAN)
        
        # Keep the script running
        try:
            while True:
                # Check if any process has died
                for process_info in pm.processes:
                    if process_info['process'].poll() is not None:
                        print_colored(f"{process_info['name']} has stopped", Colors.YELLOW)
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print_colored(f"An error occurred: {e}", Colors.RED)
    
    finally:
        pm.cleanup()

if __name__ == "__main__":
    main()