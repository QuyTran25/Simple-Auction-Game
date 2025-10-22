"""
main_server.py
--------------
Nhiệm vụ Người 1: Backend Core (Listener)
- Tạo listener socket
- Accept loop để chấp nhận nhiều clients
- Tạo thread riêng cho mỗi client
- Quản lý lifecycle và cleanup resources
"""

import socket
import threading
import sys
import signal
from auction_hub import AuctionHub
from client_thread import ClientThread
from timer_thread import TimerThread
from auction_logic import AuctionState

# ============= CẤU HÌNH SERVER =============
HOST = '0.0.0.0'  # Lắng nghe trên tất cả network interfaces
PORT = 9999        # Port để clients kết nối
AUCTION_DURATION = 120  # Thời gian đấu giá (giây) - 2 phút

# ============= BIẾN TOÀN CỤC =============
server_socket = None
auction_hub = None
timer_thread = None
auction_state = None
shutdown_flag = threading.Event()


def signal_handler(sig, frame):
    """
    Xử lý tín hiệu Ctrl+C để shutdown server một cách graceful
    """
    print("\n[SERVER] Nhận tín hiệu dừng server (Ctrl+C)...")
    shutdown_server()


def shutdown_server():
    """
    Dừng server một cách an toàn:
    - Đặt flag shutdown
    - Đóng tất cả client connections
    - Dừng timer thread
    - Đóng server socket
    """
    print("[SERVER] Đang shutdown server...")
    shutdown_flag.set()
    
    # Đóng tất cả client connections
    if auction_hub:
        auction_hub.broadcast_shutdown()
        auction_hub.close_all_clients()
    
    # Dừng timer thread
    if timer_thread:
        timer_thread.stop()
        timer_thread.join(timeout=2)
    
    # Đóng server socket
    if server_socket:
        try:
            server_socket.close()
            print("[SERVER] Server socket đã đóng")
        except Exception as e:
            print(f"[SERVER] Lỗi khi đóng socket: {e}")
    
    print("[SERVER] Server đã dừng hoàn toàn")
    sys.exit(0)


def start_server():
    """
    Hàm chính để khởi động server:
    1. Tạo và bind socket
    2. Khởi tạo các components (AuctionState, AuctionHub, Timer)
    3. Accept loop để nhận clients
    4. Tạo thread cho mỗi client
    """
    global server_socket, auction_hub, timer_thread, auction_state
    
    print("=" * 60)
    print("🎯 SIMPLE AUCTION GAME - SERVER")
    print("=" * 60)
    
    # ===== BƯỚC 1: Khởi tạo Auction State =====
    print("[INIT] Khởi tạo Auction State...")
    auction_state = AuctionState(starting_price=1000)
    
    # ===== BƯỚC 2: Khởi tạo Auction Hub =====
    print("[INIT] Khởi tạo Auction Hub...")
    auction_hub = AuctionHub(auction_state)
    
    # ===== BƯỚC 3: Tạo Server Socket =====
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Cho phép reuse address ngay sau khi socket đóng
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)  # Queue tối đa 5 pending connections
        print(f"[SERVER] Đang lắng nghe tại {HOST}:{PORT}")
        print(f"[SERVER] Thời gian đấu giá: {AUCTION_DURATION} giây")
        print("-" * 60)
    except Exception as e:
        print(f"[ERROR] Không thể khởi động server: {e}")
        sys.exit(1)
    
    # ===== BƯỚC 4: Khởi động Timer Thread =====
    print("[TIMER] Khởi động timer thread...")
    timer_thread = TimerThread(
        duration=AUCTION_DURATION,
        auction_hub=auction_hub,
        auction_state=auction_state
    )
    timer_thread.start()
    print(f"[TIMER] Timer đã bắt đầu đếm ngược {AUCTION_DURATION} giây")
    print("-" * 60)
    
    # ===== BƯỚC 5: Accept Loop (Main Server Loop) =====
    client_counter = 0
    active_threads = []  # Danh sách tracking các client threads
    
    print("[SERVER] Sẵn sàng chấp nhận clients...")
    print("[SERVER] Nhấn Ctrl+C để dừng server\n")
    
    try:
        while not shutdown_flag.is_set():
            try:
                # Set timeout để có thể check shutdown_flag định kỳ
                server_socket.settimeout(1.0)
                
                # Chấp nhận kết nối mới
                client_socket, client_address = server_socket.accept()
                
                # Kiểm tra nếu đang shutdown thì không nhận client mới
                if shutdown_flag.is_set():
                    client_socket.close()
                    break
                
                client_counter += 1
                client_id = f"Client-{client_counter}"
                
                print(f"[CONNECT] {client_id} kết nối từ {client_address}")
                
                # Tạo thread mới cho client này
                client_thread = ClientThread(
                    client_socket=client_socket,
                    client_address=client_address,
                    client_id=client_id,
                    auction_hub=auction_hub,
                    auction_state=auction_state
                )
                
                # Đăng ký client vào hub
                auction_hub.add_client(client_socket, client_id)
                
                # Khởi động thread
                client_thread.start()
                active_threads.append(client_thread)
                
                print(f"[SERVER] Tổng số clients đang kết nối: {auction_hub.get_client_count()}")
                
                # Cleanup các threads đã kết thúc
                active_threads = [t for t in active_threads if t.is_alive()]
                
            except socket.timeout:
                # Timeout là bình thường, tiếp tục loop để check shutdown_flag
                continue
            except OSError as e:
                # Socket đã đóng (có thể do shutdown)
                if shutdown_flag.is_set():
                    break
                print(f"[ERROR] Lỗi socket: {e}")
                break
                
    except KeyboardInterrupt:
        # Ctrl+C được bắt ở đây nếu signal handler không hoạt động
        print("\n[SERVER] Nhận KeyboardInterrupt...")
    except Exception as e:
        print(f"[ERROR] Lỗi không mong đợi trong accept loop: {e}")
    finally:
        # Cleanup
        print("\n[SERVER] Đang cleanup...")
        
        # Đợi tất cả client threads kết thúc (timeout 5 giây)
        for thread in active_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        shutdown_server()


def main():
    """
    Entry point của server
    """
    # Đăng ký signal handler để xử lý Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Khởi động server
    start_server()


if __name__ == "__main__":
    main()
