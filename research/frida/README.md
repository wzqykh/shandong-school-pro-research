# Frida 只读观测脚本

`geofence_logger.js` 用于在测试设备上记录阳光跑围栏和打卡点相关 Java 方法的输入与输出。

使用前提：

- 设备已安装 frida-server 或可注入 Frida gadget。
- 使用测试账号，不用于真实成绩提交。
- 不修改 App 行为，不绕过人脸。

运行示例：

```bash
frida -U -f com.huachenjie.shandong_school_pro -l geofence_logger.js
```

只记录 `GeoFenceDetail`、`UsableGeoFence`、`HCJGeoFence`、`GeoFenceComponent` 等类的点列表和围栏列表方法。
