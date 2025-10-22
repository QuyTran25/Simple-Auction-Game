"""
auction_hub.py
--------------
Nhiệm vụ Người 2: Quản lý danh sách clients và broadcast messages
- Thêm/xóa clients
- Broadcast NEW_PRICE đến tất cả clients
- Broadcast WINNER khi kết thúc
"""

import threading
import json
import socket


class AuctionHub:
    """
    Quản lý tất cả client connections và broadcast messages
    """
    
    def __init__(self, auction_state):
        """
        Khởi tạo AuctionHub
        
        Args:
            auction_state: Reference đến AuctionState
        """
        self.clients = {}  # Dict: socket -> client_id
        self.lock = threading.Lock()  # Lock để bảo vệ clients dict
        self.auction_state = auction_state
    
    def add_client(self, client_socket, client_id):
        """
        Thêm client vào danh sách
        
        Args:
            client_socket: Socket của client
            client_id: ID của client
        """
        with self.lock:
            self.clients[client_socket] = client_id
            print(f"[HUB] Đã thêm {client_id} (Total: {len(self.clients)})")
    
    def remove_client(self, client_socket):
        """
        Xóa client khỏi danh sách
        
        Args:
            client_socket: Socket của client cần xóa
        """
        with self.lock:
            if client_socket in self.clients:
                client_id = self.clients.pop(client_socket)
                print(f"[HUB] Đã xóa {client_id} (Total: {len(self.clients)})")
    
    def get_client_count(self):
        """
        Lấy số lượng clients đang kết nối
        
        Returns:
            int: Số lượng clients
        """
        with self.lock:
            return len(self.clients)
    
    def broadcast_message(self, message_dict):
        """
        Gửi message đến tất cả clients
        
        Args:
            message_dict: Dictionary sẽ được convert thành JSON
        """
        message_json = json.dumps(message_dict) + "\n"
        message_bytes = message_json.encode('utf-8')
        
        disconnected_clients = []
        
        with self.lock:
            for client_socket, client_id in self.clients.items():
                try:
                    client_socket.sendall(message_bytes)
                except Exception as e:
                    print(f"[HUB] Lỗi gửi đến {client_id}: {e}")
                    disconnected_clients.append(client_socket)
        
        # Xóa các clients đã disconnect
        for client_socket in disconnected_clients:
            self.remove_client(client_socket)
    
    def broadcast_new_price(self, user, value):
        """
        Broadcast thông báo giá mới đến tất cả clients
        
        Args:
            user: Tên người đấu giá
            value: Giá mới
        """
        message = {
            "type": "NEW_PRICE",
            "user": user,
            "value": value
        }
        print(f"[BROADCAST] NEW_PRICE: {user} = ${value}")
        self.broadcast_message(message)
    
    def broadcast_winner(self, user, value):
        """
        Broadcast thông báo người thắng cuộc
        
        Args:
            user: Tên người thắng
            value: Giá cuối cùng
        """
        message = {
            "type": "WINNER",
            "user": user,
            "value": value,
            "message": f"🎉 {user} đã thắng với giá ${value}!"
        }
        print(f"[BROADCAST] WINNER: {user} = ${value}")
        self.broadcast_message(message)
    
    def broadcast_shutdown(self):
        """
        Thông báo server đang shutdown
        """
        message = {
            "type": "SHUTDOWN",
            "message": "Server đang shutdown. Cảm ơn bạn đã tham gia!"
        }
        print("[BROADCAST] SHUTDOWN")
        self.broadcast_message(message)
    
    def close_all_clients(self):
        """
        Đóng tất cả client connections
        """
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
            print("[HUB] Đã đóng tất cả client connections")
