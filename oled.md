- 輸入 `sudo raspi-config`。
    
- 選擇 **Interface Options** -> **I2C** -> **Yes**。
- ls /dev/i2c*
# 如果看到 /dev/i2c-1，表示驅動已開
接著安裝檢測工具：

Bash

```
sudo apt-get install i2c-tools -y
sudo i2cdetect -y 1
```**看結果：** 如果你在表格中看到 **`3c`**，恭喜你，接線完全正確！這就是 SSD1306 的預設地址。