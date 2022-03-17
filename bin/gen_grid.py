import numpy as np
import os


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
                lines.append("M114_REALTIME \n")
            lines.append(f"G4 P{delay} \n\n")

    return lines

import sys, getopt

import sys, getopt

def main(argv):
    z_offset = 0.7
    speed = 1500
    grids_num = 10
    try:
        opts, args = getopt.getopt(argv,"hs:g:z:",["speed=, grids_num=, zoffset="])
    except getopt.GetoptError:
        print ('usage: python bin/gen_grid.py -s <speed> -g <grids_num> -z <zoffset>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('usage: python bin/gen_grid.py -s <speed> -g <grids_num> -z <zoffset>')
            sys.exit()
        elif opt in ("-s", "--speed"):
            speed = arg
        elif opt in ("-g", "--grids_num"):
            grids_num = arg
        elif opt in ("-z", "--zoffset"):
            z_offset = arg

    filepath = "data/template.gcode"
    create_gcode_file(filepath, speed=int(speed), grids_num=int(grids_num), z_offset=float(z_offset),
                      add_M114=True, delay=200)


if __name__ == "__main__":
   main(sys.argv[1:])
