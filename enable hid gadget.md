
sudo -i
modprobe libcomposite

ls -la /sys/kernel/config/usb_gadget

  

# 1. 進入目錄  
cd /sys/kernel/config/usb_gadget  
  
# 2. 建立你的 gadget 實例  
mkdir g1  
cd g1  
  
# 3. 寫入基本 ID (這幾步如果不成功，代表核心模組沒掛載好)  
echo 0x1d6b > idVendor  
echo 0x0104 > idProduct

# 建立功能目錄  
mkdir -p functions/hid.usb0  
echo 1 > functions/hid.usb0/protocol  
echo 1 > functions/hid.usb0/subclass  
echo 8 > functions/hid.usb0/report_length  
  
# 寫入二進位描述符 (務必完整複製這行)  
echo -ne "\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x03\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0" > functions/hid.usb0/report_desc

  

# 建立配置字串  
mkdir -p configs/c.1/strings/0x409  
echo "Config 1: HID" > configs/c.1/strings/0x409/configuration  
  
# 將 HID 功能連結到配置中  
ln -s functions/hid.usb0 configs/c.1/  
  
# 最後一擊：啟用 UDC (將虛擬設備與物理 USB-C 孔綁定)  
ls /sys/class/udc > UDC

Test:
computer:
dmesg | tail
PI:
ls -l /dev/hidg0


```bash
#!/bin/bash
# 必須以 root 權限執行
modprobe libcomposite
cd /sys/kernel/config/usb_gadget
mkdir -p g1
cd g1
echo 0x1d6b > idVendor
echo 0x0104 > idProduct
mkdir -p configs/c.1/strings/0x409
echo "Config 1: HID" > configs/c.1/strings/0x409/configuration
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne "\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x03\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0" > functions/hid.usb0/report_desc
ln -s functions/hid.usb0 configs/c.1/
ls /sys/class/udc > UDC
chmod 666 /dev/hidg0  # 讓一般使用者也能寫入
```