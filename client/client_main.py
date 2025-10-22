"""
client_main.py
--------------
Nhiệm vụ Người 3: Client Logic & I/O
- Kết nối đến server
- Gửi BID requests
- Nhận và hiển thị messages từ server
"""

import socket
import threading
import json
import sys


class AuctionClient:
    """
    Client cho game đấu giá
    """
    
    def __init__(self, host='127.0.0.1', port=9999):
        """
        Khởi tạo client
        
        Args:
            host: IP của server
            port: Port của server
        """
        self.host = host
        self.port = port
        self.socket = None
        self.is_running = False
        self.username = None
    
    def connect(self):
        """
        Kết nối đến server
        
        Returns:
            bool: True nếu kết nối thành công
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_running = True
            print(f"[CLIENT] Đã kết nối đến {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[ERROR] Không thể kết nối: {e}")
            return False
    
    def send_bid(self, value):
        """
        Gửi BID request đến server
        
        Args:
            value: Giá đấu
        """
        try:
            bid_msg = {
                "type": "BID",
                "user": self.username,
                "value": value
            }
            message_json = json.dumps(bid_msg) + "\n"
            self.socket.sendall(message_json.encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Lỗi gửi bid: {e}")
            self.is_running = False
    
    def receive_messages(self):
        """
        Thread nhận messages từ server
        """
        buffer = ""
        
        while self.is_running:
            try:
                data = self.socket.recv(4096)
                
                if not data:
                    print("\n[CLIENT] Server đã ngắt kết nối")
                    self.is_running = False
                    break
                
                buffer += data.decode('utf-8')
                
                # Xử lý các messages (mỗi message kết thúc bằng \n)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            message = json.loads(line)
                            self.handle_message(message)
                        except json.JSONDecodeError as e:
                            print(f"[ERROR] Lỗi parse JSON: {e}")
            
            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Lỗi nhận message: {e}")
                self.is_running = False
                break
    
    def handle_message(self, message):
        """
        Xử lý message từ server
        
        Args:
            message: Dictionary chứa message
        """
        msg_type = message.get("type")
        
        if msg_type == "WELCOME":
            print("\n" + "="*60)
            print(f"🎯 {message.get('message')}")
            print(f"💰 Giá hiện tại: ${message.get('current_price')}")
            print(f"🏆 Đang dẫn đầu: {message.get('current_winner')}")
            print("="*60)
        
        elif msg_type == "NEW_PRICE":
            print(f"\n💰 GIÁ MỚI: {message.get('user')} đặt ${message.get('value')}")
        
        elif msg_type == "ERROR":
            print(f"\n❌ LỖI: {message.get('message')}")
        
        elif msg_type == "WINNER":
            print("\n" + "="*60)
            print(f"🎉 {message.get('message')}")
            print("="*60)
        
        elif msg_type == "WARNING":
            print(f"\n⏰ {message.get('message')}")
        
        elif msg_type == "NO_WINNER":
            print(f"\n{message.get('message')}")
        
        elif msg_type == "SHUTDOWN":
            print(f"\n{message.get('message')}")
            self.is_running = False
        
        else:
            print(f"\n[MESSAGE] {message}")
    
    def run(self):
        """
        Chạy client - main loop
        """
        # Nhập username
        self.username = input("Nhập tên của bạn: ").strip()
        if not self.username:
            self.username = "Anonymous"
        
        print(f"Xin chào {self.username}!")
        
        # Kết nối
        if not self.connect():
            return
        
        # Khởi động thread nhận messages
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        
        # Main loop - nhập bids
        print("\n📝 Hướng dẫn:")
        print("  - Nhập số tiền để đấu giá (VD: 1500)")
        print("  - Nhập 'quit' hoặc 'exit' để thoát")
        print("  - Nhập 'info' để xem thông tin hiện tại\n")
        
        while self.is_running:
            try:
                user_input = input(f"{self.username}> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Đang thoát...")
                    break
                
                if user_input.lower() == 'info':
                    print("Client đang chạy...")
                    continue
                
                # Thử parse số tiền
                try:
                    bid_value = float(user_input)
                    self.send_bid(bid_value)
                except ValueError:
                    print("❌ Vui lòng nhập số tiền hợp lệ")
            
            except KeyboardInterrupt:
                print("\nĐang thoát...")
                break
            except EOFError:
                break
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """
        Đóng kết nối
        """
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
                print("[CLIENT] Đã ngắt kết nối")
            except:
                pass


def main():
    """
    Entry point của client
    """
    print("="*60)
    print("🎯 SIMPLE AUCTION GAME - CLIENT")
    print("="*60)
    
    # Có thể thay đổi host/port nếu cần
    host = input("Nhập IP server (Enter = 127.0.0.1): ").strip()
    if not host:
        host = '127.0.0.1'
    
    port_input = input("Nhập port (Enter = 9999): ").strip()
    port = int(port_input) if port_input else 9999
    
    client = AuctionClient(host=host, port=port)
    client.run()


if __name__ == "__main__":
    main()
