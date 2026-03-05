"""
Distributed Node Monitoring and Health Check
Monitors all 4 nodes and their network connectivity
"""

import socket
import json
import threading
import time
from datetime import datetime

class NodeMonitor:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.topology = json.load(f)
        
        self.node_status = {}
        self.connection_log = {}
        self.initialize_status()
    
    def initialize_status(self):
        for node in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D']:
            if node in self.topology:
                self.node_status[node] = {
                    'status': 'UNKNOWN',
                    'last_check': None,
                    'response_time': 0,
                    'consecutive_failures': 0
                }
                self.connection_log[node] = []
    
    def check_node_health(self, node_name):
        """Check if a node is reachable"""
        if node_name not in self.topology:
            return False
        
        node_info = self.topology[node_name]
        ip = node_info['ip']
        port = node_info['port']
        
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))
            sock.close()
            
            response_time = (time.time() - start) * 1000  # ms
            
            self.node_status[node_name]['status'] = 'ONLINE'
            self.node_status[node_name]['response_time'] = response_time
            self.node_status[node_name]['consecutive_failures'] = 0
            self.node_status[node_name]['last_check'] = datetime.now().isoformat()
            
            return True
        except:
            self.node_status[node_name]['status'] = 'OFFLINE'
            self.node_status[node_name]['consecutive_failures'] += 1
            self.node_status[node_name]['last_check'] = datetime.now().isoformat()
            return False
    
    def check_network_connectivity(self, source_node, target_node):
        """Check if two nodes can communicate"""
        if source_node not in self.topology or target_node not in self.topology:
            return False
        
        # For now, just check if target is reachable
        # In a real system, you'd establish actual communication
        return self.check_node_health(target_node)
    
    def generate_report(self):
        """Generate system health report"""
        print("\n" + "="*80)
        print(f"DISTRIBUTED NODE HEALTH REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        for node in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D']:
            status = self.node_status.get(node, {})
            print(f"\n{node}:")
            print(f"  Status: {status.get('status', 'N/A')}")
            print(f"  Response Time: {status.get('response_time', 0):.2f}ms")
            print(f"  Last Check: {status.get('last_check', 'Never')}")
            print(f"  Consecutive Failures: {status.get('consecutive_failures', 0)}")
            
            if node in self.topology:
                node_info = self.topology[node]
                print(f"  Address: {node_info['ip']}:{node_info['port']}")
                print(f"  Neighbors: {', '.join(node_info['neighbors'])}")
        
        # Connectivity matrix
        print("\n" + "-"*80)
        print("NETWORK CONNECTIVITY MATRIX:")
        print("-"*80)
        
        for source in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D']:
            if source not in self.topology:
                continue
            
            neighbors = self.topology[source]['neighbors']
            connectivity = []
            
            for neighbor in neighbors:
                is_connected = self.check_network_connectivity(source, neighbor)
                status = "✓" if is_connected else "✗"
                connectivity.append(f"{neighbor}:{status}")
            
            print(f"{source}: {' | '.join(connectivity)}")
        
        print("="*80 + "\n")
    
    def continuous_monitoring(self, interval=10):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (check interval: {interval}s)")
        
        try:
            while True:
                for node in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D']:
                    if node in self.topology:
                        self.check_node_health(node)
                
                self.generate_report()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

def main():
    import sys
    
    monitor = NodeMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        monitor.continuous_monitoring(interval)
    else:
        # Single check
        for node in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D']:
            monitor.check_node_health(node)
        monitor.generate_report()

if __name__ == "__main__":
    main()
