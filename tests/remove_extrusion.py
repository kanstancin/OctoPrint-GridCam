import re
import os

def removeExtr(gcode):
    pattern1 = "E"
    pattern2 = "S"
    res_gcode = []
    for line in gcode:
        res = re.search(pattern1, line)
        res2 = re.search(pattern2, line)
        if res2:
            continue
        if res:
            line = line[:res.start()]
        res_gcode.append(line)
    return res_gcode

def readFile(path):
    with open(path) as f:
        lines = f.readlines()
    lines = [line[:-1] for line in lines]
    return lines

def addCornerCommandsGcode(txt, step, offset_g28=100):
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
               "G4 P5000",
               "M114_REALTIME R",
               "G4 P5000", ""]
        txt[line_i:line_i] = cmd
        line_i += step + len(cmd)
    return txt

# filename = "PETG-Bracket (7).gcode"
# path = "/home/cstar/workspace/OctoPrint-GridCam/gcodes/" + filename
#
# gcode = readFile(path)
# # print(gcode)
# gcode = removeExtr(gcode)
# # print(gcode)
# filename_out = f"gcodes/{os.path.splitext(filename)[0]}_no_E.gcode"
# with open(filename_out, 'w') as f:
#     f.write('\n'.join(gcode))


filename = "PETG-Bracket (7)_no_E.gcode"
path = "/home/cstar/workspace/OctoPrint-GridCam/gcodes/" + filename
gcode = readFile(path)
gcode = addCornerCommandsGcode(gcode, 100, offset_g28=100)
filename_out = f"gcodes/{os.path.splitext(filename)[0]}_step100.gcode"
with open(filename_out, 'w') as f:
    f.write('\n'.join(gcode))
