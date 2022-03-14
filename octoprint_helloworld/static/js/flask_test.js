$(function() {
    function HelloWorldViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        // this will hold the URL currently displayed by the iframe
        self.currentUrl = ko.observable();

        // this will hold the URL entered in the text field
        self.newUrl = ko.observable();

        // self._getImage = function(imagetype, callback) {
        //     $.ajax({
        //         url: "/plugin/helloworld/echo/",
        //         type: "GET",
        //         dataType: "json",
        //         contentType: "application/json; charset=UTF-8",
        //         //data: JSON.stringify(data),
        //         success: function(response) {
        //             if(response.hasOwnProperty("src")) {
        //                 self._drawImage(response.src);
        //             }
        //             if(response.hasOwnProperty("error")) {
        //                 alert(response.error);
        //             }
        //             if (callback) callback();
        //         }
        //     });
        // };

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

                // crosshairs
                ctx.beginPath();
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 1;
                ctx.fillStyle = "#000000";
                ctx.fillRect(0, ((h*scale)/2)-0.5, w*scale, 1);
                ctx.fillRect(((w*scale)/2)-0.5, 0, 1, h*scale);

                // Avoid memory leak. Not certain if this is implemented correctly, but GC seems to free the memory every now and then.
                localimg = undefined;
            };
            if(break_cache) {
                img = img + "?" + new Date().getTime();
            }
            localimg.src = img;
        };
        // This will get called before the HelloWorldViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.

        // self.onBeforeBinding = function() {
        //     self.newUrl(self.settings.settings.plugins.helloworld.url());
        //     self.goToUrl();
        // }

        // self.videoStreamActive = ko.observable(false);
        // self.startVideo = function(url) {
        //     self.videoStreamActive(true);
        //     self.videoTimer = setInterval(function(){ self._drawImage(url, true); }, 100);
        // };
        //
        // self.stopVideo = function() {
        //     clearInterval(self.videoTimer);
        //     self.videoStreamActive(false);
        // };

        self._getImage = function(imagetype, callback) {
            $.ajax({
                url: PLUGIN_BASEURL + "helloworld/echo?imagetype=" + imagetype,
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

        self.goToUrl = function() {
            // self.currentUrl(self.newUrl());
            // self.startVideo("http://localhost:8888/videostream.cgi")

            // self._getImage('BED');
            // var ctx=self._headCanvas.getContext("2d");
            // ctx.fillStyle = "#44ff47";
            // ctx.fillRect(0, 0, 400, 300);

            // ajax({
            //     url: "/plugin/helloworld/echo/",
            //     type: "GET",
            //     dataType: "json",
            //     contentType: "application/json; charset=UTF-8",
            //     //data: JSON.stringify(data),
            //     success: function(response) {
            //         if(response.hasOwnProperty("src")) {
            //             self._drawImage(response.src);
            //         }
            //         if(response.hasOwnProperty("error")) {
            //             alert(response.error);
            //         }
            //         if (callback) callback();
            //     }
            // });
            // $.get("/plugin/helloworld/echo/");
            // setInterval(function() {self._getImage('BIM');}, 100)
            self._getImage('BIM');
            // self._getImage("BIM");
        };


    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        HelloWorldViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_helloworld"]
    ]);
});

