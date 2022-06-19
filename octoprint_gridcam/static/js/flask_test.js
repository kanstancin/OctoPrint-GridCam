$(function() {
    function GridCamViewModel(parameters) {
        var self = this; 

        self.settings = parameters[0];

        // this will hold the URL currently displayed by the iframe
        self.currentUrl = ko.observable();

        // this will hold the URL entered in the text field
        self.newUrl = ko.observable();

        // this will hold the URL entered in the text field
        self.zOffset = ko.observable();

        self._headCanvas = document.getElementById('headCanvas');
        // this will be called when the user clicks the "Go" button and set the iframe's URL to
        // the entered URL
        self._drawImage = function(img, break_cache = false) {
            var ctx=self._headCanvas.getContext("2d");
            var localimg = new Image();
            localimg.onload = function () {
                var w = localimg.width;
                var h = localimg.height;
                var scale = Math.min(ctx.canvas.clientWidth/w, ctx.canvas.clientHeight/h,1);
                ctx.drawImage(localimg, 0, 0, w*scale, h*scale);

                // Avoid memory leak. Not certain if this is implemented correctly, but GC seems to free the memory every now and then.
                localimg = undefined;
            };
            if(break_cache) {
                img = img + "?" + new Date().getTime();
            }
            localimg.src = img;
        };

        self._getImage = function(imagetype, callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/echo?imagetype=" + imagetype,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    if(response.hasOwnProperty("src")) {
                        self._drawImage(response.src);
                    }
                    if(response.hasOwnProperty("error")) {
                        alert(response.error);
                    }
                    if (callback) callback();
                }
            });
        };

        self._generateGcode = function(controls, callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/gcode?controls=" + controls,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    if(response.hasOwnProperty("src")) {
                        alert(`Please, upload the following gcode file:\n ${response.src}`);
                    }
                    // if(response.hasOwnProperty("error")) {
                    //     alert(response.error);
                    // }
                    if (callback) callback();
                }
            });
        };

        self.generateGcode = function() {
            msg = [self.settings.settings.plugins.gridcam.speed(),
                   self.settings.settings.plugins.gridcam.grids_num(),
                   self.settings.settings.plugins.gridcam.z_offset()].join(',');
            self._generateGcode(msg);
            //alert(`Gcode file can be found:\n gcodes/${}`);
        };

        self._clearImageFolder = function(callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/clear_folder",
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    if(response.hasOwnProperty("src")) {
                        alert("Image folder has been cleared.");
                    }
                    // if(response.hasOwnProperty("error")) {
                    //     alert(response.error);
                    // }
                    if (callback) callback();
                }
            });
        };

        self.clearImageFolder = function() {
            self._clearImageFolder();
        };

        self.goToUrl = function() {
            setInterval(function() {self._getImage('BIM');}, 20)
        };

        self.homePrintHead = function() {
            OctoPrint.control.sendGcode("G0 X355 Y355 F2000");
            alert("Homing command has been sent.");
        };

        self.processGcode = function() {
            // OctoPrint.control.sendGcode("G0 X355 Y355 F2000");
            const gcode_filename = document.getElementById("gcodefile").files[0]
            let text = gcode_filename.text();
            //  const formData = new FormData(form);
            // var oOutput = document.getElementById("static_file_response")
            // alert(`${gcode_filename.name}`);
            msg = [self.settings.settings.plugins.gridcam.gcode_corner_step(), gcode_filename.name, 0].join(',');
            var fileReader = new FileReader();
            fileReader.onload = function(fileLoadedEvent){
              var textFromFileLoaded = fileLoadedEvent.target.result;
              // alert(`${typeof textFromFileLoaded}`);
              self._processGcode2(textFromFileLoaded, msg);
            };

            fileReader.readAsText(gcode_filename, "UTF-8");

        };

        self._processGcode = function(text1, controls, callback) {
            $.post( PLUGIN_BASEURL + "gridcam/upload_static_file?controls=" + controls, { token: text1 },
                );
        };
        self._processGcode2 = function(text1, controls, callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/upload_static_file?controls=" + controls,
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify({text: text1}),
                success: function(response) {
                    if(response.hasOwnProperty("src")) {
                        alert("Successfully saved gcode in 'gcodes' folder");
                    }
                    // if(response.hasOwnProperty("error")) {
                    //     alert(response.error);
                    // }
                    if (callback) callback();
                }
            });
        };
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        GridCamViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_gridcam"]
    ]);
});

