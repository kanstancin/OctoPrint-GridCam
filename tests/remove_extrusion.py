import re


def removeExtr(gcode):
    pattern = "E"
    res_gcode = []
    for line in gcode:
        res = re.search(pattern, line)
        if res:
            line = line[:res.start()]
        res_gcode.append(line)
    return res_gcode

def readFile(path):
    with open(path) as f:
        lines = f.readlines()
    lines = [line[:-1] for line in lines]
    return lines

filename = "The-Twosquared-Towers (no densifier).gcode"
path = "/home/cstar/workspace/OctoPrint-GridCam/gcodes/" + filename

gcode = readFile(path)
# print(gcode)
gcode = removeExtr(gcode)
# print(gcode)
filename_out = f"gcodes/{filename}_no_E.gcode"
with open(filename_out, 'w') as f:
    f.write('\n'.join(gcode))