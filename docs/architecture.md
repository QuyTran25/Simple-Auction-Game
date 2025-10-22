# Architecture: Simple Auction Game

## Mục tiêu
- Multi Client-Server bằng Python Socket
- Concurrency với multi-threading và Lock để tránh race condition
- Realtime broadcast tới tất cả clients

## Thành phần
- server/main_server.py: tạo listener socket, accept loop
- server/auction_hub.py: quản lý danh sách client sockets, broadcast
- server/client_thread.py: xử lý I/O cho từng client trong thread riêng
- server/auction_logic.py: lưu trạng thái (giá cao nhất, tên) + Lock
- server/timer_thread.py: đếm ngược và phát WINNER khi hết giờ
- client/client_main.py: kết nối server, gửi/nhận JSON
- client/client_ui.py: giao diện Console/Tkinter

## Đồng bộ hoá (Locking)
- Dùng `threading.Lock` để bảo vệ các biến chia sẻ (giá hiện tại, người giữ giá)
- Mọi cập nhật giá phải nằm trong critical section

## Broadcast
- `auction_hub` giữ list sockets còn sống
- Khi có giá mới hợp lệ, phát thông điệp NEW_PRICE tới tất cả

## Timer
- Thread riêng đếm ngược
- Khi timeout: phát WINNER và đóng phiên

## Giao thức JSON (tóm tắt)
- BID: {"type":"BID","user":"An","value":1500}
- NEW_PRICE: {"type":"NEW_PRICE","user":"Binh","value":1600}
- ERROR: {"type":"ERROR","message":"Giá phải lớn hơn 1600"}
- WINNER: {"type":"WINNER","user":"Binh","value":2000}
