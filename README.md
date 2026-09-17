# FlashRun Lab

面向版本迭代的 Android 客户端逆向研究、协议一致性验证、传感器/轨迹自动化测试与风控检测面分析框架。

当前实现阶段：

- `profiles`：版本、端点、密钥、设备指纹档案。
- `apk_lab`：APK 拉取、哈希、版本识别、manifest/权限/组件提取。

后续阶段：

- `protocol_lab`
- `transport`
- `session`
- `motion_lab`
- `detection_lab`
- `telemetry`

## 边界

本项目仅用于 Android 开发调试、自动化测试与逆向安全研究，不包含可直接用于伪造成绩、绕过人脸或破坏平台公平性的成品模块。

## 目录

```text
src/flashrun_lab/
  profiles.py
  apk_lab.py
  cli.py
profiles/
  8.6.8.example.json
tests/
  test_profiles.py
```
