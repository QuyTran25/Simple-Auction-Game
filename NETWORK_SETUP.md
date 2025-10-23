# 🌐 Hướng Dẫn Chơi Multi-Player Qua Mạng

## 📋 Yêu Cầu
- Tất cả máy phải cài Python 3.x
- Tất cả máy phải có file `client/client_ui.py` (hoặc clone toàn bộ project)
- Chỉ **1 máy** cần chạy server

---

## 🏠 Cách 1: Chơi Qua LAN/WiFi Chung (Khuyến Nghị)

### Bước 1: Xác Định IP Máy Server

**Trên máy sẽ chạy Server**, mở PowerShell và chạy:

```powershell
ipconfig
```

Tìm dòng **IPv4 Address** của **Wi-Fi** hoặc **Ethernet** đang kết nối:
```
IPv4 Address. . . . . . . . . . . : 192.168.5.31
                                     ^^^^^^^^^^^^
                                     Đây là IP của bạn
```

**Ví dụ IP máy Server hiện tại**: `192.168.5.31`

---

### Bước 2: Mở Firewall (Quan Trọng!)

**Trên máy chạy Server**, bạn cần cho phép kết nối vào port 9999.

#### Cách 1: Dùng PowerShell (Administrator)

```powershell
New-NetFirewallRule -DisplayName "Auction Game Server" -Direction Inbound -Protocol TCP -LocalPort 9999 -Action Allow
```

#### Cách 2: Thủ công qua GUI

1. Mở **Windows Defender Firewall** → **Advanced Settings**
2. Click **Inbound Rules** → **New Rule**
3. Chọn **Port** → Next
4. Chọn **TCP**, nhập port `9999` → Next
5. Chọn **Allow the connection** → Next
6. Đặt tên: `Auction Game Server` → Finish

---

### Bước 3: Khởi Động Server

**Trên máy Server**, chạy:

```powershell
cd d:\GiuaKiMang\Simple-Auction-Game
python server/main_server.py
```

Bạn sẽ thấy:
```
[SERVER] Đang lắng nghe tại 0.0.0.0:9999
[SERVER] Sẵn sàng chấp nhận clients...
```

---

### Bước 4: Bạn Bè Kết Nối (Máy Client)

**Trên máy của bạn bè** (phải cùng WiFi):

1. **Clone hoặc copy project**:
   ```powershell
   git clone https://github.com/QuyTran25/Simple-Auction-Game.git
   cd Simple-Auction-Game
   ```

2. **Chạy GUI client**:
   ```powershell
   python client/client_ui.py
   ```

3. **Trong popup "Kết Nối Server", nhập**:
   - **Tên Của Bạn**: `Alice` (hoặc tên bất kỳ)
   - **IP Server**: `192.168.5.31` ← **IP máy chạy Server**
   - **Port**: `9999`

4. Click **🚀 Kết Nối**

---

### Bước 5: Kiểm Tra Kết Nối

Nếu thành công, bạn sẽ thấy trên **terminal Server**:
```
[CONNECT] Client-1 kết nối từ ('192.168.5.XX', YYYY)
[HUB] Đã thêm Client-1 (Total: 1)
```

Trên **GUI Client**, bạn sẽ thấy:
- Status indicator chuyển sang **● Connected** (màu xanh)
- Log feed hiển thị: `✅ Đã kết nối đến 192.168.5.31:9999`

---

## 🌐 Cách 2: Chơi Qua Internet (Ngrok)

Nếu bạn bè **KHÔNG** cùng WiFi, dùng **ngrok** để tạo tunnel:

### Bước 1: Tải và Cài Ngrok

1. Truy cập: https://ngrok.com/download
2. Tải file ngrok cho Windows
3. Giải nén và copy `ngrok.exe` vào thư mục project

### Bước 2: Chạy Server

**Terminal 1** - Chạy server Python:
```powershell
python server/main_server.py
```

### Bước 3: Chạy Ngrok

**Terminal 2** - Tạo tunnel:
```powershell
ngrok tcp 9999
```

Bạn sẽ thấy output:
```
Session Status                online
Forwarding                    tcp://2.tcp.ngrok.io:12345 -> localhost:9999
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^
                              Địa chỉ công khai cho bạn bè
```

### Bước 4: Bạn Bè Kết Nối

Bạn bè nhập trong popup kết nối:
- **IP Server**: `2.tcp.ngrok.io` ← từ ngrok output
- **Port**: `12345` ← từ ngrok output
- **Tên**: Tên của họ

**Lưu ý**: Ngrok free có giới hạn 1 tunnel cùng lúc, nhưng không giới hạn số client kết nối vào tunnel đó.

---

## 🔧 Troubleshooting

### ❌ Lỗi: "No connection could be made"

**Nguyên nhân & Giải pháp**:

1. **Firewall chặn** → Mở port 9999 (xem Bước 2)
2. **Không cùng mạng** → Kiểm tra IP bằng `ipconfig` trên cả 2 máy
3. **Server chưa chạy** → Khởi động server trước khi client kết nối
4. **IP sai** → Đảm bảo dùng đúng IP của máy Server (VD: `192.168.5.31`)

### ❌ Lỗi: "Connection refused" (Port 9999)

- Server chưa chạy hoặc đã dừng
- Port 9999 đang bị ứng dụng khác sử dụng

Kiểm tra port đang dùng:
```powershell
netstat -ano | findstr :9999
```

### ❌ Lỗi: "Phiên đấu giá đã kết thúc"

- Server đã chạy hơn 120 giây
- **Giải pháp**: Dừng server (Ctrl+C) và khởi động lại

---

## 📊 Demo Kịch Bản Multi-Player

### Setup:
- **Máy 1** (Server + Client): Bạn chạy server + client với tên `Host`
- **Máy 2** (Client): Bạn bè kết nối với tên `Alice`
- **Máy 3** (Client): Bạn bè kết nối với tên `Bob`

### Kịch Bản Test:

1. **Host** bid $1100 → tất cả 3 người nhận NEW_PRICE
2. **Alice** bid $1300 → tất cả 3 người nhận NEW_PRICE
3. **Bob** bid $1200 (thấp hơn) → chỉ Bob nhận ERROR
4. **Host** bid $1500 → tất cả 3 người nhận NEW_PRICE
5. **Alice** dùng Quick Bid +$500 → bid $2000
6. Đợi đến 10s còn lại → tất cả nhận WARNING
7. Hết 120s → tất cả nhận WINNER (Alice với $2000)

---

## 🎯 Tips Chơi Multi-Player

### Cho Host (Chạy Server):
- ✅ Mở firewall port 9999 TRƯỚC khi bạn bè kết nối
- ✅ Chia sẻ đúng IP cho bạn bè (kiểm tra lại bằng `ipconfig`)
- ✅ Đảm bảo server đang chạy trước khi bạn bè connect
- ✅ Theo dõi log server để xem ai đang kết nối

### Cho Clients (Bạn Bè):
- ✅ Đảm bảo cùng WiFi với Host (hoặc dùng ngrok nếu qua Internet)
- ✅ Nhập đúng IP:Port mà Host cung cấp
- ✅ Đặt tên khác nhau để dễ phân biệt
- ✅ Nếu lỗi kết nối, hỏi Host kiểm tra firewall

---

## 🎮 Tính Năng Đã Hỗ Trợ Multi-Player

✅ **Unlimited clients** - Server chấp nhận không giới hạn số client kết nối
✅ **Realtime broadcast** - Mọi bid được gửi đến tất cả clients ngay lập tức
✅ **Thread-safe locking** - Xử lý đúng khi nhiều người bid cùng lúc
✅ **Shared timer** - Tất cả clients thấy cùng countdown
✅ **Fair winner** - Người giữ giá cao nhất khi hết giờ thắng

---

## 📞 Liên Hệ & Support

Nếu gặp vấn đề kết nối, kiểm tra:
1. Firewall settings
2. Network connectivity (`ping 192.168.5.31` từ máy client)
3. Server logs để xem lỗi
4. Client GUI log feed để thấy error messages

Chúc bạn chơi vui! 🎉
