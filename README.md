# FlashRun Lab

面向版本迭代的 Android 客户端逆向研究、协议一致性验证、传感器/轨迹自动化测试与风控检测面分析框架。

当前实现阶段：

- `profiles`：版本、端点、密钥、设备指纹档案。
- `apk_lab`：APK 拉取、哈希、版本识别、manifest/权限/组件提取。
- `protocol_lab`：endpoint schema、签名 oracle、抓包回放验签。
- `transport`：ADB / 直连 / Mock 传输抽象层。
- `session`：账号上下文和受限权限会话持久化。
- `motion_lab`：传感器/GPS 基线录制、时变步频、航点插值和故障注入。
- `detection_lab`：检测点测绘、严重度矩阵和静态字符串扫描。
- `telemetry`：结构化 run 记录、事件日志和敏感信息脱敏。
- `pipeline`：apk_lab 端到端编排，自动写报告并落 telemetry。

CI：

- `.github/workflows/ci.yml` 在 push / pull request 时运行 `compileall` 和 `pytest`。
- `tests/test_golden_sign.py` 固化 8.6.8 签名的 golden vector。

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
