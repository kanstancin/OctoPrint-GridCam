# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from octoprint.util.comm import parse_firmware_line
import logging

import re
import octoprint.plugin
import flask
import base64

import cv2 as cv
import os
import shutil
import urllib.request
import numpy as np

# from OctoPrint-GridCam.bin.gen_grid import create_gcode_file
def get_flag_positions(filepath):
    flag_seq = ";;;!!"
    flag_line_num = []
    with open(filepath) as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line[:len(flag_seq)] == flag_seq:
                flag_line_num.append(i)
    assert (len(flag_line_num) == 2), "error: there should be exactly two flag lines"
    return flag_line_num


def get_template(filepath, flag_line_num):
    template = [[], []]
    with open(filepath) as f:
        lines = f.readlines()
        template[0] = lines[:flag_line_num[0]+1]
        template[1] = lines[flag_line_num[1]:]
    return template


def create_gcode_file(template_path, speed, grids_num=10, z_offset=0.7, add_M114=True, delay=500):
    flag_line_num = get_flag_positions(template_path)
    template = get_template(template_path, flag_line_num)

    gcode_out_path = "gcodes/"
    if not os.path.exists(gcode_out_path):
        os.makedirs(gcode_out_path)
    gcode_filename = f"{gcode_out_path}/grid_F{speed}_GRIDS{grids_num}_Z{z_offset}.gcode"
    with open(gcode_filename, "w") as f:
        f.writelines(template[0])
        f.write("\n\n")  # main gcode
        gcode = get_grid_gcode(speed, grids_num, z_offset, add_M114, delay)
        # print(gcode)
        f.writelines(gcode)
        f.write("\n\n")
        f.writelines(template[1])


def create_grid(m,n):
    out = np.empty((m,n,2),dtype=int) #Improvement suggested by @AndrasDeak
    out[...,0] = np.arange(m)[:,None]
    out[...,1] = np.arange(n)
    return out


def get_grid_gcode(speed, grids_num, z_offset, add_M114, delay):
    start_point = (10, 10)
    end_point = (345, 345)
    step_x = (end_point[0] - start_point[0]) / grids_num
    step_y = (end_point[1] - start_point[1]) / grids_num

    first_lines = [f"G1 X{start_point[0]} Y{start_point[1]} Z{z_offset} F1000 ; go to the starting position\n",
                   f"G1 F{speed}; change speed \n\n",
                   f"G4 P3000 ; wait"]
    lines = first_lines

    a = create_grid(grids_num+1, grids_num+1)
    a[1::2] = np.flip(a[1::2], axis=1)
    for i_row_ind, i_row_arr in enumerate(a):

        first_element = True
        for i, j in i_row_arr:
            x_val = j * step_x + start_point[0]
            y_val = i * step_y + start_point[1]

            if first_element:
                lines.append("\n\n")
                line = f"G1 X{x_val} Y{y_val}; Y shift \n"
                lines.append(line)

                first_element = False
            else:
                line = f"G1 X{x_val} \n"
                lines.append(line)

            # add delay
            lines.append(f"G4 P{delay} \n")
            if add_M114:
                lines.append("M114_REALTIME R \n")
            lines.append(f"G4 P{delay} \n\n")

    return lines


dir = 'images/'
if not os.path.exists(dir):
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
        #self.cam = cv.VideoCapture("/webcam/?action=stream")
        self.stream = urllib.request.urlopen("http://192.168.101.39/webcam/?action=stream")
        self._logger.info("\n\n\nsaving gcode...\n\n\n")

    def get_settings_defaults(self):
     return dict(url=2, speed=1500, grids_num=10, z_offset=0.7)

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

    @octoprint.plugin.BlueprintPlugin.route("/gcode", methods=["GET"])
    def genGcode(self):
        self._logger.info("\n\n\nsaving gcode...\n\n\n")
        result = ""
        if "controls" in flask.request.values:
            gcode_params = flask.request.values["controls"]
            gcode_params = gcode_params.split(',')
            if True:
                try:
                    # self._logger.info(gcode_params)
                    filepath = "data/template_no_homing.gcode"
                    create_gcode_file(filepath, speed=int(gcode_params[0]), grids_num=int(gcode_params[1]),
                                      z_offset=float(gcode_params[2]), add_M114=True, delay=200)
                    result = flask.jsonify(
                        src="done"
                    )
                except IOError:
                    result = flask.jsonify(
                        error="Unable to open Webcam stream"
                    )
            # else:
            #     result = flask.jsonify(
            #         error="Unable to fetch image. Check octoprint log for details."
            #     )
            # self._printer.commands("M114")
        return flask.make_response(result, 200)

    @octoprint.plugin.BlueprintPlugin.route("/clear_folder", methods=["GET"])
    def clearFolder(self):
        self._logger.info("\n\n\n.saving gcode...\n\n\n")
        result = ""
        if True:
            try:
                self._logger.info("clear")
                dir = 'images/'
                if os.path.exists(dir):
                    shutil.rmtree(dir)
                os.makedirs(dir)
            except IOError:
                result = flask.jsonify(
                    error="Unable to open Webcam stream"
                )
        # else:
        #     result = flask.jsonify(
        #         error="Unable to fetch image. Check octoprint log for details."
        #     )
        # self._printer.commands("M114")
        return flask.make_response(result, 200)

    def get_img_stream(self):
        #ret, img = self.cam.read()
        ret = "_"
        bytes = b''
        bytes += self.stream.read(1024)
        a = bytes.find(b'\xff\xd8')  # frame starting
        b = bytes.find(b'\xff\xd9')  # frame ending
        if a != -1 and b != -1:
            jpg = bytes[a:b + 2]
            bytes = bytes[b + 2:]
            img = cv.imdecode(np.fromstring(jpg, dtype=np.uint8), 1)
            # cv.imshow('image', img)
            # if cv.waitKey(1) == 27:
            #     cv.destroyAllWindows()
            #     break
        # self.cam.release()
        return ret, img

    def parse_gcode_imsave(self, comm, line, *args, **kwargs):

        pattern = "X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
        result = re.findall(pattern, line)
        if len(result) == 1:
            ret, img = self.get_img_stream()
            im_name = f"images/img_X{result[0][0]}_Y{result[0][1]}_Z{result[0][2]}.jpg"
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

