# Decentralized Cognitive Mesh

Welcome to the **Distributed Multi-Camera Tracking** project using Collaborative Edge Feature Fusion. 

This project flips the standard "Top-Heavy" surveillance architecture (which relies on centralized cloud servers) by implementing a pure **P2P Decentralized Cognitive Mesh**. Intelligence is distributed to the edge. Nodes detect humans, extract 512-dimensional "Feature Ghosts", and share only these mathematical signatures across the network. Raw images are never shared, ensuring a 100% privacy-first tracking environment.

## Key Features

1. **Local Edge Intelligence**:
   - **Detection**: Utilizes `YOLOv8s` for robust, high-speed human detection on local video streams or images.
   - **Feature Extraction**: A headless `ResNet-18` architecture converts padded CNN bounding-box crops into 512-D L2-normalized feature vectors.

2. **Distributed Algorithms**:
   - **Collaborative Verification**: A dynamic running-average fusion logic merges local Re-ID history with incoming intelligence from neighbors, creating high-fidelity "Global Identities."
   - **Opportunistic Store-and-Forward**: If a neighboring node drops off the network, intelligence packets are cached in a thread-safe Queue and automatically flushed upon reconnection, ensuring fault tolerance and zero data loss.
   - **LRU Cache Memory**: To prevent memory exhaustion on edge hardware, tracking data is managed via a Least Recently Used eviction policy.

3. **Zero-Trust Network Integrity**: 
   - Uses `SHA-256` vector commitments. When a node receives a payload, it verifies the embedded hash to ensure no data tampering occurred in transit.

4. **Nerve Center UI**:
   - A `customtkinter` dashboard built for node operation. Visualizes the real-time simulation feed, the "Re-ID Match Gallery", network pulses, and P2P connection health.

## Project Structure

```text
EdgeIntillgence/
│
├── core/                       # Core ML Algorithms
│   ├── feature_extractor.py    # ResNet-18 512-D vector extraction
│   ├── fusion.py               # Running-average mathematical fusion
│   ├── memory.py               # LRU cache tracking memory
│   ├── ml_engine.py            # YOLOv8 object detection
│   └── tracker.py              # Cosine Similarity matching logic
│
├── network/                    # P2P Connectivity
│   ├── message_queue.py        # Thread-safe Store-and-Forward queue
│   ├── p2p_node.py             # TCP socket unicast server with length-prefix framing
│   └── security.py             # SHA-256 hash vector commitments
│
├── ui/                         # Visuals
│   └── dashboard.py            # CustomTkinter Nerve Center UI
│
├── data/                       # Datasets/Simulation feeds
│   ├── stimulus_loader.py      # Trace-driven video/image sequence feeder
│   └── sample_trace.mp4        # Example video to verify tracking
│
├── tests/                      # Automated Verification
│   └── test_p2p.py             # Unit tests for routing and math
│
├── main.py                     # Primary Application Entry Point
└── requirements.txt            # Python Dependencies
```

## Setup & Installation

Ensure you have Python 3.8+ installed.

1. **Clone/Open the directory**.
2. **Create a virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Multi-Node Simulation

You can simulate a multi-camera tracking network locally by running multiple instances of `main.py` on different ports.

### 1. Start Node A
In your first terminal:
```powershell
.\venv\Scripts\activate
$env:PYTHONPATH="."
python main.py --host 127.0.0.1 --port 5001 --source data\sample_trace.mp4
```

### 2. Start Node B
In a second terminal:
```powershell
.\venv\Scripts\activate
$env:PYTHONPATH="."
python main.py --host 127.0.0.1 --port 5002 --source data\sample_trace.mp4
```

### 3. Connect the Mesh
1. On Node A's UI, enter `127.0.0.1:5002` in the input field and click **Add Peer**.
2. On Node B's UI, enter `127.0.0.1:5001` in the input field and click **Add Peer**.
3. *Click **Start Stimulus*** on both UIs to begin running the inference loop.

Watch the UI trace new identities. Watch the logs verify incoming vector hashes from peers. When the same bounding box gets matched against the other node's distributed intelligence over the mesh, you will see a Re-ID hit in the Gallery.

## Running Tests
Run the mathematical verification unit tests using:
```powershell
.\venv\Scripts\activate
$env:PYTHONPATH="."
python tests\test_p2p.py
```
This will automatically verify the queueing capability of the Store-and-Forward system and that the $L_2$ normalizations persist accurately during algebraic vector fusions.
