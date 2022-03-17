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
import os
import shutil

dir = 'images'
if os.path.exists(dir):
    shutil.rmtree(dir)
os.makedirs(dir)

class GridCamPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.BlueprintPlugin):

    def __init__(self):
        self.cam = ''

    def on_after_startup(self):
        self._logger.info("GridCam \n(more: %s)" % self._settings.get(["url"]))
        self.cam = cv.VideoCapture(0)

    def get_settings_defaults(self):
     return dict(url="https://mosaicmfg.com/", z_offset=0.7)

    def get_template_configs(self):
     return [
         dict(type="navbar", custom_bindings=False),
         dict(type="settings", custom_bindings=False)
     ]

    def get_assets(self):
     return dict(
         js=["js/flask_test.js"],
         css=["css/gridcam.css"]
     )

    @octoprint.plugin.BlueprintPlugin.route("/echo", methods=["GET"])
    def getCameraImage(self):
        result = ""
        # self._logger.info("Hello World! \n\n\n\n\n(more: )")
        ret, img = self.get_img_stream()
        shape = img.shape[:2]
        res = 360
        dim = (int(res * shape[1] / shape[0]), res)
        img = cv.resize(img, dim, interpolation=cv.INTER_AREA)

        retval,  buffer = cv.imencode('.jpg', img)

        if "imagetype" in flask.request.values:
            camera = flask.request.values["imagetype"]
            if camera in ("HEAD", "BIM"):
                if True:
                    # self._settings.get(["camera", camera.lower(), "path"])
                    try:
                        result = flask.jsonify(
                            src="data:image/{0};base64,{1}".format(
                                ".jpg",
                                str(base64.b64encode(buffer), "utf-8"))
                        )
                    except IOError:
                        result = flask.jsonify(
                            error="Unable to open Webcam stream"
                        )
                else:
                    result = flask.jsonify(
                        error="Unable to fetch image. Check octoprint log for details."
                    )
            # self._printer.commands("M114")
        return flask.make_response(result, 200)

    def get_img_stream(self):
        ret, img = self.cam.read()
        # self.cam.release()
        return ret, img

    def parse_gcode_imsave(self, comm, line, *args, **kwargs):

        pattern = "X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
        result = re.findall(pattern, line)
        if len(result) == 1:
            ret, img = self.get_img_stream()
            im_name = f"images/img_X{result[0][0]}_Y{result[0][1]}.jpg"
            cv.imwrite(im_name, img)
            # self._logger.info(line)
            self._logger.info(f"\nsaving image: {im_name}\n")
        # else:
        #     self._logger.info(line)
        return line


__plugin_name__ = "GridCam"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = GridCamPlugin()
__plugin_hooks__ = {
    "octoprint.comm.protocol.gcode.received": __plugin_implementation__.parse_gcode_imsave
}

