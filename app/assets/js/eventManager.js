let eventManager = {
  activeProject: null,
  activeVersion: null,
  activePanel: "input",
  activeView: null,
  projects: [],
  versions: [],
  init: function () {
    $(".nav-item").click(function () {
      eventManager.navItemClick($(this));
    });
    eventManager.initializeUsers();
    eventManager.downloadTemplate();
    eventManager.uploadDataEvent();
    eventManager.initProjectHandlers();
    eventManager.initVersionHandlers();
    eventManager.loadProjects();
    eventManager.initAccessHandlers();
    dataManager.loadDataSheet();
    queryBuilderManager.init();
    eventManager.navItemClick($(".nav-item[data-panel='input']"));
    aiAssistant.init();
  },
  initAccessHandlers: function () {
    $("#active-project-users").change(function () {
      fetch(
        constants.HOST_URL +
          `api/projects/${$("#active-project-name").val()}/users`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ users: $("#active-project-users").val() }),
        }
      );
    });
  },
  initializeUsers: function () {
    fetch(constants.HOST_URL + "api/users")
      .then((response) => response.json())
      .then((users) => {
        users.forEach((user) => {
          $("#active-project-users").append(
            `<option value="${user.username}">${user.username}</option>`
          );
        });
      })
      .catch((error) => console.error("Error:", error));
    $("#active-project-users").trigger("chosen:updated");
  },
  setActiveProject: function (projectId) {
    $("#current-project-id").val(projectId);
  },
  setActiveVersion: function (versionId) {
    $("#current-version-id").val(versionId);
  },
  showLoading: function () {
    $("#loading-screen").show();
  },
  hideLoading: function () {
    $("#loading-screen").hide();
  },
  showPanel: function (panel) {
    $(".panel[data-panel='" + panel + "']")
      .show()
      .removeClass("hidden");
  },
  hidePanel: function (panel) {
    $(".panel[data-panel='" + panel + "']")
      .hide()
      .addClass("hidden");
  },
  navItemClick: function (navItem) {
    $(".nav-item").removeClass("active");
    navItem.addClass("active");

    $(".panel").hide().addClass("hidden");
    const panel = navItem.data("panel");
    eventManager.showPanel(panel);
    eventManager.activePanel = panel;

    $(".controls-group").hide().addClass("hidden");
    $(".controls-group").each(function () {
      if ($(this).data("panel").indexOf(panel) !== -1) {
        $(this).show().removeClass("hidden");
      }
    });
    eventManager.chosenJSInit();
    // extra events for panels:
    if (panel === "input") {
      dataManager.loadDataSheet();
    }
    if (panel === "xs-quant") {
      dataManager.loadCrossSellData();
    }
    if (panel === "fact-pack") {
      dataManager.loadFactPackData();
    }
    if (panel === "price-uplift") {
      dataManager.loadPriceUpliftData();
    }
    if (panel === "segmentation") {
      dataManager.loadSegmentationData();
    }
  },
  downloadTemplate: function () {
    $("#download-template").click(function () {
      window.open(constants.HOST_URL + "/data/template.xlsx", "_blank");
    });
  },
  chosenJSInit: function () {
    // destroy all chosen instances
    $(".chosen-container").each(function () {
      $(this).chosen("destroy");
    });
    $("select").each(function () {
      // if it is in #builder, don't use chosen
      if ($(this).closest("#builder").length === 0) {
        $(this).chosen({
          disable_search: true,
        });
      }
    });
  },
  initProjectHandlers: function () {
    $("#active-project-name").change(function () {
      eventManager.loadProjects($("#active-project-name").val());
    });
    $("#active-version-name").change(function () {
      eventManager.loadProjects(
        $("#active-project-name").val(),
        $("#active-version-name").val()
      );
    });
    $("#add-project").click(function () {
      eventManager.showModal("project-modal");
    });
    $("#project-form").submit(function (e) {
      e.preventDefault();
      const projectData = {
        project_name: $("#project-name").val(),
        description: $("#project-description").val(),
        client_name: $("#client-name").val(),
      };
      fetch(constants.HOST_URL + "api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(projectData),
      })
        .then((response) => response.json())
        .then((data) => {
          eventManager.closeModal("project-modal");

          eventManager.loadProjects(data.project_name);
          $("#project-form").trigger("reset");
        })
        .catch((error) => console.error("Error:", error));
    });
  },
  initVersionHandlers: function () {
    $("#add-version").click(function () {
      eventManager.showModal("version-modal");
    });

    $("#version-form").submit(function (e) {
      e.preventDefault();
      const versionData = {
        version_name: $("#version-name").val(),
        description: $("#version-description").val(),
      };

      fetch(
        constants.HOST_URL +
          `api/projects/${$("#active-project-name").val()}/versions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(versionData),
        }
      )
        .then((response) => response.json())
        .then((data) => {
          eventManager.closeModal("version-modal");
          $("#version-form").trigger("reset");
          eventManager.loadProjects(
            $("#active-project-name").val(),
            data.version_name
          );
          eventManager.hideLoading();
        })
        .catch((error) => console.error("Error:", error))
        .finally(() => {});
    });
  },
  showModal: function (modalId) {
    $(`#${modalId}`).show();
  },
  closeModal: function (modalId) {
    $(`#${modalId}`).hide();
  },
  loadProjects: function (projectName = null, versionName = null) {
    fetch(constants.HOST_URL + "api/projects")
      .then((response) => response.json())
      .then((projects) => {
        $("#active-project-name").empty();
        $("#active-version-name").empty();
        // remove all options from chosen chosen-choices
        $("#active-project-name").trigger("chosen:updated");
        $("#active-version-name").trigger("chosen:updated");
        $("#active-project-users").trigger("chosen:updated");
        projects.forEach((project) => {
          $("#active-project-name").append(
            `<option value="${project.project_name}">${project.project_name}</option>`
          );
        });
        if (projectName) {
          let project = projects.find(
            (project) => project.project_name === projectName
          );
          project.versions.forEach((version) => {
            $("#active-version-name").append(
              `<option value="${version.version_name}">${version.version_name}</option>`
            );
          });
          $("#active-project-users")
            .val(project.users)
            .trigger("chosen:updated");
        } else {
          projects[0].versions.forEach((version) => {
            $("#active-version-name").append(
              `<option value="${version.version_name}">${version.version_name}</option>`
            );
          });
          $("#active-project-users")
            .val(projects[0].users)
            .trigger("chosen:updated");
        }
        if (projectName) {
          $("#active-project-name").val(projectName).trigger("chosen:updated");
        }
        if (versionName) {
          $("#active-version-name").val(versionName).trigger("chosen:updated");
        }
        $("#active-project-name").trigger("chosen:updated");
        $("#active-version-name").trigger("chosen:updated");
        $("#active-project-users").trigger("chosen:updated");
      })
      .catch((error) => console.error("Error:", error))
      .finally(() => {
        eventManager.hideLoading();
        dataManager.loadDataSheet();
      });
  },
  refreshActiveView: function () {
    console.log("refreshActiveView");
  },
  uploadDataEvent: function () {
    $("#upload-input").click(function () {
      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ".xlsx";
      fileInput.onchange = function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        eventManager.showLoading();
        fetch(
          constants.HOST_URL +
            `data/upload/${$("#active-project-name").val()}/${$(
              "#active-version-name"
            ).val()}`,
          {
            method: "POST",
            body: formData,
          }
        )
          .then((response) => response.json())
          .then((data) => {
            // Reload projects after successful upload
            eventManager.loadProjects(
              $("#active-project-name").val(),
              $("#active-version-name").val()
            );
            dataManager.loadDataSheet();
          })
          .catch((error) => console.error("Error:", error))
          .finally(() => {
            eventManager.hideLoading();
          });
      };
      fileInput.click();
    });
  },
  updateActiveViewSelector: function () {
    $("#active-view-selector").empty();
    Object.keys(dataManager.data).forEach((sheet) => {
      $("#active-view-selector").append(
        `<option value="${sheet.replace('_','-')}">${dataManager.data[sheet].name}</option>`
      );
    });
    $("#active-view-selector").trigger("chosen:updated");
    $("#active-view-selector").off("change");
    $("#active-view-selector").change((e) => {
      $('.view-container').addClass('hidden');
      eventManager.activeView = e.target.value;
      console.log('#' + eventManager.activePanel + '-' + eventManager.activeView + ' is not hidden');
      $('#' + eventManager.activePanel + '-' + eventManager.activeView).removeClass('hidden');
      render.updateView();
    });
  },
};
