import customtkinter as ctk
import cv2
from PIL import Image
import threading
import time

class NerveCenterUI(ctk.CTk):
    def __init__(self, node_id, on_start_sim, on_add_peer):
        super().__init__()
        
        self.title(f"Nerve Center - Node {node_id}")
        self.geometry("1000x800")
        
        # Callbacks
        self.on_start_sim = on_start_sim
        self.on_add_peer = on_add_peer
        
        self._build_ui()
        self.log_messages = []
        
    def _build_ui(self):
        # Top panel: Controls
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(pady=10, padx=10, fill="x")
        
        self.peer_entry = ctk.CTkEntry(self.control_frame, placeholder_text="Peer IP:Port (e.g., 127.0.0.1:5002)")
        self.peer_entry.pack(side="left", padx=10)
        
        self.add_peer_btn = ctk.CTkButton(self.control_frame, text="Add Peer", command=self._handle_add_peer)
        self.add_peer_btn.pack(side="left", padx=10)
        
        self.sim_btn = ctk.CTkButton(self.control_frame, text="Start Stimulus", command=self.on_start_sim)
        self.sim_btn.pack(side="right", padx=10)
        
        # Middle panel: Video & Matches
        self.middle_frame = ctk.CTkFrame(self)
        self.middle_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.video_label = ctk.CTkLabel(self.middle_frame, text="Local Stimulus View")
        self.video_label.pack(side="left", expand=True, fill="both")
        
        self.match_frame = ctk.CTkFrame(self.middle_frame, width=300)
        self.match_frame.pack(side="right", fill="y", padx=10)
        
        self.match_label = ctk.CTkLabel(self.match_frame, text="Re-ID Match Gallery", font=("Arial", 16, "bold"))
        self.match_label.pack(pady=10)
        
        self.match_text = ctk.CTkTextbox(self.match_frame, width=280, height=300)
        self.match_text.pack(pady=10)
        
        # Bottom panel: Network Health & Logs
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(pady=10, padx=10, fill="x")
        
        self.log_text = ctk.CTkTextbox(self.bottom_frame, height=150)
        self.log_text.pack(fill="x", padx=10, pady=10)
        
    def _handle_add_peer(self):
        peer_addr = self.peer_entry.get()
        if peer_addr and ":" in peer_addr:
            ip, port = peer_addr.split(":")
            self.on_add_peer(ip, int(port))
            self.log(f"Added peer target {ip}:{port}")
            self.peer_entry.delete(0, 'end')
            
    def update_frame(self, frame_bgr):
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        # Resize to fit UI
        image.thumbnail((500, 500))
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        self.video_label.configure(image=ctk_image, text="")
        
    def log(self, msg):
        self.log_messages.append(msg)
        if len(self.log_messages) > 100:
            self.log_messages.pop(0)
        
        # Update text box safely
        self.log_text.delete("0.0", "end")
        self.log_text.insert("0.0", "\n".join(self.log_messages))
        self.log_text.see("end")
        
    def log_match(self, global_id, similarity):
        msg = f"Match! ID: {global_id} | Sim: {similarity:.2f}"
        self.match_text.insert("end", msg + "\n")
        self.match_text.see("end")
