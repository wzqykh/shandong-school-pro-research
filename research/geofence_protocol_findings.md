# 围栏 / 打卡点 / 阳光跑接口静态发现

分析日期：2026-09-17

## 从 App UI 读到的围栏列表

“跑步区域 → 更多”显示：

- 田径场：0.07 公里，开放中
- 西田径场：3.36 公里，开放中
- 东田径场：3.80 公里，开放中
- 田径场：6.84 公里，开放中

说明：UI 只显示名称和距离，未直接暴露经纬度多边形。

## 从 classes.dex 提取的相关接口

- `/running/sunshineRun`
- `/running/sunshineRunV3`
- `/running/sunshineRunningDetail`
- `/running/sunshineRunningDetailRoute`
- `/running/sunshineRank`
- `/sport/attendance`
- `/sport/attendancePeriod`
- `/sport/attendancePlan`
- `/sport/attendanceRange`
- `/sport/attendanceRule`
- `$run-front/sso/school/getSchoolConfig`
- `run-front/run/free/detail`

## 相关类名

- `GeoFenceDetail`
- `UsableGeoFence`
- `HCJGeoFence`
- `GeoFenceNetManager`
- `GeoFenceUtil`
- `RunPlanBean`
- `RunPlanListBean`
- `SunRunActivityData`
- `SchoolRule`
- `CommonConfig`
- `SunshineRunFaceCheckData`
- `SunshineRunFaceRecord`
- `SunshineRunFinishData`
- `SunshineRunServiceData`
- `SunshineRunningDetail`

## 关键常量

- `SUNSHINE_RUNNING_MIN_DISTANCE`
- `SUNSHINE_RUNNING_MIN_DURATIN`
- `TYPE_SUNSHINE_RUNNING`
- `BUNDLE_KEY_FENCE`
- `BUNDLE_KEY_FENCEID`
- `BUNDLE_KEY_FENCESTATUS`

## 尚未完成

- 精确围栏多边形坐标。
- 3 个顺序打卡点的精确坐标。
- `getSchoolConfig` / `attendanceRange` / `attendanceRule` 的响应结构。

下一步建议：

1. 在测试设备上打开阳光跑引导页，抓取 `attendanceRange` / `attendanceRule` / `getSchoolConfig` 响应。
2. 若不方便抓包，则动态 Hook `GeoFenceNetManager` / `HCJGeoFence.setPointList` / `getPointList`，只记录数据。
3. 将抓到的 polygon/pointList 写入 `profiles/<version>.yaml`，供 `motion_lab` 使用。
