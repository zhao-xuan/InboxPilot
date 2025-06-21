#!/usr/bin/env python3
"""
ChromaDB Server Setup - Two Server Instances
This script sets up and manages two ChromaDB server instances running on different ports.
"""

import subprocess
import time
import signal
import sys
import os
import logging
import requests
from typing import List, Dict, Any
import threading
from chromadb_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBServerManager:
    """Manages two ChromaDB server instances"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG
        self.processes: List[subprocess.Popen] = []
        self.server_info = {}
        
        # Ensure directories exist
        self.config.create_directories()
    
    def start_server(self, instance_name: str) -> subprocess.Popen:
        """Start a single ChromaDB server instance"""
        config = self.config.get_instance_config(instance_name)
        
        # ChromaDB server command
        cmd = [
            "chroma",
            "run",
            "--host", config.host,
            "--port", str(config.port),
            "--path", config.persist_directory,
            "--log-config", "chromadb/log_config.yml",
        ]
        
        logger.info(f"Starting {instance_name} server on {config.host}:{config.port}")
        logger.info(f"Data directory: {config.persist_directory}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            # Start the server process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Store server info
            self.server_info[instance_name] = {
                "process": process,
                "host": config.host,
                "port": config.port,
                "url": f"http://{config.host}:{config.port}",
                "config": config
            }
            
            self.processes.append(process)
            logger.info(f"✅ {instance_name.capitalize()} server started (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start {instance_name} server: {e}")
            raise
    
    def wait_for_server(self, instance_name: str, timeout: int = 30) -> bool:
        """Wait for a server to be ready"""
        if instance_name not in self.server_info:
            logger.error(f"Server {instance_name} not started")
            return False
        
        server = self.server_info[instance_name]
        url = f"{server['url']}/api/v1/heartbeat"
        
        logger.info(f"Waiting for {instance_name} server to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ {instance_name.capitalize()} server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        logger.error(f"❌ {instance_name.capitalize()} server failed to start within {timeout} seconds")
        return False
    
    def start_both_servers(self):
        """Start both ChromaDB server instances"""
        logger.info("🚀 Starting ChromaDB server instances...")
        
        try:
            # Start Outlook Email server
            self.start_server("outlookEmail")
            
            # Start Teams Chat server
            self.start_server("teamsChat")
            
            # Wait for both servers to be ready
            outlook_ready = self.wait_for_server("outlookEmail")
            teams_ready = self.wait_for_server("teamsChat")
            
            if outlook_ready and teams_ready:
                logger.info("✅ Both ChromaDB servers are running!")
                self.print_server_info()
                return True
            else:
                logger.error("❌ One or more servers failed to start")
                self.stop_all_servers()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start servers: {e}")
            self.stop_all_servers()
            raise
    
    def print_server_info(self):
        """Print information about running servers"""
        print("\n" + "="*60)
        print("📊 ChromaDB Server Information")
        print("="*60)
        
        for name, server in self.server_info.items():
            print(f"\n{name.upper()} Server:")
            print(f"  URL: {server['url']}")
            print(f"  PID: {server['process'].pid}")
            print(f"  Data Directory: {server['config'].persist_directory}")
            print(f"  Collection: {server['config'].collection_name}")
            print(f"  Status: {'🟢 Running' if server['process'].poll() is None else '🔴 Stopped'}")
        
        print(f"\n🔗 API Endpoints:")
        for name, server in self.server_info.items():
            print(f"  {name.capitalize()} API: {server['url']}/docs")
    
    def stop_server(self, instance_name: str):
        """Stop a specific server instance"""
        if instance_name not in self.server_info:
            logger.warning(f"Server {instance_name} not found")
            return
        
        server = self.server_info[instance_name]
        process = server["process"]
        
        if process.poll() is None:  # Process is still running
            logger.info(f"Stopping {instance_name} server (PID: {process.pid})...")
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
                logger.info(f"✅ {instance_name.capitalize()} server stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {instance_name} server...")
                process.kill()
                process.wait()
                logger.info(f"✅ {instance_name.capitalize()} server force stopped")
        else:
            logger.info(f"{instance_name.capitalize()} server already stopped")
    
    def stop_all_servers(self):
        """Stop all running server instances"""
        logger.info("🛑 Stopping all ChromaDB servers...")
        
        for instance_name in self.server_info.keys():
            self.stop_server(instance_name)
        
        # Clear server info
        self.server_info.clear()
        self.processes.clear()
        
        logger.info("✅ All servers stopped")
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers"""
        status = {}
        
        for name, server in self.server_info.items():
            process = server["process"]
            is_running = process.poll() is None
            
            status[name] = {
                "running": is_running,
                "pid": process.pid if is_running else None,
                "url": server["url"],
                "port": server["port"]
            }
        
        return status
    
    def monitor_servers(self):
        """Monitor server health and restart if needed"""
        logger.info("👀 Starting server monitoring...")
        
        while True:
            try:
                for name, server in self.server_info.items():
                    process = server["process"]
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        logger.warning(f"⚠️ {name.capitalize()} server stopped unexpectedly")
                        logger.info(f"🔄 Restarting {name} server...")
                        
                        # Remove from current tracking
                        self.server_info.pop(name)
                        if process in self.processes:
                            self.processes.remove(process)
                        
                        # Restart the server
                        self.start_server(name)
                        self.wait_for_server(name)
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                time.sleep(5)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"\nReceived signal {signum}, shutting down servers...")
        self.stop_all_servers()
        sys.exit(0)


def main():
    """Main function to start and manage ChromaDB servers"""
    manager = ChromaDBServerManager()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # Start both servers
        if manager.start_both_servers():
            
            print("\n🎉 ChromaDB servers are ready!")
            print("\nPress Ctrl+C to stop all servers")
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(target=manager.monitor_servers, daemon=True)
            monitor_thread.start()
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
    finally:
        manager.stop_all_servers()


if __name__ == "__main__":
    main() 