"""
auction_logic.py
----------------
Nhiệm vụ Người 2: Quản lý trạng thái đấu giá và đồng bộ hóa
- Lưu giá cao nhất và người đấu giá
- Sử dụng Lock để tránh race condition
- Validate bids
- Lưu lịch sử bids
- Thống kê phiên đấu giá
"""

import threading
import time
from datetime import datetime


class AuctionState:
    """
    Quản lý trạng thái của phiên đấu giá
    Thread-safe với Lock để tránh Race Condition
    
    Attributes:
        current_price: Giá cao nhất hiện tại
        current_winner: Người đang dẫn đầu
        starting_price: Giá khởi điểm
        is_active: Trạng thái phiên đấu giá
        bid_history: Lịch sử các bids
        lock: threading.Lock để bảo vệ shared state
    """
    
    def __init__(self, starting_price=1000, min_increment=50):
        """
        Khởi tạo trạng thái đấu giá
        
        Args:
            starting_price: Giá khởi điểm (mặc định: $1000)
            min_increment: Mức tăng tối thiểu cho mỗi bid (mặc định: $50)
        """
        # Biến trạng thái chính (CRITICAL - cần Lock)
        self.current_price = starting_price
        self.current_winner = None
        self.starting_price = starting_price
        self.min_increment = min_increment
        self.is_active = True
        
        # Lịch sử và thống kê
        self.bid_history = []  # List của dict: {user, value, timestamp}
        self.total_bids = 0
        self.unique_bidders = set()
        self.start_time = datetime.now()
        self.end_time = None
        
        # Lock để bảo vệ tất cả shared state
        self.lock = threading.Lock()  # ⚠️ CRITICAL: Thread Synchronization
        
        print(f"[AUCTION] ═══════════════════════════════════════════")
        print(f"[AUCTION] Khởi tạo phiên đấu giá mới")
        print(f"[AUCTION] Giá khởi điểm: ${starting_price}")
        print(f"[AUCTION] Mức tăng tối thiểu: ${min_increment}")
        print(f"[AUCTION] Thời gian bắt đầu: {self.start_time.strftime('%H:%M:%S')}")
        print(f"[AUCTION] ═══════════════════════════════════════════")
    
    def place_bid(self, user, value):
        """
        Xử lý một bid từ user
        ⚠️ CRITICAL SECTION - Sử dụng Lock để tránh Race Condition
        
        Flow:
        1. Acquire Lock (chỉ 1 thread được vào)
        2. Validate bid (giá phải hợp lệ)
        3. Cập nhật state nếu hợp lệ
        4. Lưu vào bid history
        5. Release Lock
        
        Args:
            user: Tên người đấu giá
            value: Giá đấu
        
        Returns:
            tuple: (success: bool, message: str)
        """
        with self.lock:  # ═══ BẮT ĐẦU CRITICAL SECTION ═══
            
            # Validate 1: Kiểm tra phiên đấu giá còn hoạt động không
            if not self.is_active:
                return False, "❌ Phiên đấu giá đã kết thúc"
            
            # Validate 2: Giá phải là số dương
            if value <= 0:
                return False, "❌ Giá phải là số dương"
            
            # Validate 3: Giá phải lớn hơn giá hiện tại
            if value <= self.current_price:
                return False, f"❌ Giá phải lớn hơn ${self.current_price}"
            
            # Validate 4: Giá phải đạt mức tăng tối thiểu
            required_price = self.current_price + self.min_increment
            if value < required_price:
                return False, f"❌ Giá tối thiểu phải là ${required_price} (tăng ${self.min_increment})"
            
            # ✅ BID HỢP LỆ - Cập nhật state
            old_price = self.current_price
            old_winner = self.current_winner
            
            self.current_price = value
            self.current_winner = user
            self.total_bids += 1
            self.unique_bidders.add(user)
            
            # Lưu vào lịch sử
            bid_record = {
                "user": user,
                "value": value,
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "bid_number": self.total_bids
            }
            self.bid_history.append(bid_record)
            
            # Log chi tiết
            print(f"[AUCTION] ✅ BID #{self.total_bids} THÀNH CÔNG")
            print(f"[AUCTION]    User: {user}")
            print(f"[AUCTION]    Giá: ${old_price} → ${value} (+${value - old_price})")
            if old_winner:
                print(f"[AUCTION]    {old_winner} đã bị vượt qua!")
            
            return True, f"✅ Bid thành công! {user} đang dẫn đầu với ${value}"
        
        # ═══ KẾT THÚC CRITICAL SECTION ═══
    
    
    def get_current_price(self):
        """
        Lấy giá hiện tại (thread-safe)
        
        Returns:
            float: Giá hiện tại
        """
        with self.lock:
            return self.current_price
    
    def get_current_winner(self):
        """
        Lấy người đang dẫn đầu (thread-safe)
        
        Returns:
            str: Tên người dẫn đầu hoặc None
        """
        with self.lock:
            return self.current_winner
    
    def get_winner_info(self):
        """
        Lấy thông tin người thắng cuộc (thread-safe)
        
        Returns:
            tuple: (winner_name, final_price)
        """
        with self.lock:
            return self.current_winner, self.current_price
    
    def get_bid_history(self, limit=10):
        """
        Lấy lịch sử bids (thread-safe)
        
        Args:
            limit: Số lượng bids gần nhất cần lấy (mặc định: 10)
        
        Returns:
            list: Danh sách các bid records
        """
        with self.lock:
            return self.bid_history[-limit:] if limit else self.bid_history.copy()
    
    def get_statistics(self):
        """
        Lấy thống kê phiên đấu giá (thread-safe)
        
        Returns:
            dict: Thống kê chi tiết
        """
        with self.lock:
            duration = None
            if self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
            elif self.is_active:
                duration = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "total_bids": self.total_bids,
                "unique_bidders": len(self.unique_bidders),
                "current_price": self.current_price,
                "starting_price": self.starting_price,
                "price_increase": self.current_price - self.starting_price,
                "current_winner": self.current_winner,
                "is_active": self.is_active,
                "duration_seconds": duration,
                "avg_bid_interval": duration / self.total_bids if self.total_bids > 0 else 0
            }
    
    def end_auction(self):
        """
        Kết thúc phiên đấu giá (thread-safe)
        """
        with self.lock:
            self.is_active = False
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            print(f"[AUCTION] ═══════════════════════════════════════════")
            print(f"[AUCTION] PHIÊN ĐẤU GIÁ ĐÃ KẾT THÚC")
            print(f"[AUCTION] Thời gian: {duration:.0f} giây")
            print(f"[AUCTION] Tổng số bids: {self.total_bids}")
            print(f"[AUCTION] Số người tham gia: {len(self.unique_bidders)}")
            print(f"[AUCTION] Giá bắt đầu: ${self.starting_price}")
            print(f"[AUCTION] Giá cuối cùng: ${self.current_price}")
            print(f"[AUCTION] Tăng: ${self.current_price - self.starting_price}")
            print(f"[AUCTION] Người thắng: {self.current_winner or '❌ Không có'}")
            print(f"[AUCTION] ═══════════════════════════════════════════")
    
    def is_auction_active(self):
        """
        Kiểm tra phiên đấu giá còn hoạt động không
        
        Returns:
            bool: True nếu còn hoạt động
        """
        with self.lock:
            return self.is_active
    
    def get_required_next_bid(self):
        """
        Tính giá tối thiểu cho bid tiếp theo (thread-safe)
        
        Returns:
            float: Giá tối thiểu
        """
        with self.lock:
            return self.current_price + self.min_increment
    
    def reset_auction(self, new_starting_price=None):
        """
        Reset phiên đấu giá (để chơi lại)
        ⚠️ Chỉ dùng khi muốn tạo phiên mới
        
        Args:
            new_starting_price: Giá khởi điểm mới (None = giữ nguyên)
        """
        with self.lock:
            if new_starting_price:
                self.starting_price = new_starting_price
            
            self.current_price = self.starting_price
            self.current_winner = None
            self.is_active = True
            self.bid_history = []
            self.total_bids = 0
            self.unique_bidders = set()
            self.start_time = datetime.now()
            self.end_time = None
            
            print(f"[AUCTION] ♻️ Đã reset phiên đấu giá - Giá khởi điểm: ${self.starting_price}")

