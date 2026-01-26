#!/usr/bin/env python3
"""
Neovance-AI: Complete Real-time ML + HIL Orchestration
Launches the complete Human-in-the-Loop sepsis prediction system

This script orchestrates all components:
1. ML Prediction Service (FastAPI)
2. Real-time Data Processing (Pathway)  
3. HIL Feedback Loop
4. Frontend Alerts
"""

import subprocess
import time
import signal
import sys
import os
from datetime import datetime
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeovanceMLHILOrchestrator:
    """Orchestrates the complete ML + HIL system"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
    
    def start_ml_prediction_service(self):
        """Start the ML prediction FastAPI service"""
        logger.info("🤖 Starting ML Prediction Service...")
        
        try:
            process = subprocess.Popen(
                ['python', 'sepsis_prediction_service.py'],
                cwd='.',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['ml_service'] = process
            
            # Wait for service to start
            time.sleep(3)
            
            # Test if service is running
            try:
                response = requests.get('http://localhost:8001/health', timeout=5)
                if response.status_code == 200:
                    logger.info("✅ ML Prediction Service started successfully")
                    return True
                else:
                    logger.error(f"❌ ML Service unhealthy: {response.status_code}")
                    return False
            except:
                logger.error("❌ ML Service not responding")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start ML service: {e}")
            return False
    
    def start_pathway_orchestrator(self):
        """Start the Pathway real-time orchestrator"""
        logger.info("🔄 Starting Real-time ML Orchestrator...")
        
        try:
            process = subprocess.Popen(
                ['python', 'realtime_ml_orchestrator.py'],
                cwd='.',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['pathway_orchestrator'] = process
            logger.info("✅ Real-time ML Orchestrator started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Pathway orchestrator: {e}")
            return False
    
    def start_existing_backend(self):
        """Start the existing Neovance backend"""
        logger.info("🏥 Starting Neovance Backend...")
        
        try:
            process = subprocess.Popen(
                ['python', '-m', 'uvicorn', 'main:app', '--reload', '--port', '8000', '--host', '0.0.0.0'],
                cwd='backend',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['neovance_backend'] = process
            time.sleep(2)
            logger.info("✅ Neovance Backend started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Neovance backend: {e}")
            return False
    
    def start_data_simulator(self):
        """Start the EOS data simulator"""
        logger.info("📊 Starting EOS Data Simulator...")
        
        try:
            process = subprocess.Popen(
                ['python', 'pathway_eos_simulator.py'],
                cwd='backend',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['data_simulator'] = process
            logger.info("✅ EOS Data Simulator started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start data simulator: {e}")
            return False
    
    def check_prerequisites(self):
        """Check if all prerequisites are available"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if trained model exists
        if not os.path.exists('trained_models/sepsis_random_forest.pkl'):
            logger.error("❌ Trained model not found")
            logger.info("💡 Run: python train_sepsis_model.py")
            return False
        
        # Check if feature info exists
        if not os.path.exists('trained_models/feature_columns.pkl'):
            logger.error("❌ Feature columns not found")
            logger.info("💡 Run: python train_sepsis_model.py")
            return False
        
        # Check if data directory exists
        if not os.path.exists('data'):
            os.makedirs('data', exist_ok=True)
            logger.info("📁 Created data directory")
        
        logger.info("✅ Prerequisites check passed")
        return True
    
    def start_all_services(self):
        """Start all services in the correct order"""
        logger.info("🚀 STARTING NEOVANCE-AI ML + HIL SYSTEM")
        logger.info("="*60)
        
        if not self.check_prerequisites():
            return False
        
        # Start services in dependency order
        services = [
            ('ML Prediction Service', self.start_ml_prediction_service),
            ('Neovance Backend', self.start_existing_backend),
            ('Data Simulator', self.start_data_simulator),
            ('Real-time ML Orchestrator', self.start_pathway_orchestrator)
        ]
        
        for service_name, start_func in services:
            logger.info(f"\\nStarting {service_name}...")
            success = start_func()
            
            if not success:
                logger.error(f"❌ Failed to start {service_name}")
                self.stop_all_services()
                return False
            
            time.sleep(1)  # Brief pause between services
        
        self.running = True
        logger.info("\\n✅ ALL SERVICES STARTED SUCCESSFULLY!")
        self.print_service_status()
        
        return True
    
    def print_service_status(self):
        """Print the status of all services"""
        logger.info("\\n📋 SERVICE STATUS:")
        logger.info("="*50)
        logger.info("🤖 ML Prediction API: http://localhost:8001")
        logger.info("   • Health: http://localhost:8001/health")
        logger.info("   • Docs: http://localhost:8001/docs")
        logger.info("🏥 Neovance Backend: http://localhost:8000")
        logger.info("   • API: http://localhost:8000/docs")
        logger.info("📊 Data Simulator: Generating live EOS data")
        logger.info("🔄 ML Orchestrator: Monitoring critical thresholds")
        
        logger.info("\\n🎯 WORKFLOW ACTIVE:")
        logger.info("Live Data → Critical Threshold → ML Prediction → Alert → Doctor Action → HIL Log")
    
    def monitor_services(self):
        """Monitor running services"""
        logger.info("\\n👁️ Monitoring services (Press Ctrl+C to stop)...")
        
        try:
            while self.running:
                time.sleep(10)
                
                # Check if processes are still running
                failed_services = []
                for service_name, process in self.processes.items():
                    if process.poll() is not None:  # Process has terminated
                        failed_services.append(service_name)
                
                if failed_services:
                    logger.error(f"❌ Services failed: {failed_services}")
                    break
                
                # Log periodic status
                current_time = datetime.now().strftime("%H:%M:%S")
                active_count = len([p for p in self.processes.values() if p.poll() is None])
                logger.info(f"[{current_time}] {active_count}/{len(self.processes)} services running")
                
        except KeyboardInterrupt:
            logger.info("\\n⏹️ Shutdown requested by user")
            self.running = False
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("\\n🛑 Stopping all services...")
        
        for service_name, process in self.processes.items():
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping {service_name}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {service_name}...")
                        process.kill()
                        process.wait()
                        
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")
        
        self.processes.clear()
        self.running = False
        logger.info("✅ All services stopped")
    
    def run_interactive_mode(self):
        """Run in interactive mode with options"""
        while True:
            print("\\n" + "="*60)
            print("🎛️ NEOVANCE-AI ML + HIL CONTROL PANEL")
            print("="*60)
            print("1. Start complete ML + HIL system")
            print("2. Test HIL workflow")
            print("3. View HIL analytics")
            print("4. Retrain model with HIL data")
            print("5. Stop all services")
            print("6. Exit")
            
            try:
                choice = input("\\nSelect option (1-6): ").strip()
                
                if choice == "1":
                    if self.start_all_services():
                        self.monitor_services()
                
                elif choice == "2":
                    print("\\n🧪 Running HIL Workflow Test...")
                    subprocess.run(['python', 'test_complete_hil_workflow.py'])
                
                elif choice == "3":
                    print("\\n📊 HIL Analytics...")
                    subprocess.run(['python', 'hil_outcome_logger.py'])
                
                elif choice == "4":
                    print("\\n🔄 Model Retraining...")
                    subprocess.run(['python', 'hil_outcome_logger.py'])
                
                elif choice == "5":
                    self.stop_all_services()
                
                elif choice == "6":
                    self.stop_all_services()
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid option")
                    
            except KeyboardInterrupt:
                print("\\n⏹️ Interrupted")
                self.stop_all_services()
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\\n🛑 Shutdown signal received")
    sys.exit(0)


def main():
    """Main orchestration function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("="*80)
    print("🏥 NEOVANCE-AI: REAL-TIME ML + HUMAN-IN-THE-LOOP SYSTEM")
    print("="*80)
    print("Complete sepsis prediction with continuous learning workflow")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    orchestrator = NeovanceMLHILOrchestrator()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--auto':
            # Auto-start mode
            logger.info("🤖 Auto-start mode")
            if orchestrator.start_all_services():
                orchestrator.monitor_services()
        else:
            # Interactive mode
            orchestrator.run_interactive_mode()
    
    except Exception as e:
        logger.error(f"❌ System error: {e}")
    
    finally:
        orchestrator.stop_all_services()


if __name__ == "__main__":
    main()