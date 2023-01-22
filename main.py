
import os
from pathlib import Path
import json
# os.system("ngspice xnor_test.cir")


def make_test_skeleton(gate, drive, source_file):
    if gate == "fxor":
        if drive == "low":
            f = open("fxor_low_skeleton.txt", "w")
            f.write('')


# f = open("demofile2.txt", "w")
# f.write('Now the file has more content!')
# f.close()

# open and read the file after the appending:
# f = open("demofile2.txt", "r")
# print(f.read())

class Cell:
    def __init__(self, name, type, path, signature, pins):
        self.name = name
        self.path = path
        self.type = type
        self.signature = signature
        self.pins = pins


def parse_config(config_path):
    f = open(config_path)
    data = json.load(f)
    cells = []
    for cell_info in data:
        cells.append(Cell(cell_info['name'], cell_info['type'], cell_info['path'], cell_info['signature'], cell_info['pins']))
    f.close()
    return cells


def fill_measure_files(file_name, related_pin, other_pin, is_related_ris, is_out_ris, other_val):
    f = open(file_name, "w")
    out = "wrong_out"
    f.write(".include " + cell.path + "\n\n")
    for pin in cell.pins:
        if pin['type'] == 'input':
            if pin['name'] == related_pin:
                if is_related_ris:
                    f.write("Vin" + pin['name'] + " " + pin['name'] + " gnd 0 PWL(0 0 HIGHRAMPT 2.5)\n")
                else:
                    f.write("Vin" + pin['name'] + " " + pin['name'] + " gnd 2.5 PWL(0 2.5 LOWRAMPT 0)\n")
            elif pin['name'] == other_pin:
                f.write("Vin" + pin['name'] + " " + pin['name'] + " gnd " + str(other_val) + "\n")
        elif pin['type'] == 'power':
            f.write("VPower " + pin['name'] + " gnd 2.5\n")
        elif pin['type'] == 'output':
            out = pin['name']
    f.write('C1 ' + out + ' Gnd LOAD\n')
    f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
    f.write('.tran 10p 40n\n.control\nrun\n')
    if is_out_ris:
        f.write('\tmeas tran slew TRIG v(' + out +
                ') VAL=0.25 RISE=1 TARG v(' + out + ') VAL=2.25 RISE=1\n')
        if is_related_ris:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 RISE=1 TARG v(' +
                    out + ') VAL=1.25 RISE=1\n')
        else:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 FALL=1 TARG v(' +
                    out + ') VAL=1.25 RISE=1\n')
    else:
        f.write('\tmeas tran slew TRIG v(' + out +
                ') VAL=2.25 FALL=1 TARG v(' + out + ') VAL=0.25 FALL=1\n')
        if is_related_ris:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 RISE=1 TARG v(' +
                    out + ') VAL=1.25 FALL=1\n')
        else:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 FALL=1 TARG v(' +
                    out + ') VAL=1.25 FALL=1\n')
    f.write("\techo \"slew $&slew delay $&delay\" > out_meas.txt\n")
    f.write(".endc\n\n.end")
    f.close()


def make_skeleton_files(cell):
   for pin in cell.pins:
       if pin['type'] == 'output':
           for timing in pin['timing']:
               print(timing)
               if timing['timing_sense'] == 'binate':
                   if timing['binate_type'] == 'positive 0':
                       fname_in_ris_out_ris = 'skeleton_files/' + cell.name + '/' + timing['related_pin'] +\
                                              '_rising_' + timing['other_pin'] + '_0_skeleton.txt'
                       fname_in_ris_out_fal = 'skeleton_files/' + cell.name + '/' + timing['related_pin'] + \
                                              '_rising_' + timing['other_pin'] + '_1_skeleton.txt'
                       fname_in_fal_out_fal = 'skeleton_files/' + cell.name + '/' + timing['related_pin'] + \
                                              '_falling_' + timing['other_pin'] + '_0_skeleton.txt'
                       fname_in_fal_out_ris = 'skeleton_files/' + cell.name + '/' + timing['related_pin'] + \
                                              '_fallling_' + timing['other_pin'] + '_1_skeleton.txt'

                       fill_measure_files(fname_in_ris_out_ris, timing['related_pin'],
                                          timing['other_pin'], True, True, 0)
                       fill_measure_files(fname_in_ris_out_fal, timing['related_pin'],
                                          timing['other_pin'], True, False, 2.5)
                       fill_measure_files(fname_in_fal_out_fal, timing['related_pin'],
                                          timing['other_pin'], False, False, 0)
                       fill_measure_files(fname_in_fal_out_ris, timing['related_pin'],
                                          timing['other_pin'], False, True, 2.5)


config_path = "/home/znikolaos-g/VLSI/Project/Part2/config.json"
cells = parse_config(config_path)

try:
    os.mkdir('skeleton_files')
except FileExistsError:
    pass

try:
    os.mkdir('measure_files')
except FileExistsError:
    pass

try:
    os.mkdir('out_measure_files')
except FileExistsError:
    pass

for cell in cells:
    try:
        os.mkdir('skeleton_files/'+cell.name)
    except FileExistsError:
        pass
    try:
        os.mkdir('measure_files/'+cell.name)
    except FileExistsError:
        pass
    try:
        os.mkdir('out_measure_files/'+cell.name)
    except FileExistsError:
        pass
    make_skeleton_files(cell)
