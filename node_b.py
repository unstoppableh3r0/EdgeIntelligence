"""
NODE_B - Run this on Laptop 2
Configure with your actual IP address in config.json
"""
import sys
import os

os.environ['MY_NODE_ID'] = 'NODE_B'

import core_node_optimized as core

core.MY_NODE_ID = "NODE_B"
core.MY_IP = core.TOPOLOGY["NODE_B"]["ip"]
core.MY_PORT = core.TOPOLOGY["NODE_B"]["port"]
core.MY_NEIGHBORS = core.TOPOLOGY["NODE_B"]["neighbors"]

if __name__ == "__main__":
    print(f"Starting NODE_B on {core.MY_IP}:{core.MY_PORT}")
    print(f"Neighbors: {core.MY_NEIGHBORS}")
    print("Press 'q' to quit")
