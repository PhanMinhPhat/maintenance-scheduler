sap.ui.define(
  ["sap/ui/core/UIComponent", "sap/ui/Device", "sap/ui/model/json/JSONModel"],
  function (UIComponent, Device, JSONModel) {
    "use strict";

    return UIComponent.extend("maintenance.scheduler.Component", {
      metadata: {
        manifest: "json",
      },

      init: function () {
        // Call the base component's init function
        UIComponent.prototype.init.apply(this, arguments);

        // Set device model
        var oDeviceModel = new JSONModel(Device);
        oDeviceModel.setDefaultBindingMode("OneWay");
        this.setModel(oDeviceModel, "device");

        // Initialize the router
        this.getRouter().initialize();
      },
    });
  }
);
