#!/usr/bin/env python3
"""
Neovance AI Application Runner
Comprehensive runner for NICU Monitoring System with EOS Risk Calculator
Supports demo mode and full stack deployment
"""

import subprocess
import sys
import os
import time
import signal
import threading
import argparse
import sqlite3
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
    print_colored("🏥 NEOVANCE AI - NICU MONITORING SYSTEM", Colors.BLUE)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("🔬 Featuring Puopolo/Kaiser EOS Risk Calculator", Colors.GREEN)
    print_colored("🎯 Validated clinical decision support for NICU", Colors.GREEN)
    print_colored("=" * 60, Colors.CYAN)

def run_eos_demo():
    """Run the EOS Risk Calculator demonstration"""
    print_colored("\n🧪 Running EOS Calculator Validation Tests...", Colors.YELLOW)
    
    script_dir = Path(__file__).parent.absolute()
    
    try:
        # Run EOS calculator tests
        result = subprocess.run([
            sys.executable, "backend/test_eos_calculator.py"
        ], cwd=script_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            print_colored("✅ EOS Calculator validation passed!", Colors.GREEN)
        else:
            print_colored("❌ EOS Calculator tests failed:", Colors.RED)
            print(result.stderr)
            return False
        
        # Run EOS simulation
        print_colored("\n🔄 Running EOS Risk Calculation Simulation...", Colors.YELLOW)
        result = subprocess.run([
            sys.executable, "backend/pathway_eos_simulator.py"
        ], cwd=script_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            print_colored("✅ EOS simulation completed successfully!", Colors.GREEN)
        else:
            print_colored("❌ EOS simulation failed:", Colors.RED)
            print(result.stderr)
            return False
        
        # Check database
        print_colored("\n💾 Checking EOS data in database...", Colors.YELLOW)
        try:
            conn = sqlite3.connect(script_dir / 'backend/neonatal_ehr.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM live_vitals WHERE risk_score > 0')
            count = cursor.fetchone()[0]
            cursor.execute('SELECT mrn, risk_score, status FROM live_vitals ORDER BY created_at DESC LIMIT 3')
            recent = cursor.fetchall()
            conn.close()
            
            print(f'📊 Records with EOS scores: {count}')
            print('🔍 Recent entries:')
            for row in recent:
                print(f'   MRN:{row[0]} EOS:{row[1]}/1000 Status:{row[2]}')
            print_colored("✅ Database verification successful!", Colors.GREEN)
        except Exception as e:
            print_colored(f"⚠️  Database check: {e} (normal if first run)", Colors.YELLOW)
        
        # Final status
        print_colored("\n" + "=" * 60, Colors.CYAN)
        print_colored("🎊 EOS RISK CALCULATOR DEMONSTRATION COMPLETE!", Colors.BLUE)
        print_colored("\n📈 Key Features Demonstrated:", Colors.PURPLE)
        print_colored("   ✓ Validated Puopolo/Kaiser algorithm", Colors.GREEN)
        print_colored("   ✓ Real-time risk calculation (0.5-50/1000 births)", Colors.GREEN)
        print_colored("   ✓ Clinical status categories (ROUTINE/ENHANCED/HIGH)", Colors.GREEN)
        print_colored("   ✓ Database integration with SQLite", Colors.GREEN)
        print_colored("   ✓ Maternal risk factor assessment", Colors.GREEN)
        print_colored("\n🏆 Production-ready clinical decision support!", Colors.BLUE)
        print_colored("=" * 60, Colors.CYAN)
        
        return True
        
    except Exception as e:
        print_colored(f"❌ Demo failed: {e}", Colors.RED)
        return False

def check_requirements():
    """Check if required dependencies are available"""
    print_colored("Checking requirements...", Colors.YELLOW)
    
    # Check if we're in the right directory
    if not Path("backend/main.py").exists():
        print_colored("Error: backend/main.py not found. Run from Neovance-AI root directory.", Colors.RED)
        sys.exit(1)
    
    # Check virtual environment
    if not Path("venv/bin/activate").exists() and not Path("venv/Scripts/activate").exists():
        print_colored("Warning: Virtual environment not found. Some features may not work.", Colors.YELLOW)
    
    # Check if node_modules exists for frontend
    if not Path("frontend/dashboard/node_modules").exists():
        print_colored("Warning: node_modules not found. Run 'npm install' in frontend/dashboard", Colors.YELLOW)
    
    # Check EOS calculator availability
    if Path("backend/pathway_eos_simulator.py").exists():
        print_colored("✓ EOS Risk Calculator available", Colors.GREEN)
    else:
        print_colored("Warning: EOS Risk Calculator not found", Colors.YELLOW)
    
    print_colored("Requirements check completed", Colors.GREEN)

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
        """Start the EOS pathway simulator"""
        # Initialize EOS data stream first
        data_dir = self.script_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Check if EOS data exists, if not create it
        eos_file = data_dir / "stream_eos.csv"
        if not eos_file.exists():
            with open(eos_file, 'w') as f:
                f.write("timestamp,mrn,hr,spo2,rr,temp,map,ga_weeks,ga_days,temp_celsius,rom_hours,gbs_status,antibiotic_type,clinical_exam\n")
                # Add initial sample EOS data
                f.write("2026-01-26T00:00:00,B001,80.0,98.0,20.0,37.0,35.0,38,3,37.2,8,negative,none,normal\n")
        
        # Also ensure regular stream exists for fallback
        stream_file = data_dir / "stream.csv"
        if not stream_file.exists():
            with open(stream_file, 'w') as f:
                f.write("timestamp,mrn,hr,spo2,rr,temp,map,risk_score,status\n")
        
        print_colored("Initialized EOS data streams", Colors.GREEN)
        
        # Get python executable from venv
        if os.name == 'nt':  # Windows
            python_exe = self.script_dir / "venv" / "Scripts" / "python.exe"
        else:  # Unix/Linux
            python_exe = self.script_dir / "venv" / "bin" / "python"
        
        # Try EOS simulator first, fallback to regular simulator
        eos_simulator = self.script_dir / "backend" / "pathway_eos_simulator.py"
        if eos_simulator.exists():
            command = [str(python_exe), "backend/pathway_eos_simulator.py"]
            print_colored("Using EOS Risk Calculator simulator", Colors.GREEN)
        else:
            command = [str(python_exe), "backend/pathway_simulator.py"]
            print_colored("Using standard simulator (EOS not available)", Colors.YELLOW)
        
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
        """Start the EOS pathway ETL"""
        # Get python executable from venv
        if os.name == 'nt':  # Windows
            python_exe = self.script_dir / "venv" / "Scripts" / "python.exe"
        else:  # Unix/Linux
            python_exe = self.script_dir / "venv" / "bin" / "python"
        
        # Try EOS ETL first, fallback to regular ETL
        eos_etl = self.script_dir / "backend" / "pathway_etl_eos.py"
        if eos_etl.exists():
            command = [str(python_exe), "backend/pathway_etl_eos.py"]
            print_colored("Using EOS Risk Calculator ETL Pipeline", Colors.GREEN)
        else:
            command = [str(python_exe), "backend/pathway_etl.py"]
            print_colored("Using standard ETL (EOS not available)", Colors.YELLOW)
        
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Neovance AI - NICU Monitoring System with EOS Risk Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_neovance.py                    # Full stack mode (default)
  python run_neovance.py --demo             # EOS calculator demo only
  python run_neovance.py --full-stack      # Full stack mode (explicit)
  python run_neovance.py --demo --verbose  # Verbose demo output
  
The EOS Risk Calculator provides validated clinical decision support based on 
the Puopolo/Kaiser Early-Onset Sepsis risk stratification model.
        """
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Run EOS Risk Calculator demonstration only (no web services)'
    )
    
    parser.add_argument(
        '--full-stack', 
        action='store_true',
        help='Run complete application stack (default behavior)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--skip-frontend',
        action='store_true',
        help='Start backend and data services only (no frontend)'
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print_colored(f"Working directory: {script_dir}", Colors.PURPLE)
    
    # Check requirements
    check_requirements()
    
    # Determine mode
    if args.demo:
        print_colored("\n🎯 Running in EOS DEMO mode", Colors.BLUE)
        success = run_eos_demo()
        if success:
            print_colored("\n💡 To run the full application stack:", Colors.CYAN)
            print_colored("   python run_neovance.py --full-stack", Colors.CYAN)
        sys.exit(0 if success else 1)
    
    # Default to full stack mode
    print_colored(f"\n🚀 Running in FULL STACK mode", Colors.BLUE)
    print_colored("   Use --demo flag for EOS calculator demo only", Colors.PURPLE)
    
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
        print_colored("\n🔧 Starting Backend API...", Colors.GREEN)
        backend_process = pm.start_backend()
        if not backend_process:
            print_colored("Failed to start backend", Colors.RED)
            return
        
        print_colored("Waiting for backend to initialize...", Colors.YELLOW)
        time.sleep(5)
        
        print_colored("\n🔬 Starting EOS Pathway Simulator...", Colors.GREEN)
        simulator_process = pm.start_simulator()
        
        time.sleep(3)  # Give simulator more time to initialize EOS data
        
        print_colored("\n⚙️  Starting EOS Pathway ETL...", Colors.GREEN)
        etl_process = pm.start_etl()
        
        if not args.skip_frontend:
            time.sleep(3)
            print_colored("\n📊 Starting Frontend Dashboard...", Colors.GREEN)
            frontend_process = pm.start_frontend()
        
        # Display status
        time.sleep(2)
        print_colored("\n" + "=" * 60, Colors.CYAN)
        print_colored("🎊 Neovance AI - NICU Monitoring System Ready!", Colors.BLUE)
        print_colored("✨ Featuring Puopolo/Kaiser EOS Risk Calculator", Colors.GREEN)
        print_colored("\nAccess your application:", Colors.BLUE)
        
        if not args.skip_frontend:
            print_colored("   📊 Frontend Dashboard: http://localhost:3000", Colors.GREEN)
            print_colored("      (may use port 3005 if 3000 is occupied)", Colors.PURPLE)
        
        print_colored("   🔧 Backend API: http://localhost:8000", Colors.GREEN)
        print_colored("   📚 API Documentation: http://localhost:8000/docs", Colors.GREEN)
        print_colored("   🌐 WebSocket Live Data: ws://localhost:8000/ws/live", Colors.GREEN)
        print_colored("\n🔬 EOS Risk Calculator: Validated clinical decision support", Colors.PURPLE)
        print_colored("   Risk categories: ROUTINE_CARE, ENHANCED_MONITORING, HIGH_RISK", Colors.PURPLE)
        print_colored("   Based on maternal risk factors and clinical assessment", Colors.PURPLE)
        print_colored("\n💡 Tips:", Colors.CYAN)
        print_colored("   • Use --demo flag for EOS calculator demonstration", Colors.CYAN)
        print_colored("   • Check database: python -c \"import sqlite3; ...\"", Colors.CYAN)
        print_colored("   • Press Ctrl+C to stop all services", Colors.YELLOW)
        print_colored("=" * 60, Colors.CYAN)
        
        # Keep the script running
        try:
            while True:
                # Check if any critical process has died
                critical_dead = False
                for process_info in pm.processes:
                    if process_info['process'].poll() is not None:
                        if args.verbose:
                            print_colored(f"{process_info['name']} has stopped", Colors.YELLOW)
                        if process_info['name'] in ['Backend API']:
                            critical_dead = True
                
                if critical_dead:
                    print_colored("Critical service stopped, shutting down...", Colors.RED)
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print_colored("\nShutdown requested by user", Colors.YELLOW)
            
    except Exception as e:
        print_colored(f"An error occurred: {e}", Colors.RED)
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    finally:
        pm.cleanup()

if __name__ == "__main__":
    main()