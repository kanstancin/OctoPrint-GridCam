

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from octoprint.util.comm import parse_firmware_line
import logging

import re
import octoprint.plugin
import flask
import os
import base64

import cv2 as cv

class HelloWorldPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.BlueprintPlugin):

    def __init__(self):
        self.cam = cv.VideoCapture(0)

    def on_after_startup(self):
        self._logger.info("Hello World! \n\n\n\n\n(more: %s)" % self._settings.get(["url"]))

    def get_settings_defaults(self):
     return dict(url="https://en.wikipedia.org/wiki/Hello_world")

    def get_template_configs(self):
     return [
         dict(type="navbar", custom_bindings=False),
         dict(type="settings", custom_bindings=False)
     ]

    def get_assets(self):
     return dict(
         js=["js/flask_test.js"],
         css=["css/helloworld.css"]
     )

    @octoprint.plugin.BlueprintPlugin.route("/echo", methods=["GET"])
    def getCameraImage(self):
        result = ""
        # self._logger.info("Hello World! \n\n\n\n\n(more: )")
        imagePath = "data/saved_img.png"
        ret, img = self.get_img_stream()
        retval,  buffer = cv.imencode('.png', img)

        if "imagetype" in flask.request.values:
            camera = flask.request.values["imagetype"]
            if camera in ("HEAD", "BIM"):
                if True:
                    imagePath = "data/saved_img.png";  # self._settings.get(["camera", camera.lower(), "path"])
                    try:
                        with open(imagePath, "rb") as f:
                            result = flask.jsonify(
                                src="data:image/{0};base64,{1}".format(
                                    os.path.splitext(imagePath)[1],
                                    str(base64.b64encode(buffer), "utf-8"))
                            )
                    except IOError:
                        result = flask.jsonify(
                            error="Unable to open Image after fetching. Image path: "
                            + imagePath
                        )
                else:
                    result = flask.jsonify(
                        error="Unable to fetch image. Check octoprint log for details."
                    )
            self._printer.commands("M114")
        return flask.make_response(result, 200)

    def get_img_stream(self):
        ret, img = self.cam.read()
        # self.cam.release()
        return ret, img

    def detect_machine_type(self, comm, line, *args, **kwargs):
        # if "MACHINE_TYPE" not in line:
        #     return line
        #
        # # Create a dict with all the keys/values returned by the M115 request
        # printer_data = parse_firmware_line(line)
        #
        # logging.getLogger("octoprint.plugin." + __name__).info(
        #     "Machine type detected\n\n\n: {machine}.\n\n\n".format(machine=printer_data["MACHINE_TYPE"]))

        pattern = "X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
        result = re.findall(pattern, line)
        if len(result) == 1:
            self._logger.info(result[0])

        return line

# class HelloWorldPlugin(octoprint.plugin.BlueprintPlugin):
#     def on_after_startup(self):
#         self._logger.info("Hello Worlkkd!\n\n\n\n\n ")
#
#     @octoprint.plugin.BlueprintPlugin.route("/echo", methods=["GET"])
#     def myEcho(self):
#         self._logger.info("Hello World! (more)")
#         if not "text" in flask.request.values:
#             abort(400, description="Expected a text to echo back.")
#         return flask.request.values["text"]


# __plugin_implementation__ = HelloWorldPlugin()


__plugin_name__ = "helloworld"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = HelloWorldPlugin()
__plugin_hooks__ = {
    "octoprint.comm.protocol.gcode.received": __plugin_implementation__.detect_machine_type
}

