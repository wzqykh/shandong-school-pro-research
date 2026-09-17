/*
 * Read-only Frida logger for Sunshine Run geofence and checkpoint data.
 * It does not modify app behaviour and does not bypass face recognition.
 */

if (Java.available) {
  Java.perform(function () {
    var classNames = [
      "com.huachenjie.common.bean.GeoFenceDetail",
      "com.huachenjie.common.bean.UsableGeoFence",
      "com.huachenjie.sdk.map.adapter.location.model.HCJGeoFence",
      "com.huachenjie.common.map.GeoFenceComponent",
      "com.huachenjie.running.page.geofence.GeoFenceActivityVM",
      "com.huachenjie.running.page.geofence.GeoFenceFragment"
    ];

    var methodNames = [
      "setPointList",
      "getPointList",
      "getFenceList",
      "setFenceList",
      "getGeoFenceList",
      "getAllGeoFence"
    ];

    function safeJson(value) {
      try {
        return JSON.stringify(value);
      } catch (err) {
        return String(value);
      }
    }

    classNames.forEach(function (className) {
      try {
        var clazz = Java.use(className);
        methodNames.forEach(function (methodName) {
          if (!clazz[methodName]) {
            return;
          }
          clazz[methodName].overloads.forEach(function (overload) {
            overload.implementation = function () {
              var result = overload.apply(this, arguments);
              var payload = {
                class: className,
                method: methodName,
                args: Array.prototype.slice.call(arguments).map(safeJson),
                result: safeJson(result)
              };
              console.log("[geofence_logger] " + JSON.stringify(payload));
              return result;
            };
          });
        });
      } catch (err) {
        console.log("[geofence_logger] skip " + className + ": " + err);
      }
    });
  });
} else {
  console.log("[geofence_logger] Java runtime unavailable");
}
