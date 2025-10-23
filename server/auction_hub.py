"""
auction_hub.py
--------------
Nhiệm vụ Người 2: Quản lý danh sách clients và broadcast messages
- Thêm/xóa clients
- Broadcast NEW_PRICE đến tất cả clients
- Broadcast WINNER khi kết thúc
- Broadcast lịch sử và thống kê
- Gửi messages riêng cho từng client
"""

import threading
import json
import socket
import time


class AuctionHub:
    """
    Quản lý tất cả client connections và broadcast messages
    Thread-safe với Lock để tránh Race Condition khi thêm/xóa clients
    
    Attributes:
        clients: Dictionary mapping socket -> client_id
        lock: threading.Lock để bảo vệ clients dict
        auction_state: Reference đến AuctionState
        message_count: Đếm số messages đã broadcast
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
        self.message_count = 0  # Tracking số messages
        
        print(f"[HUB] ✅ AuctionHub đã khởi tạo")
    
    def add_client(self, client_socket, client_id):
        """
        Thêm client vào danh sách (thread-safe)
        
        Args:
            client_socket: Socket của client
            client_id: ID của client
        """
        with self.lock:  # ═══ CRITICAL SECTION ═══
            self.clients[client_socket] = client_id
            total = len(self.clients)
            print(f"[HUB] ➕ Đã thêm {client_id} | Tổng: {total} client(s)")
    
    def remove_client(self, client_socket):
        """
        Xóa client khỏi danh sách (thread-safe)
        
        Args:
            client_socket: Socket của client cần xóa
        
        Returns:
            str: client_id đã xóa hoặc None
        """
        with self.lock:  # ═══ CRITICAL SECTION ═══
            if client_socket in self.clients:
                client_id = self.clients.pop(client_socket)
                total = len(self.clients)
                print(f"[HUB] ➖ Đã xóa {client_id} | Còn lại: {total} client(s)")
                return client_id
            return None
    
    def get_client_count(self):
        """
        Lấy số lượng clients đang kết nối (thread-safe)
        
        Returns:
            int: Số lượng clients
        """
        with self.lock:
            return len(self.clients)
    
    def get_client_list(self):
        """
        Lấy danh sách tất cả client IDs (thread-safe)
        
        Returns:
            list: Danh sách client IDs
        """
        with self.lock:
            return list(self.clients.values())
    
    def broadcast_message(self, message_dict, exclude_socket=None):
        """
        📡 Gửi message đến TẤT CẢ clients (Broadcast)
        Thread-safe: Sử dụng Lock khi iterate qua clients
        
        Args:
            message_dict: Dictionary sẽ được convert thành JSON
            exclude_socket: Socket cần loại trừ (không gửi cho socket này)
        
        Returns:
            int: Số clients nhận được message thành công
        """
        message_json = json.dumps(message_dict) + "\n"
        message_bytes = message_json.encode('utf-8')
        
        disconnected_clients = []
        success_count = 0
        
        with self.lock:  # ═══ CRITICAL SECTION ═══
            for client_socket, client_id in self.clients.items():
                # Skip nếu là socket cần exclude
                if exclude_socket and client_socket == exclude_socket:
                    continue
                
                try:
                    client_socket.sendall(message_bytes)
                    success_count += 1
                except Exception as e:
                    print(f"[HUB] ❌ Lỗi gửi đến {client_id}: {e}")
                    disconnected_clients.append(client_socket)
        
        # Xóa các clients đã disconnect (không trong lock để tránh deadlock)
        for client_socket in disconnected_clients:
            self.remove_client(client_socket)
        
        self.message_count += 1
        return success_count
    
    def send_to_client(self, client_socket, message_dict):
        """
        📤 Gửi message đến MỘT client cụ thể
        
        Args:
            client_socket: Socket của client
            message_dict: Dictionary sẽ được convert thành JSON
        
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            message_json = json.dumps(message_dict) + "\n"
            client_socket.sendall(message_json.encode('utf-8'))
            return True
        except Exception as e:
            with self.lock:
                client_id = self.clients.get(client_socket, "Unknown")
            print(f"[HUB] ❌ Lỗi gửi đến {client_id}: {e}")
            self.remove_client(client_socket)
            return False
    
    def broadcast_new_price(self, user, value):
        """
        📡 Broadcast thông báo giá mới đến tất cả clients
        
        Args:
            user: Tên người đấu giá
            value: Giá mới
        """
        # Lấy thông tin bổ sung từ auction_state
        stats = self.auction_state.get_statistics()
        next_min_bid = self.auction_state.get_required_next_bid()
        
        message = {
            "type": "NEW_PRICE",
            "user": user,
            "value": value,
            "next_min_bid": next_min_bid,
            "total_bids": stats["total_bids"],
            "timestamp": time.strftime('%H:%M:%S')
        }
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] 💰 NEW_PRICE: {user} = ${value} | Gửi tới {success} client(s)")
    
    def broadcast_winner(self, user, value):
        """
        📡 Broadcast thông báo người thắng cuộc
        
        Args:
            user: Tên người thắng
            value: Giá cuối cùng
        """
        stats = self.auction_state.get_statistics()
        
        message = {
            "type": "WINNER",
            "user": user,
            "value": value,
            "message": f"🎉 {user} đã thắng với giá ${value}!",
            "total_bids": stats["total_bids"],
            "unique_bidders": stats["unique_bidders"],
            "duration_seconds": stats["duration_seconds"],
            "price_increase": stats["price_increase"]
        }
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] 🏆 WINNER: {user} = ${value} | Gửi tới {success} client(s)")
    
    def broadcast_bid_history(self, limit=10):
        """
        📡 Broadcast lịch sử bids gần nhất
        
        Args:
            limit: Số lượng bids gần nhất (mặc định: 10)
        """
        history = self.auction_state.get_bid_history(limit)
        
        message = {
            "type": "BID_HISTORY",
            "history": history,
            "total_bids": len(history)
        }
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] 📜 BID_HISTORY: {len(history)} bids | Gửi tới {success} client(s)")
    
    def broadcast_statistics(self):
        """
        📡 Broadcast thống kê phiên đấu giá
        """
        stats = self.auction_state.get_statistics()
        
        message = {
            "type": "STATISTICS",
            "stats": stats
        }
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] 📊 STATISTICS | Gửi tới {success} client(s)")
    
    def broadcast_shutdown(self):
        """
        📡 Thông báo server đang shutdown
        """
        message = {
            "type": "SHUTDOWN",
            "message": "Server đang shutdown. Cảm ơn bạn đã tham gia!",
            "timestamp": time.strftime('%H:%M:%S')
        }
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] 🛑 SHUTDOWN | Gửi tới {success} client(s)")
    
    def broadcast_warning(self, warning_message, remaining_seconds=None):
        """
        📡 Broadcast cảnh báo chung
        
        Args:
            warning_message: Nội dung cảnh báo
            remaining_seconds: Số giây còn lại (tùy chọn)
        """
        message = {
            "type": "WARNING",
            "message": warning_message,
            "timestamp": time.strftime('%H:%M:%S')
        }
        
        if remaining_seconds is not None:
            message["remaining_seconds"] = remaining_seconds
        
        success = self.broadcast_message(message)
        print(f"[BROADCAST] ⚠️ WARNING: {warning_message} | Gửi tới {success} client(s)")
    
    def close_all_clients(self):
        """
        Đóng tất cả client connections
        """
        with self.lock:  # ═══ CRITICAL SECTION ═══
            total = len(self.clients)
            print(f"[HUB] Đang đóng {total} client connection(s)...")
            
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except Exception as e:
                    pass
            
            self.clients.clear()
            print(f"[HUB] ✅ Đã đóng tất cả client connections")
    
    def get_hub_statistics(self):
        """
        Lấy thống kê về Hub
        
        Returns:
            dict: Thống kê Hub
        """
        with self.lock:
            return {
                "total_clients": len(self.clients),
                "client_ids": list(self.clients.values()),
                "total_messages_broadcast": self.message_count
            }

