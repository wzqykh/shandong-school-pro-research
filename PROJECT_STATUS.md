# 项目状态索引

更新时间：2026-09-18

## 一句话定位

闪动校园Pro 本地客户端逆向研究、权限最小化、去广告验证，以及后续围栏/打卡点协议与动态观测研究。

## 下次如何让我继续

在新会话直接说：

> 继续闪动校园Pro项目，看 PROJECT_STATUS.md。

我会先读这个文件，并检查：

- `/home/wzqykh/shandong-school-pro-research`
- `/mnt/d/shandong_school_pro_local`
- GitHub 私有仓库 `wzqykh/shandong-school-pro-research`

## 关键位置

- GitHub 代码库：`https://github.com/wzqykh/shandong-school-pro-research`
- 本地代码：`/home/wzqykh/shandong-school-pro-research`
- Windows 项目目录：`D:\shandong_school_pro_local`
- 原版 APK：`D:\shandong_school_pro_local\apk\original\base_26083114_e66628aa2e6a.apk`
- APK SHA256：`e66628aa2e6aabd59e15f893715a23091a2be8390b289008f10a501acec88cec`

## 已完成

- 阶段 0：设备、APK、加固识别。
- 阶段 1：权限最小化与操场实测通过。
- 阶段 2：AdGuard 去广告实测通过。
- 阶段 3：确认网易易盾加固，默认不进入改 APK。
- 代码框架：profiles、apk_lab、protocol_lab、transport、session、motion_lab、detection_lab、telemetry、pipeline。
- 测试：本地 pytest 26 passed。
- 学校规则已从 App 提取。
- 围栏列表已从 App 提取。
- 静态 DEX 分析确认真实业务类被易盾壳加密。
- 已准备只读 Frida 围栏日志脚本。
- 已新增 `rules_lab`：学校规则、围栏目录、围栏多边形与打卡点模型，以及只读轨迹回放校验。
- 已将 2.0.6 学校规则、围栏目录落成结构化 JSON，并把关键 App UI dump 存入 `research/ui_dumps/`。
- 本地测试扩展到 37 passed。

## 待办

1. 等新的可解锁 Bootloader 备用机。
2. 在新设备上搭建 Frida/LSPosed 或网络抓包环境。
3. 提取精确围栏多边形和 3 个顺序打卡点坐标。
4. 将围栏/打卡点写入 `profiles/<version>.yaml`。
5. 用 `motion_lab` 做只读回放和边界测试。

> 待办 4 已先建立 `2.0.6.geofence.example.json` 和
> `2.0.6.geofence_plan.example.json` 作为占位 schema；拿到动态观测数据后只需回填
> `polygon` / `points`，无需再改代码结构。

## 边界

- 只做本地研究、自动化测试和协议分析。
- 不伪造真实成绩，不绕过人脸，不攻击平台。
- 高风险结果仅用于研究，不用于破坏公平性。
