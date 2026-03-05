"""
Quick Setup Script - Run once to verify all dependencies
"""

import sys
import subprocess

def check_import(module_name, package_name=None):
    """Check if a module can be imported"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} NOT INSTALLED")
        return False

def main():
    print("="*60)
    print("EdgeIntelligence 4-Node System - Setup Verification")
    print("="*60)
    
    print("\n1. Checking Python version...")
    print(f"   Python {sys.version}")
    if sys.version_info < (3, 8):
        print("   ⚠️ WARNING: Python 3.8+ recommended")
    else:
        print("   ✓ OK")
    
    print("\n2. Checking required dependencies...")
    dependencies = [
        ("cv2", "OpenCV (cv2)"),
        ("torch", "PyTorch (torch)"),
        ("torchvision", "TorchVision"),
        ("numpy", "NumPy"),
        ("ultralytics", "YOLOv8 (ultralytics)"),
    ]
    
    all_installed = True
    for module, name in dependencies:
        if not check_import(module, name):
            all_installed = False
    
    if not all_installed:
        print("\n⚠️ Missing dependencies! Install with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n3. Checking PyTorch GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   ✓ GPU Available: {torch.cuda.get_device_name(0)}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            print("   ℹ GPU Not available (will use CPU)")
    except Exception as e:
        print(f"   ✗ Error checking GPU: {e}")
    
    print("\n4. Checking configuration file...")
    import os
    if os.path.exists('config.json'):
        print("   ✓ config.json found")
        
        import json
        with open('config.json') as f:
            config = json.load(f)
        
        nodes_found = [n for n in ['NODE_A', 'NODE_B', 'NODE_C', 'NODE_D'] if n in config]
        print(f"   ✓ Configured nodes: {', '.join(nodes_found)}")
        
        if len(nodes_found) < 4:
            print("   ⚠️ Not all 4 nodes configured")
    else:
        print("   ✗ config.json NOT found")
        return False
    
    print("\n5. Checking core files...")
    files_to_check = [
        'core_node_optimized.py',
        'node_a.py', 'node_b.py', 'node_c.py', 'node_d.py',
        'monitor.py',
        'DEPLOYMENT_GUIDE.md',
        'OPTIMIZATION_ANALYSIS.md'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✓ {file}")
        else:
            print(f"   ✗ {file} NOT found")
    
    print("\n6. Checking camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("   ✓ Camera detected and working")
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"   Resolution: {w}x{h}")
            cap.release()
        else:
            print("   ✗ Camera not detected or not accessible")
            print("   Tip: Check camera permissions or try camera_id: 1")
    except Exception as e:
        print(f"   ✗ Camera check failed: {e}")
    
    print("\n7. Network Setup Instructions")
    print("   " + "-"*50)
    print("   1. Find each laptop's IP address:")
    print("      - Windows: ipconfig (look for IPv4 Address)")
    print("      - Linux/Mac: ifconfig")
    print()
    print("   2. Update config.json with your IPs:")
    print("      - NODE_A: Laptop 1 IP")
    print("      - NODE_B: Laptop 2 IP")
    print("      - NODE_C: Laptop 3 IP")
    print("      - NODE_D: Laptop 4 IP")
    print()
    print("   3. Test connectivity from each laptop:")
    print("      python monitor.py")
    print()
    print("   4. If connection fails:")
    print("      - Ensure all laptops on same network")
    print("      - Check firewall (port 5000 must be open)")
    print("      - Check IP addresses are correct")
    
    print("\n" + "="*60)
    print("✓ SETUP VERIFICATION COMPLETE!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Update config.json with your laptop IP addresses")
    print("2. Run: python monitor.py  (check connectivity)")
    print("3. On Laptop 1: python node_a.py")
    print("4. On Laptop 2: python node_b.py")
    print("5. On Laptop 3: python node_c.py")
    print("6. On Laptop 4: python node_d.py")
    print("\nDocumentation:")
    print("- DEPLOYMENT_GUIDE.md: Detailed setup instructions")
    print("- OPTIMIZATION_ANALYSIS.md: Performance details")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
