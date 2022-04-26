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

        self._generateGcode = function(callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/gcode",
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    // if(response.hasOwnProperty("src")) {
                    //     self._drawImage(response.src);
                    // }
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
        };

        self._clearImageFolder = function(callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "gridcam/clear_folder",
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    // if(response.hasOwnProperty("src")) {
                    //     self._drawImage(response.src);
                    // }
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
            setInterval(function() {self._getImage('BIM');}, 100)
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

