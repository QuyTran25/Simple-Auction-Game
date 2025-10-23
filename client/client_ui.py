"""
client_ui.py
------------
Nhiệm vụ Người 4: Frontend (UI) - Tkinter GUI
- Giao diện đầy đủ với Status Panel, Action Panel, Log Feed
- Tích hợp với client_main.py socket logic
- Thread-safe GUI updates
- Quick Bid buttons, Connection Dialog, Rules popup
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import socket
import json
import sys


class AuctionClientGUI:
    """
    Tkinter GUI cho Auction Game Client
    """
    
    def __init__(self, root):
        """
        Khởi tạo GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("🎯 Simple Auction Game - Client")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Socket và connection state
        self.socket = None
        self.is_running = False
        self.username = None
        self.host = None
        self.port = None
        
        # Auction state (từ server)
        self.current_price = 0
        self.current_winner = "Chưa có"
        self.connection_status = "Disconnected"
        
        # Colors
        self.color_bg = "#f0f0f0"
        self.color_header = "#2c3e50"
        self.color_status = "#ecf0f1"
        self.color_action = "#ffffff"
        self.color_connected = "#27ae60"
        self.color_disconnected = "#e74c3c"
        self.color_price = "#3498db"
        self.color_button = "#2ecc71"
        
        # Setup GUI
        self.setup_gui()
        
        # Show connection dialog
        self.root.after(100, self.show_connection_dialog)
    
    def setup_gui(self):
        """
        Thiết lập giao diện chính
        """
        # ===== HEADER PANEL =====
        self.setup_header()
        
        # ===== MAIN CONTAINER =====
        main_frame = tk.Frame(self.root, bg=self.color_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side (Status + Action)
        left_frame = tk.Frame(main_frame, bg=self.color_bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.setup_status_panel(left_frame)
        self.setup_action_panel(left_frame)
        
        # Right side (Log Feed)
        right_frame = tk.Frame(main_frame, bg=self.color_bg)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.setup_log_panel(right_frame)
        
        # ===== FOOTER (Rules button) =====
        self.setup_footer()
    
    def setup_header(self):
        """
        Thiết lập Header Panel
        """
        header_frame = tk.Frame(self.root, bg=self.color_header, height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🎯 SIMPLE AUCTION GAME",
            font=("Arial", 18, "bold"),
            bg=self.color_header,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Connection status indicator
        self.status_indicator = tk.Label(
            header_frame,
            text="● Disconnected",
            font=("Arial", 12, "bold"),
            bg=self.color_header,
            fg=self.color_disconnected
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=10)
    
    def setup_status_panel(self, parent):
        """
        Thiết lập Status Panel (Realtime info)
        """
        status_frame = tk.LabelFrame(
            parent,
            text="📊 Trạng Thái Đấu Giá",
            font=("Arial", 12, "bold"),
            bg=self.color_status,
            padx=15,
            pady=15
        )
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current Price
        price_container = tk.Frame(status_frame, bg=self.color_status)
        price_container.pack(fill=tk.X, pady=5)
        
        tk.Label(
            price_container,
            text="💰 Giá Cao Nhất:",
            font=("Arial", 11),
            bg=self.color_status,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.price_label = tk.Label(
            price_container,
            text="$0",
            font=("Arial", 16, "bold"),
            bg=self.color_status,
            fg=self.color_price,
            anchor="e"
        )
        self.price_label.pack(side=tk.RIGHT)
        
        # Current Winner
        winner_container = tk.Frame(status_frame, bg=self.color_status)
        winner_container.pack(fill=tk.X, pady=5)
        
        tk.Label(
            winner_container,
            text="🏆 Người Dẫn Đầu:",
            font=("Arial", 11),
            bg=self.color_status,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.winner_label = tk.Label(
            winner_container,
            text="Chưa có",
            font=("Arial", 12, "bold"),
            bg=self.color_status,
            fg="#e67e22",
            anchor="e"
        )
        self.winner_label.pack(side=tk.RIGHT)
        
        # Timer / Warnings
        timer_container = tk.Frame(status_frame, bg=self.color_status)
        timer_container.pack(fill=tk.X, pady=5)
        
        tk.Label(
            timer_container,
            text="⏰ Thông Báo:",
            font=("Arial", 11),
            bg=self.color_status,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.timer_label = tk.Label(
            timer_container,
            text="Đang chờ...",
            font=("Arial", 11),
            bg=self.color_status,
            fg="#95a5a6",
            anchor="e"
        )
        self.timer_label.pack(side=tk.RIGHT)
    
    def setup_action_panel(self, parent):
        """
        Thiết lập Action Panel (Input & Buttons)
        """
        action_frame = tk.LabelFrame(
            parent,
            text="🎮 Đặt Giá",
            font=("Arial", 12, "bold"),
            bg=self.color_action,
            padx=15,
            pady=15
        )
        action_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Bid Input
        input_container = tk.Frame(action_frame, bg=self.color_action)
        input_container.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            input_container,
            text="Nhập Giá ($):",
            font=("Arial", 11),
            bg=self.color_action
        ).pack(anchor="w", pady=(0, 5))
        
        self.bid_entry = tk.Entry(
            input_container,
            font=("Arial", 14),
            justify="center"
        )
        self.bid_entry.pack(fill=tk.X, ipady=5)
        self.bid_entry.bind("<Return>", lambda e: self.send_bid())
        
        # Main Bid Button
        self.bid_button = tk.Button(
            action_frame,
            text="🚀 Đặt Giá",
            font=("Arial", 12, "bold"),
            bg=self.color_button,
            fg="white",
            command=self.send_bid,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        self.bid_button.pack(fill=tk.X, pady=(0, 15), ipady=8)
        
        # Quick Bid Buttons
        quick_bid_frame = tk.LabelFrame(
            action_frame,
            text="⚡ Đặt Nhanh",
            font=("Arial", 10, "bold"),
            bg=self.color_action,
            padx=10,
            pady=10
        )
        quick_bid_frame.pack(fill=tk.X, pady=(0, 15))
        
        quick_values = [100, 500, 1000]
        for value in quick_values:
            btn = tk.Button(
                quick_bid_frame,
                text=f"+${value}",
                font=("Arial", 10, "bold"),
                bg="#3498db",
                fg="white",
                command=lambda v=value: self.quick_bid(v),
                cursor="hand2",
                relief=tk.RAISED,
                bd=2
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2, ipady=5)
        
        # Error Message Box
        self.error_label = tk.Label(
            action_frame,
            text="",
            font=("Arial", 10),
            bg=self.color_action,
            fg="#e74c3c",
            wraplength=250,
            justify="center"
        )
        self.error_label.pack(fill=tk.X, pady=(5, 0))
    
    def setup_log_panel(self, parent):
        """
        Thiết lập Log Feed Panel (Event history)
        """
        log_frame = tk.LabelFrame(
            parent,
            text="📜 Lịch Sử Sự Kiện",
            font=("Arial", 12, "bold"),
            bg=self.color_action,
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # ScrolledText widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#2c3e50",
            fg="#ecf0f1",
            wrap=tk.WORD,
            state=tk.DISABLED,
            cursor="arrow"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colors
        self.log_text.tag_config("new_price", foreground="#2ecc71", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("error", foreground="#e74c3c", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("winner", foreground="#f1c40f", font=("Consolas", 11, "bold"))
        self.log_text.tag_config("warning", foreground="#e67e22", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("info", foreground="#3498db", font=("Consolas", 10))
    
    def setup_footer(self):
        """
        Thiết lập Footer (Rules button)
        """
        footer_frame = tk.Frame(self.root, bg=self.color_bg, height=40)
        footer_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        rules_button = tk.Button(
            footer_frame,
            text="📖 Luật Chơi",
            font=("Arial", 10),
            bg="#95a5a6",
            fg="white",
            command=self.show_rules,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        rules_button.pack(side=tk.LEFT, padx=5, ipady=3, ipadx=10)
        
        reconnect_button = tk.Button(
            footer_frame,
            text="🔄 Kết Nối Lại",
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            command=self.show_connection_dialog,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        reconnect_button.pack(side=tk.LEFT, padx=5, ipady=3, ipadx=10)
    
    # ========== CONNECTION METHODS ==========
    
    def show_connection_dialog(self):
        """
        Hiển thị dialog để nhập connection info
        """
        if self.is_running:
            response = messagebox.askyesno(
                "Kết Nối Lại",
                "Bạn đang kết nối. Ngắt kết nối hiện tại?"
            )
            if response:
                self.disconnect()
            else:
                return
        
        # Dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Kết Nối Server")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        tk.Label(
            dialog,
            text="🎯 Kết Nối Đến Server",
            font=("Arial", 14, "bold")
        ).pack(pady=15)
        
        # Username
        tk.Label(dialog, text="Tên Của Bạn:", font=("Arial", 10)).pack(anchor="w", padx=30)
        username_entry = tk.Entry(dialog, font=("Arial", 11))
        username_entry.pack(fill=tk.X, padx=30, pady=(0, 10))
        username_entry.insert(0, self.username or "Player")
        
        # Host
        tk.Label(dialog, text="IP Server:", font=("Arial", 10)).pack(anchor="w", padx=30)
        host_entry = tk.Entry(dialog, font=("Arial", 11))
        host_entry.pack(fill=tk.X, padx=30, pady=(0, 10))
        host_entry.insert(0, self.host or "127.0.0.1")
        
        # Port
        tk.Label(dialog, text="Port:", font=("Arial", 10)).pack(anchor="w", padx=30)
        port_entry = tk.Entry(dialog, font=("Arial", 11))
        port_entry.pack(fill=tk.X, padx=30, pady=(0, 15))
        port_entry.insert(0, str(self.port) if self.port else "9999")
        
        # Connect button
        def attempt_connect():
            username = username_entry.get().strip()
            host = host_entry.get().strip()
            port_str = port_entry.get().strip()
            
            if not username or not host or not port_str:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin!")
                return
            
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror("Lỗi", "Port phải là số!")
                return
            
            self.username = username
            self.host = host
            self.port = port
            dialog.destroy()
            self.connect()
        
        connect_btn = tk.Button(
            dialog,
            text="🚀 Kết Nối",
            font=("Arial", 12, "bold"),
            bg=self.color_button,
            fg="white",
            command=attempt_connect,
            cursor="hand2"
        )
        connect_btn.pack(fill=tk.X, padx=30, ipady=5)
        
        username_entry.focus()
        username_entry.bind("<Return>", lambda e: attempt_connect())
        host_entry.bind("<Return>", lambda e: attempt_connect())
        port_entry.bind("<Return>", lambda e: attempt_connect())
    
    def connect(self):
        """
        Kết nối đến server
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_running = True
            
            self.update_connection_status(True)
            self.add_log(f"✅ Đã kết nối đến {self.host}:{self.port}", "info")
            
            # Start receive thread
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
        except Exception as e:
            messagebox.showerror("Lỗi Kết Nối", f"Không thể kết nối:\n{e}")
            self.update_connection_status(False)
    
    def disconnect(self):
        """
        Ngắt kết nối
        """
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.update_connection_status(False)
        self.add_log("❌ Đã ngắt kết nối", "error")
    
    def update_connection_status(self, connected):
        """
        Cập nhật trạng thái kết nối trên UI
        """
        if connected:
            self.connection_status = "Connected"
            self.status_indicator.config(
                text="● Connected",
                fg=self.color_connected
            )
            self.bid_button.config(state=tk.NORMAL)
        else:
            self.connection_status = "Disconnected"
            self.status_indicator.config(
                text="● Disconnected",
                fg=self.color_disconnected
            )
            self.bid_button.config(state=tk.DISABLED)
    
    # ========== RECEIVE MESSAGES ==========
    
    def receive_messages(self):
        """
        Thread nhận messages từ server
        """
        buffer = ""
        
        while self.is_running:
            try:
                data = self.socket.recv(4096)
                
                if not data:
                    self.root.after(0, lambda: self.add_log("❌ Server đã ngắt kết nối", "error"))
                    self.is_running = False
                    self.root.after(0, lambda: self.update_connection_status(False))
                    break
                
                buffer += data.decode('utf-8')
                
                # Process line-delimited JSON messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            message = json.loads(line)
                            self.root.after(0, lambda msg=message: self.handle_message(msg))
                        except json.JSONDecodeError as e:
                            self.root.after(0, lambda: self.add_log(f"❌ JSON Error: {e}", "error"))
            
            except Exception as e:
                if self.is_running:
                    self.root.after(0, lambda: self.add_log(f"❌ Lỗi nhận message: {e}", "error"))
                self.is_running = False
                self.root.after(0, lambda: self.update_connection_status(False))
                break
    
    def handle_message(self, message):
        """
        Xử lý message từ server (chạy trong main thread)
        
        Args:
            message: Dictionary chứa message
        """
        msg_type = message.get("type")
        
        if msg_type == "WELCOME":
            self.current_price = message.get("current_price", 0)
            self.current_winner = message.get("current_winner", "Chưa có")
            self.update_status_panel()
            self.add_log(f"🎉 {message.get('message')}", "info")
            self.add_log(f"💰 Giá hiện tại: ${self.current_price}", "info")
        
        elif msg_type == "NEW_PRICE":
            self.current_price = message.get("value", 0)
            self.current_winner = message.get("user", "Unknown")
            self.update_status_panel()
            self.add_log(
                f"💰 {self.current_winner} đặt ${self.current_price}",
                "new_price"
            )
            self.clear_error()
        
        elif msg_type == "ERROR":
            error_msg = message.get("message", "Unknown error")
            self.show_error(error_msg)
            self.add_log(f"❌ {error_msg}", "error")
        
        elif msg_type == "WINNER":
            winner = message.get("user")
            value = message.get("value")
            msg_text = message.get("message", "")
            self.add_log(f"\n{'='*50}", "winner")
            self.add_log(f"🎉 WINNER: {winner} - ${value}", "winner")
            self.add_log(f"{msg_text}", "winner")
            self.add_log(f"{'='*50}\n", "winner")
            self.timer_label.config(text="Đã kết thúc!", fg="#e74c3c")
            messagebox.showinfo("Kết Thúc", msg_text)
        
        elif msg_type == "WARNING":
            warning_msg = message.get("message", "")
            remaining = message.get("remaining", 0)
            self.add_log(f"⏰ {warning_msg}", "warning")
            self.timer_label.config(text=f"{remaining}s còn lại!", fg="#e67e22")
        
        elif msg_type == "NO_WINNER":
            self.add_log(f"❌ {message.get('message')}", "error")
        
        elif msg_type == "SHUTDOWN":
            self.add_log(f"🛑 {message.get('message')}", "error")
            self.is_running = False
            self.update_connection_status(False)
        
        else:
            self.add_log(f"📩 {message}", "info")
    
    # ========== SEND BID ==========
    
    def send_bid(self):
        """
        Gửi BID request đến server
        """
        if not self.is_running:
            self.show_error("Chưa kết nối đến server!")
            return
        
        bid_value_str = self.bid_entry.get().strip()
        
        if not bid_value_str:
            self.show_error("Vui lòng nhập giá!")
            return
        
        try:
            bid_value = float(bid_value_str)
        except ValueError:
            self.show_error("Giá phải là số!")
            return
        
        if bid_value <= 0:
            self.show_error("Giá phải lớn hơn 0!")
            return
        
        # Send BID message
        bid_msg = {
            "type": "BID",
            "user": self.username,
            "value": bid_value
        }
        
        try:
            message_json = json.dumps(bid_msg) + "\n"
            self.socket.sendall(message_json.encode('utf-8'))
            self.add_log(f"📤 Đã gửi bid: ${bid_value}", "info")
            self.bid_entry.delete(0, tk.END)
        except Exception as e:
            self.show_error(f"Lỗi gửi bid: {e}")
    
    def quick_bid(self, increment):
        """
        Đặt giá nhanh (current_price + increment)
        
        Args:
            increment: Số tiền tăng thêm
        """
        new_bid = self.current_price + increment
        self.bid_entry.delete(0, tk.END)
        self.bid_entry.insert(0, str(new_bid))
        self.send_bid()
    
    # ========== UI UPDATE HELPERS ==========
    
    def update_status_panel(self):
        """
        Cập nhật Status Panel với dữ liệu mới
        """
        self.price_label.config(text=f"${self.current_price}")
        self.winner_label.config(text=self.current_winner)
    
    def add_log(self, text, tag="info"):
        """
        Thêm dòng log vào Log Feed
        
        Args:
            text: Nội dung log
            tag: Tag để tô màu (info, new_price, error, winner, warning)
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_error(self, message):
        """
        Hiển thị error message trong Action Panel
        
        Args:
            message: Nội dung lỗi
        """
        self.error_label.config(text=f"❌ {message}")
    
    def clear_error(self):
        """
        Xóa error message
        """
        self.error_label.config(text="")
    
    def show_rules(self):
        """
        Hiển thị popup Luật Chơi
        """
        rules_text = """
🎯 LUẬT CHƠI GAME ĐẤU GIÁ ĐƠN GIẢN

1. LUẬT VỀ GIÁ (Đấu Giá Tăng Tiến):
   • Giá đặt mới PHẢI lớn hơn Giá Cao Nhất Hiện Tại
   • Không thể đặt giá thấp hơn hoặc bằng giá hiện tại
   • Server sẽ từ chối bid không hợp lệ

2. LUẬT VỀ THỜI GIAN (Timer):
   • Phiên đấu giá có thời gian cố định (120 giây)
   • Khi hết giờ, người đang giữ giá cao nhất thắng
   • Server sẽ cảnh báo khi còn 10s và 5s

3. LUẬT VỀ TỐC ĐỘ (Locking):
   • Nếu 2 người bid cùng lúc, server xử lý tuần tự
   • Người nào gửi nhanh hơn sẽ được xử lý trước
   • Đảm bảo công bằng tuyệt đối

🎮 CÁCH CHƠI:
   • Nhập giá vào ô "Nhập Giá ($)"
   • Hoặc dùng nút "Đặt Nhanh" (+$100, +$500, +$1000)
   • Theo dõi giá và người dẫn đầu ở "Trạng Thái Đấu Giá"
   • Xem lịch sử bid ở "Lịch Sử Sự Kiện"

💡 MẸO:
   • Sử dụng nút Đặt Nhanh để bid nhanh hơn
   • Theo dõi cảnh báo thời gian để bid kịp thời
   • Đặt giá cao hơn một chút để đảm bảo thắng

Chúc may mắn! 🍀
"""
        messagebox.showinfo("📖 Luật Chơi", rules_text)
    
    def on_closing(self):
        """
        Xử lý khi đóng cửa sổ
        """
        if self.is_running:
            if messagebox.askokcancel("Thoát", "Bạn có muốn ngắt kết nối và thoát?"):
                self.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """
    Entry point của GUI client
    """
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
