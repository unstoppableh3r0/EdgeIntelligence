"""
NODE_C - Run this on Laptop 3
Configure with your actual IP address in config.json
"""
import sys
import os

os.environ['MY_NODE_ID'] = 'NODE_C'

import core_node_optimized as core

core.MY_NODE_ID = "NODE_C"
core.MY_IP = core.TOPOLOGY["NODE_C"]["ip"]
core.MY_PORT = core.TOPOLOGY["NODE_C"]["port"]
core.MY_NEIGHBORS = core.TOPOLOGY["NODE_C"]["neighbors"]

if __name__ == "__main__":
    print(f"Starting NODE_C on {core.MY_IP}:{core.MY_PORT}")
    print(f"Neighbors: {core.MY_NEIGHBORS}")
    print("Press 'q' to quit")
