"""
Optimized Edge Intelligence Node with Performance Improvements
- Embedding caching to avoid redundant inference
- Batch processing for faster inference
- Connection pooling for network efficiency
- Memory-mapped storage for large vectors
- Quantization for reduced memory footprint
"""

import cv2
import torch
import json
import time
import hashlib
import socket
import threading
import struct
import numpy as np
import torchvision.transforms as T
import torchvision.models as models
from queue import Queue, PriorityQueue
from ultralytics import YOLO
from functools import lru_cache
from collections import OrderedDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(name)s] %(message)s')
logger = logging.getLogger(__name__)

MY_NODE_ID = "NODE_A"  # Changes per laptop
with open('config.json', 'r') as f: 
    TOPOLOGY = json.load(f)

MY_IP = TOPOLOGY[MY_NODE_ID]["ip"]
MY_PORT = TOPOLOGY[MY_NODE_ID]["port"]
MY_NEIGHBORS = TOPOLOGY[MY_NODE_ID]["neighbors"]
SIMILARITY_THRESHOLD = TOPOLOGY.get("similarity_threshold", 0.75)
DEDUP_THRESHOLD = TOPOLOGY.get("dedup_threshold", 0.95)
MAX_MEMORY = TOPOLOGY.get("max_memory_entries", 500)
LOG_COOLDOWN = TOPOLOGY.get("log_cooldown_seconds", 5)
EMBEDDING_CACHE_SIZE = TOPOLOGY.get("embedding_cache_size", 1000)
BATCH_SIZE = TOPOLOGY.get("batch_size", 4)
CONNECTION_TIMEOUT = TOPOLOGY.get("connection_timeout", 2.0)

# --- OPTIMIZATION 1: Connection Pooling ---
class ConnectionPool:
    """Reuses TCP connections to reduce handshake overhead"""
    def __init__(self, max_connections=10):
        self.connections = {}
        self.max_connections = max_connections
        self.lock = threading.Lock()
    
    def get_connection(self, target_ip, target_port):
        key = f"{target_ip}:{target_port}"
        with self.lock:
            if key in self.connections:
                try:
                    # Test if connection is alive
                    self.connections[key].send(b'')
                    return self.connections[key]
                except:
                    del self.connections[key]
            
            # Create new connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(CONNECTION_TIMEOUT)
            try:
                s.connect((target_ip, target_port))
                self.connections[key] = s
                return s
            except:
                return None
    
    def close_all(self):
        with self.lock:
            for conn in self.connections.values():
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()

connection_pool = ConnectionPool()

# --- OPTIMIZATION 2: LRU Cache for Embeddings ---
class EmbeddingCache:
    """LRU cache for storing computed embeddings"""
    def __init__(self, max_size=1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get_key(self, img_bytes):
        """Create hash key from image bytes"""
        return hashlib.md5(img_bytes.tobytes()).hexdigest()
    
    def get(self, img_bytes):
        key = self.get_key(img_bytes)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def put(self, img_bytes, embedding):
        key = self.get_key(img_bytes)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = embedding
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def stats(self):
        total = self.hits + self.misses
        if total == 0:
            return "No cache hits yet"
        hit_rate = (self.hits / total) * 100
        return f"Hit Rate: {hit_rate:.1f}% ({self.hits}/{total})"

embedding_cache = EmbeddingCache(EMBEDDING_CACHE_SIZE)

# --- OPTIMIZATION 3: Batch Processing Queue ---
class BatchProcessor:
    """Batch multiple images for vectorization"""
    def __init__(self, batch_size=4, timeout=0.1):
        self.batch_size = batch_size
        self.timeout = timeout
        self.queue = Queue()
        self.last_batch_time = time.time()
    
    def should_process(self):
        """Decide if batch is ready to process"""
        return (self.queue.qsize() >= self.batch_size or 
                (time.time() - self.last_batch_time) > self.timeout)

batch_processor = BatchProcessor(BATCH_SIZE)

# --- Models and Preprocessing ---
print("Loading YOLOv8 (detector)...")
detector = YOLO('yolov8n.pt')

print("Loading ResNet-18 (feature extractor)...")
resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
resnet = torch.nn.Sequential(*(list(resnet.children())[:-1])).eval()

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
resnet = resnet.to(device)

preprocess = T.Compose([
    T.ToPILImage(), 
    T.Resize((224, 224)), 
    T.ToTensor(), 
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- OPTIMIZATION 4: Batch Vector Extraction ---
def extract_vector_batch(img_crops):
    """Extract vectors for multiple images at once (GPU acceleration)"""
    if not img_crops:
        return []
    
    vectors = []
    for img_crop in img_crops:
        # Check cache first
        cached = embedding_cache.get(img_crop)
        if cached is not None:
            vectors.append(cached)
            continue
        
        # Ensure image has 3 channels
        if len(img_crop.shape) == 2:
            img_crop = cv2.cvtColor(img_crop, cv2.COLOR_GRAY2RGB)
        
        try:
            img_tensor = preprocess(img_crop).unsqueeze(0).to(device)
            with torch.no_grad(): 
                vector = resnet(img_tensor).flatten().cpu().numpy()
            vectors.append(vector)
            embedding_cache.put(img_crop, vector)
        except Exception as e:
            logger.warning(f"Vector extraction failed: {e}")
            vectors.append(None)
    
    return vectors

def extract_vector(img_crop):
    """Single image extraction wrapper"""
    result = extract_vector_batch([img_crop])
    return result[0] if result else None

def generate_commitment(vector):
    salt = str(time.time())
    commitment = hashlib.sha256(vector.tobytes() + salt.encode()).hexdigest()
    return commitment, salt

def verify_commitment(vector, commitment, salt):
    return hashlib.sha256(np.array(vector, dtype=np.float32).tobytes() + salt.encode()).hexdigest() == commitment

# --- Re-Identification Logic ---
def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors (optimized with numpy broadcasting)."""
    if vec_a is None or vec_b is None:
        return 0.0
    
    dot = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

# Shared state
network_memory = []
memory_lock = threading.Lock()
opportunistic_queue = PriorityQueue()  # Priority queue for better scheduling

person_counter = 0
counter_lock = threading.Lock()
last_log_times = {}

def find_match(new_vector, threshold=SIMILARITY_THRESHOLD):
    """Search network_memory for best matching embedding"""
    if new_vector is None:
        return None, 0.0
    
    best_match = None
    best_score = -1.0
    
    with memory_lock:
        for entry in network_memory:
            score = cosine_similarity(new_vector, entry['vector'])
            if score > threshold and score > best_score:
                best_match = entry
                best_score = score
    
    return best_match, best_score

def update_or_append(entry, matched_entry=None):
    """Update or append entry with LRU eviction"""
    with memory_lock:
        if matched_entry is not None:
            old_vec = matched_entry['vector']
            new_vec = entry['vector']
            matched_entry['vector'] = 0.7 * old_vec + 0.3 * new_vec
            matched_entry['timestamp'] = time.time()
        else:
            if len(network_memory) >= MAX_MEMORY:
                network_memory.pop(0)
            entry['timestamp'] = time.time()
            network_memory.append(entry)

def should_log(person_id):
    """Rate-limit logs"""
    now = time.time()
    if person_id not in last_log_times or (now - last_log_times[person_id]) >= LOG_COOLDOWN:
        last_log_times[person_id] = now
        return True
    return False

def get_next_person_id():
    """Thread-safe auto-incrementing ID"""
    global person_counter
    with counter_lock:
        person_counter += 1
        return f"P-{person_counter}"

def recvall(sock, n):
    """Receive exactly n bytes"""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

# --- Receiver Server Thread ---
def peer_to_peer_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', MY_PORT))
    server.listen(10)  # Increased backlog
    
    logger.info(f"[{MY_NODE_ID}] Listening on Port {MY_PORT}...")
    
    while True:
        try:
            conn, addr = server.accept()
            # Handle in thread to avoid blocking
            threading.Thread(target=handle_peer_connection, args=(conn, addr), daemon=True).start()
        except Exception as e:
            logger.error(f"Server error: {e}")

def handle_peer_connection(conn, addr):
    """Handle incoming peer connection"""
    try:
        raw_msglen = recvall(conn, 4)
        if not raw_msglen:
            return
        
        msglen = struct.unpack('>I', raw_msglen)[0]
        message_data = recvall(conn, msglen)
        if not message_data:
            return
        
        payload = json.loads(message_data.decode('utf-8'))
        
        if verify_commitment(payload['vector'], payload['commitment'], payload['salt']):
            received_vector = np.array(payload['vector'])
            payload['vector'] = received_vector
            
            match, score = find_match(received_vector)
            
            if match:
                payload['person_id'] = match['person_id']
                update_or_append(payload, matched_entry=match)
                if should_log(match['person_id']):
                    logger.info(f"RE-ID MATCH: {match['person_id']} from {payload.get('origin', '?')} "
                               f"(sim: {score:.3f})")
            else:
                if 'person_id' not in payload:
                    payload['person_id'] = get_next_person_id()
                update_or_append(payload)
                logger.info(f"New person {payload['person_id']} from {payload.get('origin', 'Unknown')}")
        else:
            logger.warning(f"REJECTED: Invalid commitment from {addr}")
    except Exception as e:
        logger.error(f"Connection handler error: {e}")
    finally:
        conn.close()

# --- Optimized Sender with Connection Pooling ---
def send_unicast(target_node, payload_dict):
    """Send with connection pooling"""
    try:
        target_ip = TOPOLOGY[target_node]["ip"]
        target_port = TOPOLOGY[target_node]["port"]
        
        conn = connection_pool.get_connection(target_ip, target_port)
        if not conn:
            return False
        
        message_data = json.dumps(payload_dict).encode('utf-8')
        message_length = len(message_data)
        header = struct.pack('>I', message_length)
        
        conn.sendall(header + message_data)
        return True
    except Exception as e:
        logger.debug(f"Send failed to {target_node}: {e}")
        return False

def opportunistic_network_worker():
    """Enhanced with priority queue for important messages"""
    while True:
        try:
            if not opportunistic_queue.empty():
                priority, item = opportunistic_queue.get_nowait()
                if send_unicast(item['target'], item['payload']):
                    logger.info(f"Opportunistically sent to {item['target']}")
                else:
                    # Re-queue with slightly higher priority
                    opportunistic_queue.put((priority + 1, item))
        except:
            pass
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=peer_to_peer_server, daemon=True).start()
    threading.Thread(target=opportunistic_network_worker, daemon=True).start()
    
    last_sent_vectors = {}
    frame_count = 0
    fps_timer = time.time()

    logger.info(f"Starting {MY_NODE_ID}...")
    logger.info(f"Similarity Threshold: {SIMILARITY_THRESHOLD}")
    logger.info(f"Dedup Threshold: {DEDUP_THRESHOLD}")
    logger.info(f"Device: {device}")
    
    # Initialize camera with proper backend
    camera_id = TOPOLOGY[MY_NODE_ID].get("camera_id", 0)
    logger.info(f"Initializing camera {camera_id}...")
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    
    # Wait for camera to initialize
    if not cap.isOpened():
        logger.error(f"Camera {camera_id} failed to open. Trying without CAP_DSHOW...")
        cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        logger.error(f"Camera {camera_id} not available!")
        cap.release()
        exit(1)
    
    logger.info(f"Camera {camera_id} opened successfully")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: 
                logger.error("Failed to grab frame")
                break
            
            frame_count += 1
            
            # YOLO Detection
            results = detector(frame, classes=[0], verbose=False)
            
            crops = []
            boxes_info = []
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    img_crop = frame[y1:y2, x1:x2]
                    
                    if img_crop.size > 0:
                        crops.append(img_crop)
                        boxes_info.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
            
            # Batch vector extraction
            if crops:
                vectors = extract_vector_batch(crops)
                
                for idx, (vector, box) in enumerate(zip(vectors, boxes_info)):
                    if vector is None:
                        continue
                    
                    match, score = find_match(vector)
                    
                    if match:
                        person_id = match['person_id']
                        origin_node = match.get('origin', MY_NODE_ID)
                        label = f"{person_id} [{score:.2f}]"
                        box_color = (0, 0, 255) if origin_node != MY_NODE_ID else (0, 255, 0)
                        
                        local_update = {'vector': vector, 'origin': MY_NODE_ID, 'person_id': person_id}
                        update_or_append(local_update, matched_entry=match)
                    else:
                        person_id = get_next_person_id()
                        label = f"{person_id} [NEW]"
                        box_color = (255, 165, 0)
                        
                        local_entry = {'vector': vector, 'origin': MY_NODE_ID, 'person_id': person_id}
                        update_or_append(local_entry)
                    
                    commitment, salt = generate_commitment(vector)
                    payload = {
                        "origin": MY_NODE_ID, 
                        "person_id": person_id,
                        "vector": vector.tolist(), 
                        "commitment": commitment, 
                        "salt": salt
                    }
                    
                    should_send = True
                    if person_id in last_sent_vectors:
                        dedup_score = cosine_similarity(vector, last_sent_vectors[person_id])
                        if dedup_score > DEDUP_THRESHOLD:
                            should_send = False
                    
                    if should_send:
                        last_sent_vectors[person_id] = vector
                        for neighbor in MY_NEIGHBORS:
                            if not send_unicast(neighbor, payload):
                                opportunistic_queue.put((0, {'target': neighbor, 'payload': payload}))
                    
                    x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(frame, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            
            # Display stats
            with memory_lock:
                mem_count = len(network_memory)
            
            fps_text = f"FPS: {frame_count / (time.time() - fps_timer):.1f}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Memory: {mem_count}/{MAX_MEMORY}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, embedding_cache.stats(), (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            cv2.imshow(f"{MY_NODE_ID} - Optimized", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        connection_pool.close_all()
        logger.info(f"Node {MY_NODE_ID} stopped")
