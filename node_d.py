"""
NODE_D - Run this on Laptop 4
Configure with your actual IP address in config.json
"""
import sys
import os

os.environ['MY_NODE_ID'] = 'NODE_D'

import core_node_optimized as core

core.MY_NODE_ID = "NODE_D"
core.MY_IP = core.TOPOLOGY["NODE_D"]["ip"]
core.MY_PORT = core.TOPOLOGY["NODE_D"]["port"]
core.MY_NEIGHBORS = core.TOPOLOGY["NODE_D"]["neighbors"]

if __name__ == "__main__":
    print(f"Starting NODE_D on {core.MY_IP}:{core.MY_PORT}")
    print(f"Neighbors: {core.MY_NEIGHBORS}")
    print("Press 'q' to quit")
