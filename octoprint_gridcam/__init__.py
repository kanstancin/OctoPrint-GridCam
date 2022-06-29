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
from time import sleep
from time import time

from img_diff_c9_integration import get_det_res, avg_imgs

# logging
from datetime import datetime

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
        self.stream = ''
        self.bytes = b''
        self.img = False
        self.im_counter = 0
        self.prev_im_counter = -1
        self.buffer_size = 0
        self.img_buffer = np.zeros((3, 10, 360, 480, 3)).astype(np.uint8)
        self.im_det = np.zeros((360, 480, 3)).astype(np.uint8)
        self.found_cntr = False

    def on_after_startup(self):
        self._logger.info("GridCam \n(more: %s)" % self._settings.get(["url"]))
        # self.cam = cv.VideoCapture(0)
        self.stream = urllib.request.urlopen("http://192.168.101.39/webcam/?action=stream")
        self._logger.info("\n\n\nsaving gcode...\n\n\n")

    def get_settings_defaults(self):
     return dict(url=2, speed=1500, grids_num=10, z_offset=0.7, gcode_corner_step=100)

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
        # ret, img = self.cam.read()
        img = cv.resize(img, (480, 360), interpolation=cv.INTER_AREA)
        self.img = img
        self.im_counter += 1
        # while (ret == False):
        #     ret, img = self.get_img_stream()
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

    @octoprint.plugin.BlueprintPlugin.route("/echo2", methods=["GET"])
    def sendProcessedImage(self):
        result = ""
        shape = self.im_det.shape[:2]
        res = 360
        dim = (int(res * shape[1] / shape[0]), res)
        img = cv.resize(self.im_det, dim, interpolation=cv.INTER_AREA)

        retval, buffer = cv.imencode('.jpg', img)

        if "imagetype" in flask.request.values:
            camera = flask.request.values["imagetype"]
            if camera in ("HEAD", "BIM"):
                if True:
                    # self._settings.get(["camera", camera.lower(), "path"])
                    try:
                        result = flask.jsonify(
                            src="data:image/{0};base64,{1}".format(
                                ".jpg",
                                str(base64.b64encode(buffer), "utf-8")),
                            det_res=self.found_cntr
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
                    gcode_filename = f"gcodes/grid_F{gcode_params[0]}_GRIDS{gcode_params[1]}_Z{gcode_params[2]}.gcode"
                    result = flask.jsonify(
                        src=gcode_filename
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

    @octoprint.plugin.BlueprintPlugin.route("/upload_static_file", methods=["GET", "POST"])
    def process_gcode_file(self):
        try:
            # get controls
            self._logger.info(f"\n\n\nprocessing gcode: ... \n\n\n")
            gcode_params = flask.request.values["controls"]
            gcode_params = gcode_params.split(',')
            step, filename, *_ = gcode_params

            # process file
            # data = flask.request.values["data"]
            data = flask.request.get_json()["text"]
            data = data.splitlines()
            self._logger.info(f"\n\n\nprocessing gcode:\n {data[:20]}... \n\n\n")
            data_out = self.addCornerCommandsGcode(data, int(step), offset_g28=100)

            # save file
            filename = os.path.splitext(filename)[0]
            filename_out = f"gcodes/{filename}_step{step}.gcode"
            with open(filename_out, 'w') as f:
                f.write('\n'.join(data_out))
            self._logger.info(f"saved gcode as '{filename_out}'")
            result = flask.jsonify(
                src=f"{filename_out}"
            )
        except Exception as e:
            result = flask.jsonify(
                error=f"{e}"
            )

        return result

    def addCornerCommandsGcode(self, txt, step, offset_g28=100):
        # txt.splitlines()
        # find G28 position
        g28_line_i = 200
        for line_i in range(len(txt[:1000][::-1])):
            if txt[line_i][:3] == 'G28':
                g28_line_i = line_i
                break
        line_i = g28_line_i + offset_g28
        while (line_i < len(txt)):
            cmd = ["", "G1 X340.0 Y340.0; Y shift; go to corner",
                   "G4 P500",
                   "M114_REALTIME R",
                   "G4 P500", ""]
            txt[line_i:line_i] = cmd
            line_i += step + len(cmd)
        return txt

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
                result = flask.jsonify(
                    src=""
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

    def get_img_stream(self):
        ret = False
        img = None
        while(ret == False):
            self.bytes += self.stream.read(1024)
            a = self.bytes.find(b'\xff\xd8')  # frame starting
            b = self.bytes.find(b'\xff\xd9')  # frame ending
            if a != -1 and b != -1:
                jpg = self.bytes[a:b + 2]
                self.bytes = self.bytes[b + 2:]
                img = cv.imdecode(np.fromstring(jpg, dtype=np.uint8), 1)
                img = cv.rotate(img, cv.ROTATE_180)
                ret = True
                self.stream = urllib.request.urlopen("http://192.168.101.39/webcam/?action=stream")
                # self.stream = urllib.request.urlopen("https://localhost:8888/videostream.cgi")
                self.bytes = b''
        return ret, img

    def parse_gcode_imsave(self, comm, line, *args, **kwargs):

        pattern = "X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
        result = re.findall(pattern, line)

        if len(result) == 1:
            img = self.img   # self.get_img_stream()
            im_name = f"images/img_X{result[0][0]}_Y{result[0][1]}_Z{result[0][2]}.jpg"
            cv.imwrite(im_name, img)
            # self._logger.info(line)
            self._logger.info(f"\nsaving image: {im_name}\n")
        # else:
        #     self._logger.info(line)
        return line


    def process_imgs(self, comm, line, *args, **kwargs):
        try:
            st = time()
            # take N images append them to M size array of imgs, make a call to im_diff processing func, send res to JS
            pattern = "X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
            result = re.findall(pattern, line)

            if len(result) == 1:
                self._logger.info(f"detected M114, entered hook function: \n\t{line}")
                # rotate buffer
                buff_len = self.img_buffer.shape[0]
                if self.buffer_size == buff_len:
                    self.img_buffer[:buff_len-1] = self.img_buffer[1:]
                # update queue
                for i in range(self.img_buffer.shape[1]):
                    # wait for new image
                    while self.prev_im_counter == self.im_counter:
                        sleep(0.01)
                    curr_im_buff_i = self.buffer_size - 1
                    if self.buffer_size < buff_len:
                        curr_im_buff_i = self.buffer_size
                    self.img_buffer[curr_im_buff_i, i, :, :, :] = self.img
                    self._logger.info(f"added image: {self.im_counter} to the buffer")
                    self.prev_im_counter = self.im_counter
                imgs = None
                if self.buffer_size >= 1 and self.buffer_size != buff_len:
                    imgs = self.img_buffer[self.buffer_size-1:self.buffer_size+1]
                elif self.buffer_size == buff_len:
                    imgs = self.img_buffer[-2:]
                if imgs is not None:
                    self.im_det, self.found_cntr = get_det_res(imgs, show=False)
                    # save imgs
                    # self.log_imgs(imgs, self.found_cntr)
                # update buffer size
                if self.buffer_size < buff_len:
                    self.buffer_size += 1
                # send two last imgs for processing

                # get im_res and state
                self._logger.info(f"finished processing, sent a resulting image")
                en = time()
                self._logger.info(f"'process_imgs' execution time: {en - st}s")
        except Exception as e:
            self._logger.info(f"error \t\n{e}")
        return line

    def log_imgs(self, buff, det_res):
        # save imgs
        im1 = avg_imgs(buff[-2, 0:5])
        im2 = avg_imgs(buff[-2, 5:])
        filename_img1 = os.path.join('logs', f"img_{self.prev_im_counter}_{self.get_timestamp()}_{str(int(det_res))}_1.jpg")
        filename_img2 = os.path.join('logs', f"img_{self.prev_im_counter}_{self.get_timestamp()}_{str(int(det_res))}_2.jpg")
        # np.save(filename_imgs, imgs[-1])
        cv.imwrite(filename_img1, im1)
        cv.imwrite(filename_img2, im2)

    def get_timestamp(self):
        time_ = datetime.now()
        return time_.strftime("%d-%m-%H:%M")



__plugin_name__ = "GridCam"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = GridCamPlugin()
__plugin_hooks__ = {
    "octoprint.comm.protocol.gcode.received": __plugin_implementation__.process_imgs
}

