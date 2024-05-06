# fix_lcu_window

## 编译
``` shell
gcc main.c -o main.exe -O2 -static-libgcc
```

## 运行
以**管理员身份**：
``` shell
.\fix_lcu_window.exe <dpi_scall>
```

### 参数

- `dpi_scall`（必需）：英雄联盟窗口缩放大小，有以下三种选择：
  - `0.8`：对应设置中的 `1024 * 576`；
  - `1.0`：对应设置中的 `1280 * 720`；
  - `1.25`：对应设置中的 `1600 * 900`。
  
  该值可由 `connector.getClientZoom()` 函数直接获得。

### 返回值
- 永远是 0。


## 参考资料
- https://github.com/LeagueTavern/fix-lcu-window