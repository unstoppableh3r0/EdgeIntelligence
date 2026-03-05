"""
NODE_A - Run this on Laptop 1 (Main Hub)
Configure with your actual IP address in config.json
"""
import sys
import os

# Override NODE_ID
os.environ['MY_NODE_ID'] = 'NODE_A'

# Import and patch the core module
import core_node_optimized as core

# Override the MY_NODE_ID in the core module
core.MY_NODE_ID = "NODE_A"
core.MY_IP = core.TOPOLOGY["NODE_A"]["ip"]
core.MY_PORT = core.TOPOLOGY["NODE_A"]["port"]
core.MY_NEIGHBORS = core.TOPOLOGY["NODE_A"]["neighbors"]

if __name__ == "__main__":
    print(f"Starting NODE_A on {core.MY_IP}:{core.MY_PORT}")
    print(f"Neighbors: {core.MY_NEIGHBORS}")
    print("Press 'q' to quit")
    
    # Run the main loop from core_node_optimized
    core.main_loop() if hasattr(core, 'main_loop') else exec(open('core_node_optimized.py').read())
