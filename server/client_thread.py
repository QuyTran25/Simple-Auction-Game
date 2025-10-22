"""
client_thread.py
----------------
Xử lý mỗi client trong một thread riêng
- Nhận messages từ client
- Parse JSON
- Xử lý BID requests
- Gửi responses
"""

import threading
import socket
import json


class ClientThread(threading.Thread):
    """
    Thread xử lý một client connection
    """
    
    def __init__(self, client_socket, client_address, client_id, auction_hub, auction_state):
        """
        Khởi tạo client thread
        
        Args:
            client_socket: Socket của client
            client_address: Address (IP, port) của client
            client_id: ID duy nhất cho client
            auction_hub: Reference đến AuctionHub để broadcast
            auction_state: Reference đến AuctionState để xử lý bids
        """
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_id = client_id
        self.auction_hub = auction_hub
        self.auction_state = auction_state
        self.is_running = True
        self.daemon = True  # Thread sẽ tự động kết thúc khi main thread kết thúc
    
    def run(self):
        """
        Main loop của thread - nhận và xử lý messages từ client
        """
        print(f"[{self.client_id}] Thread started")
        
        # Gửi welcome message
        self.send_welcome()
        
        try:
            while self.is_running:
                # Nhận data từ client
                data = self.client_socket.recv(4096)
                
                if not data:
                    # Client đã ngắt kết nối
                    print(f"[{self.client_id}] Ngắt kết nối")
                    break
                
                # Parse JSON message
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.handle_message(message)
                except json.JSONDecodeError as e:
                    print(f"[{self.client_id}] Lỗi parse JSON: {e}")
                    self.send_error("Invalid JSON format")
                except Exception as e:
                    print(f"[{self.client_id}] Lỗi xử lý message: {e}")
                    self.send_error(f"Error: {str(e)}")
        
        except Exception as e:
            print(f"[{self.client_id}] Exception: {e}")
        finally:
            self.cleanup()
    
    def send_welcome(self):
        """
        Gửi thông tin chào mừng cho client mới
        """
        current_price = self.auction_state.get_current_price()
        current_winner = self.auction_state.get_current_winner()
        
        welcome_msg = {
            "type": "WELCOME",
            "message": f"Chào mừng {self.client_id}!",
            "current_price": current_price,
            "current_winner": current_winner if current_winner else "Chưa có người đấu giá"
        }
        self.send_message(welcome_msg)
    
    def handle_message(self, message):
        """
        Xử lý message từ client
        
        Args:
            message: Dict chứa message đã parse từ JSON
        """
        msg_type = message.get("type")
        
        if msg_type == "BID":
            # Xử lý bid request
            user = message.get("user", self.client_id)
            value = message.get("value")
            
            if value is None:
                self.send_error("Missing bid value")
                return
            
            try:
                value = float(value)
            except ValueError:
                self.send_error("Bid value must be a number")
                return
            
            # Gọi auction_state để xử lý bid
            success, result_message = self.auction_state.place_bid(user, value)
            
            if success:
                # Bid thành công - broadcast NEW_PRICE
                self.auction_hub.broadcast_new_price(user, value)
                print(f"[{self.client_id}] BID accepted: {user} = ${value}")
            else:
                # Bid thất bại - gửi ERROR
                self.send_error(result_message)
                print(f"[{self.client_id}] BID rejected: {result_message}")
        
        else:
            self.send_error(f"Unknown message type: {msg_type}")
    
    def send_message(self, message_dict):
        """
        Gửi JSON message đến client
        
        Args:
            message_dict: Dictionary sẽ được convert thành JSON
        """
        try:
            message_json = json.dumps(message_dict) + "\n"
            self.client_socket.sendall(message_json.encode('utf-8'))
        except Exception as e:
            print(f"[{self.client_id}] Lỗi gửi message: {e}")
            self.is_running = False
    
    def send_error(self, error_message):
        """
        Gửi ERROR message đến client
        
        Args:
            error_message: Nội dung lỗi
        """
        error_msg = {
            "type": "ERROR",
            "message": error_message
        }
        self.send_message(error_msg)
    
    def cleanup(self):
        """
        Cleanup khi thread kết thúc
        """
        print(f"[{self.client_id}] Cleaning up...")
        
        # Xóa client khỏi hub
        self.auction_hub.remove_client(self.client_socket)
        
        # Đóng socket
        try:
            self.client_socket.close()
        except:
            pass
        
        print(f"[{self.client_id}] Thread terminated")
