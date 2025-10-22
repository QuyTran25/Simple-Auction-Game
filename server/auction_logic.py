"""
auction_logic.py
----------------
Nhiệm vụ Người 2: Quản lý trạng thái đấu giá và đồng bộ hóa
- Lưu giá cao nhất và người đấu giá
- Sử dụng Lock để tránh race condition
- Validate bids
"""

import threading


class AuctionState:
    """
    Quản lý trạng thái của phiên đấu giá
    Thread-safe với Lock
    """
    
    def __init__(self, starting_price=1000):
        """
        Khởi tạo trạng thái đấu giá
        
        Args:
            starting_price: Giá khởi điểm
        """
        self.current_price = starting_price
        self.current_winner = None
        self.starting_price = starting_price
        self.is_active = True  # Phiên đấu giá đang hoạt động
        self.lock = threading.Lock()  # Lock để bảo vệ shared state
        
        print(f"[AUCTION] Khởi tạo phiên đấu giá - Giá khởi điểm: ${starting_price}")
    
    def place_bid(self, user, value):
        """
        Xử lý một bid từ user
        Thread-safe với Lock
        
        Args:
            user: Tên người đấu giá
            value: Giá đấu
        
        Returns:
            tuple: (success: bool, message: str)
        """
        with self.lock:  # CRITICAL SECTION - Chỉ một thread có thể vào tại một thời điểm
            
            # Kiểm tra phiên đấu giá còn hoạt động không
            if not self.is_active:
                return False, "Phiên đấu giá đã kết thúc"
            
            # Validate: Giá phải lớn hơn giá hiện tại
            if value <= self.current_price:
                return False, f"Giá phải lớn hơn ${self.current_price}"
            
            # Validate: Giá phải là số dương
            if value <= 0:
                return False, "Giá phải là số dương"
            
            # BID HỢP LỆ - Cập nhật state
            self.current_price = value
            self.current_winner = user
            
            return True, f"Bid thành công! {user} đang dẫn đầu với ${value}"
    
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
    
    def end_auction(self):
        """
        Kết thúc phiên đấu giá (thread-safe)
        """
        with self.lock:
            self.is_active = False
            print(f"[AUCTION] Phiên đấu giá đã kết thúc")
            print(f"[AUCTION] Người thắng: {self.current_winner or 'Không có'}")
            print(f"[AUCTION] Giá cuối: ${self.current_price}")
    
    def is_auction_active(self):
        """
        Kiểm tra phiên đấu giá còn hoạt động không
        
        Returns:
            bool: True nếu còn hoạt động
        """
        with self.lock:
            return self.is_active
