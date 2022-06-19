



def addCornerCommandsGcode(txt, step, offset_g28=100):
    # txt.splitlines()
    # find G28 position
    g28_line_i = 200
    for line_i in range(len(txt[:1000][::-1])):
        if txt[line_i][:3] == 'G28':
            g28_line_i = line_i
            break
    line_i = g28_line_i + offset_g28
    while(line_i < len(txt)):
        cmd = ["", "G1 X340.0 Y340.0; Y shift; go to corner",
                "G4 P500",
                "M114_REALTIME R",
                "G4 P500", ""]
        txt[line_i:line_i] = cmd
        line_i += step + len(cmd)
    return txt

# test
filepath = "/home/cstar/workspace/OctoPrint-GridCam/gcodes/diamondx100.gcode"
with open(filepath) as f:
    lines = f.readlines()
lines = [line[:-1] for line in lines]
out = addCornerCommandsGcode(lines, 100)

out_fp = "/home/cstar/workspace/OctoPrint-GridCam/gcodes/test.gcode"
with open(out_fp, "w") as f:
    f.write('\n'.join(out))



