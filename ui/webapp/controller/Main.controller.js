sap.ui.define(
  ["sap/ui/core/mvc/Controller", "sap/m/MessageToast", "sap/m/MessageBox"],
  function (Controller, MessageToast, MessageBox) {
    "use strict";

    return Controller.extend("maintenance.scheduler.controller.Main", {
      onInit: function () {
        this.getView().setModel(
          new sap.ui.model.json.JSONModel({
            scheduleData: [],
          })
        );
      },

      handleFileSelect: function (oEvent) {
        var file = oEvent.getParameter("files")[0];
        if (!file) {
          MessageToast.show("Please select a file first");
          return;
        }
      },

      handleUploadPress: function (oEvent) {
        var fileUploader = this.getView().byId("fileUploader");
        if (!fileUploader.getValue()) {
          MessageToast.show("Please select a file first");
          return;
        }

        fileUploader.upload();
      },

      handleUploadComplete: function (oEvent) {
        try {
          var responseRaw = oEvent.getParameter("responseRaw");
          var response;
          
          try {
            response = JSON.parse(responseRaw);
          } catch (parseError) {
            MessageBox.error("Server response is not in the expected format");
            return;
          }

          if (response.error) {
            MessageBox.error(response.error);
            return;
          }

          // Update the model with schedule data
          var oModel = this.getView().getModel();
          oModel.setProperty("/scheduleData", response);

          // Show the table
          this.getView().byId("scheduleTable").setVisible(true);
          
          MessageToast.show("Schedule generated successfully");
        } catch (error) {
          MessageBox.error("An error occurred while processing the response: " + error.message);
        }
      },

      handleTemplateDownload: function () {
        window.location.href = "/api/download_template";
      },

      handleScheduleDownload: function () {
        window.location.href = "/api/download_schedule";
      },
    });
  }
);
