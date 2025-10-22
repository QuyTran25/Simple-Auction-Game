"""
timer_thread.py
---------------
Nhiệm vụ Người 4: Timer Thread
- Đếm ngược thời gian đấu giá
- Khi hết giờ, broadcast WINNER
- Có thể dừng sớm nếu cần
"""

import threading
import time


class TimerThread(threading.Thread):
    """
    Thread đếm ngược thời gian đấu giá
    """
    
    def __init__(self, duration, auction_hub, auction_state):
        """
        Khởi tạo timer thread
        
        Args:
            duration: Thời gian đấu giá (giây)
            auction_hub: Reference đến AuctionHub để broadcast
            auction_state: Reference đến AuctionState để kết thúc phiên
        """
        super().__init__()
        self.duration = duration
        self.auction_hub = auction_hub
        self.auction_state = auction_state
        self.stop_flag = threading.Event()
        self.daemon = True  # Thread sẽ tự động kết thúc khi main thread kết thúc
    
    def run(self):
        """
        Đếm ngược và kết thúc phiên khi hết giờ
        """
        print(f"[TIMER] Bắt đầu đếm ngược {self.duration} giây...")
        
        elapsed = 0
        
        while elapsed < self.duration and not self.stop_flag.is_set():
            time.sleep(1)
            elapsed += 1
            
            # Thông báo mỗi 30 giây
            remaining = self.duration - elapsed
            if remaining > 0 and remaining % 30 == 0:
                print(f"[TIMER] Còn {remaining} giây...")
            
            # Thông báo 10 giây cuối
            if remaining == 10:
                print(f"[TIMER] ⏰ 10 GIÂY CUỐI!")
                self.broadcast_warning(10)
            elif remaining == 5:
                print(f"[TIMER] ⏰ 5 GIÂY CUỐI!")
                self.broadcast_warning(5)
        
        # Hết giờ hoặc bị dừng
        if not self.stop_flag.is_set():
            self.end_auction()
    
    def broadcast_warning(self, seconds):
        """
        Broadcast cảnh báo thời gian còn lại
        
        Args:
            seconds: Số giây còn lại
        """
        message = {
            "type": "WARNING",
            "message": f"⏰ Còn {seconds} giây!",
            "remaining": seconds
        }
        self.auction_hub.broadcast_message(message)
    
    def end_auction(self):
        """
        Kết thúc phiên đấu giá và broadcast WINNER
        """
        print("[TIMER] ⏰ HẾT GIỜ!")
        
        # Kết thúc phiên trong auction_state
        self.auction_state.end_auction()
        
        # Lấy thông tin người thắng
        winner, final_price = self.auction_state.get_winner_info()
        
        if winner:
            # Có người thắng - broadcast WINNER
            self.auction_hub.broadcast_winner(winner, final_price)
        else:
            # Không có người đấu giá
            no_winner_msg = {
                "type": "NO_WINNER",
                "message": "Phiên đấu giá kết thúc - Không có người tham gia"
            }
            self.auction_hub.broadcast_message(no_winner_msg)
            print("[TIMER] Không có người thắng")
    
    def stop(self):
        """
        Dừng timer thread sớm
        """
        print("[TIMER] Đang dừng timer...")
        self.stop_flag.set()
