# DEX 静态分析结果

分析工具：androguard 4.1.4

## 结论

`classes.dex` 只包含 30 个类，全部是网易易盾 wrapper：

- `Lcom/netease/nis/wrapper/*`
- `La/auu/a;`

这意味着真实业务类（GeoFence、SunshineRun、RunPlan 等）不在可直接反编译的 `classes.dex` 中，而是在易盾壳的加密 DEX 或 native 层。

## 与之前字符串提取的关系

之前用 `strings` 找到的 `GeoFenceDetail`、`HCJGeoFence`、`/running/sunshineRunV3` 等字符串存在于 DEX 字符串池或资源中，但对应类实现无法通过普通 `classes.dex` 反编译读取。

## 对项目的影响

- 静态提取精确围栏多边形和打卡点坐标在本机不可行。
- 继续提取需要动态观测，可选路径：
  1. 网络抓包：在测试设备上安装 CA + 代理，记录 `attendanceRange` / `attendanceRule` / `getSchoolConfig` 响应。
  2. Frida：需要可注入环境，先打通 frida-server 或 gadget。
  3. Shizuku / LSPosed：如果设备已具备模块运行条件，加载只读 Hook 记录 `pointList`。

## 当前已提交的只读工具

- `research/frida/geofence_logger.js`

## 边界

只做数据观测和协议结构研究，不用于伪造成绩，不绕过人脸。
