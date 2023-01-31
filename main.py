
import os
from pathlib import Path
import json
import shutil

def delete(path):
    """path could either be relative or absolute. """
    # check if file or directory exists
    if os.path.isfile(path) or os.path.islink(path):
        # remove file
        os.remove(path)
    elif os.path.isdir(path):
        # remove directory and all its content
        shutil.rmtree(path)
    else:
        raise ValueError("Path {} is not a file or dir.".format(path))


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


def fill_skeleton_files(cell, file_name, related_pin, other_pin, is_related_ris, is_out_ris, other_val):
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
    f.write('.tran 50p 100n\n.control\nrun\n')
    if is_out_ris:
        f.write('\tmeas tran slew TRIG v(' + out +
                ') VAL=0.75 RISE=1 TARG v(' + out + ') VAL=1.75 RISE=1\n')
        if is_related_ris:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 RISE=1 TARG v(' +
                    out + ') VAL=1.25 RISE=1\n')
        else:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 FALL=1 TARG v(' +
                    out + ') VAL=1.25 RISE=1\n')
    else:
        f.write('\tmeas tran slew TRIG v(' + out +
                ') VAL=1.75 FALL=1 TARG v(' + out + ') VAL=0.75 FALL=1\n')
        if is_related_ris:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 RISE=1 TARG v(' +
                    out + ') VAL=1.25 FALL=1\n')
        else:
            f.write('\tmeas tran delay TRIG v(' + related_pin + ') VAL=1.25 FALL=1 TARG v(' +
                    out + ') VAL=1.25 FALL=1\n')
    f.write("\techo \"slew $&slew delay $&delay\" > out_meas.txt\n")
    f.write("\tquit\n.endc\n\n.end")
    f.close()


def copy_file_to_file(source_file, dest_file):
    for line in source_file:
        dest_file.write(line)


def fill_measure_files_con(sub_name, related_slews, constrained_slews, con_type):
    if con_type == 'setup' or con_type == 'hold':
        f_skeleton = open('skeleton_files/' + sub_name + '_skeleton.txt', "r")
        skeleton_data = f_skeleton.read()
        f_skeleton.close()

        for related_slew in related_slews:
            for constrained_slew in constrained_slews:
                f_measure = open('measure_files/' + sub_name + '_' + str(related_slew) + '_' + str(constrained_slew) + '_.txt', "w")
                d_start_end = constrained_slew/0.4
                c_start_end = related_slew/0.4

                measure_data = skeleton_data.replace("D_START_END", str(d_start_end)+'n')
                measure_data = measure_data.replace("C_START_END", str(c_start_end) + 'n')

                f_measure.write(measure_data)
                f_measure.close()
    elif con_type == 'recovery' or con_type == 'removal':
        f_skeleton = open('skeleton_files/' + sub_name + '_skeleton.txt', "r")
        skeleton_data = f_skeleton.read()
        f_skeleton.close()

        for related_slew in related_slews:
            for constrained_slew in constrained_slews:
                f_measure = open(
                    'measure_files/' + sub_name + '_' + str(related_slew) + '_' + str(constrained_slew) + '_.txt', "w")
                a_start_end = constrained_slew / 0.4
                c_start_end = related_slew / 0.4

                measure_data = skeleton_data.replace("A_START_END", str(a_start_end) + 'n')
                measure_data = measure_data.replace("C_START_END", str(c_start_end) + 'n')

                f_measure.write(measure_data)
                f_measure.close()


def fill_measure_files(sub_name, source_slews, loads, is_related_ris):
    f_skeleton = open('skeleton_files/' + sub_name + '_skeleton.txt', "r")
    skeleton_data = f_skeleton.read()
    f_skeleton.close()

    for source_slew in source_slews:
        for load in loads:
            f_measure = open('measure_files/' + sub_name + '_' + str(source_slew)
                             + '_' + str(load) + '_.txt', "w")
            t1 = source_slew/0.4
            if is_related_ris:
                measure_data = skeleton_data.replace("HIGHRAMPT", str(t1)+'n')
            else:
                measure_data = skeleton_data.replace("LOWRAMPT", str(t1)+'n')
            measure_data = measure_data.replace("LOAD", str(load)+'p')
            measure_data = measure_data.replace("out_meas.txt", "out_measure_files/"+ sub_name + "_" + str(source_slew)
                             + '_' + str(load) + '_meas.txt')
            f_measure.write(measure_data)
            f_measure.close()


def make_measure_files(cell):
    if cell.type == 'combinational':
        for pin in cell.pins:
            if pin['type'] == 'output':
                for timing in pin['timing']:
                    print(timing)
                    if timing['timing_sense'] == 'binate':
                        if timing['binate_type'] == 'positive 0':
                            fname_in_ris_out_ris = cell.name + '/timing_' + timing['related_pin'] + '_rising_' +\
                                                   timing['other_pin'] + '_0_' + pin['name'] + '_rising'
                            fname_in_ris_out_fal = cell.name + '/timing_' + timing['related_pin'] + \
                                                   '_rising_' + timing['other_pin'] + '_1_' + pin['name'] + '_falling'
                            fname_in_fal_out_fal = cell.name + '/timing_' + timing['related_pin'] + \
                                                   '_falling_' + timing['other_pin'] + '_0_' + pin['name'] + '_falling'
                            fname_in_fal_out_ris = cell.name + '/timing_' + timing['related_pin'] + \
                                                   '_falling_' + timing['other_pin'] + '_1_' + pin['name'] + '_rising'
                        elif timing['binate_type'] == 'negative 0':
                            fname_in_ris_out_ris = cell.name + '/timing_'  + timing['related_pin'] + \
                                                   '_rising_' + timing['other_pin'] + '_1_' + pin['name'] + '_rising'
                            fname_in_ris_out_fal = cell.name + '/timing_'  + timing['related_pin'] + \
                                                   '_rising_' + timing['other_pin'] + '_0_' + pin['name'] + '_falling'
                            fname_in_fal_out_fal = cell.name + '/timing_'  + timing['related_pin'] + \
                                                   '_falling_' + timing['other_pin'] + '_1_' + pin['name'] + '_falling'
                            fname_in_fal_out_ris = cell.name + '/timing_'  + timing['related_pin'] + \
                                                   '_falling_' + timing['other_pin'] + '_0_' + pin['name'] + '_rising'

                        loads = [float(load) for load in timing['loads']]
                        source_slews = [float(source_slew) for source_slew in timing['source_slews']]
                        fill_measure_files(fname_in_ris_out_ris, source_slews, loads, True)
                        fill_measure_files(fname_in_ris_out_fal, source_slews, loads, True)
                        fill_measure_files(fname_in_fal_out_fal, source_slews, loads, False)
                        fill_measure_files(fname_in_fal_out_ris, source_slews, loads, False)
    else:
        for pin in cell.pins:
            if pin['type'] == 'input':
                for timing in pin['timing']:
                    if timing['type'] == 'setup_rising':
                        fname_setup_rise = cell.name + '/setup/rise/' + cell.name
                        fname_setup_fall = cell.name + '/setup/fall/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_setup_rise, related_slews, constrained_slews, 'setup')
                        fill_measure_files_con(fname_setup_fall, related_slews, constrained_slews, 'setup')
                    elif timing['type'] == 'hold_rising':
                        fname_hold_rise = cell.name + '/hold/rise/' + cell.name
                        fname_hold_fall = cell.name + '/hold/fall/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_hold_rise, related_slews, constrained_slews, 'hold')
                        fill_measure_files_con(fname_hold_fall, related_slews, constrained_slews, 'hold')
            elif pin['type'] == 'preset':
                for timing in pin['timing']:
                    if timing['type'] == 'recovery_rising':
                        fname_recovery = cell.name + '/recovery/set/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_recovery, related_slews, constrained_slews, 'recovery')
                    elif timing['type'] == 'removal_rising':
                        fname_removal = cell.name + '/removal/set/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_removal, related_slews, constrained_slews, 'removal')
            elif pin['type'] == 'clear':
                for timing in pin['timing']:
                    if timing['type'] == 'recovery_rising':
                        fname_recovery = cell.name + '/recovery/clear/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_recovery, related_slews, constrained_slews, 'recovery')
                    elif timing['type'] == 'removal_rising':
                        fname_removal = cell.name + '/removal/clear/' + cell.name
                        related_slews = [float(slew) for slew in timing['related_slew']]
                        constrained_slews = [float(slew) for slew in timing['constrained_slew']]
                        fill_measure_files_con(fname_removal, related_slews, constrained_slews, 'removal')


def fill_skeleton_setup_hold(cell, file_name, constraint, is_rising):
    f = open(file_name, "w")
    f.write(".include " + cell.path + "\n\n")
    f.write(".param td_start = D_START\n")
    f.write(".param td_start_end = D_START_END\n")
    f.write(".param td_end = {td_start + td_start_end}\n")
    f.write(".param tc_start = 20n\n")
    f.write(".param tc_start_end = C_START_END\n")
    f.write(".param tc_end = {tc_start + tc_start_end}\n\n")
    out_q = 'wrong_output'
    out_qm = 'wrong_output'

    if constraint == "setup":
        if is_rising:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 0 PWL(0 0 td_start 0 td_end 2.5)\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=0.75 RISE=1 TARG v('+out_q+
                    ') VAL=1.75 RISE=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
        else:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 2.5 PWL(0 2.5 td_start 2.5 td_end 0)\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=1.75 FALL=1 TARG v('+out_q+
                    ') VAL=0.75 FALL=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
    elif constraint == 'hold':
        if not is_rising:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 0 PWL(0 0 td_start 0 td_end 2.5)\n')
                elif pin['type'] == 'preset':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + " Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=1.75 FALL=1 TARG v('+out_q+
                    ') VAL=0.75 FALL=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
        else:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 2.5 PWL(0 2.5 td_start 2.5 td_end 0)\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'clear':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + " Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=0.75 RISE=1 TARG v('+out_q+
                    ') VAL=1.75 RISE=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
    f.close()


def fill_skeleton_recovery_removal(cell, file_name, constraint, is_preset):
    f = open(file_name, "w")
    f.write(".include " + cell.path + "\n\n")
    f.write(".param ta_start = A_START\n")
    f.write(".param ta_start_end = A_START_END\n")
    f.write(".param ta_end = {ta_start + ta_start_end}\n")
    f.write(".param tc_start = 20n\n")
    f.write(".param tc_start_end = C_START_END\n")
    f.write(".param tc_end = {tc_start + tc_start_end}\n\n")
    out_q = 'wrong_output'
    out_qm = 'wrong_output'

    if constraint == "recovery":
        if is_preset:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 0\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 2.5 PWL(0 2.5 ta_start 2.5 ta_end 0)\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=1.75 FALL=1 TARG v('+out_q+
                    ') VAL=0.75 FALL=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
        else:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 2.5\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 2.5 PWL(0 2.5 ta_start 2.5 ta_end 0)\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=0.75 RISE=1 TARG v('+out_q+
                    ') VAL=1.75 RISE=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
    elif constraint == 'removal':
        if not is_preset:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 0\n')
                elif pin['type'] == 'preset':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + " Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0 ta_start 0 ta_end 2.5)\n")
                elif pin['type'] == 'clear':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=1.75 FALL=1 TARG v('+out_q+
                    ') VAL=0.75 FALL=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')
        else:
            for pin in cell.pins:
                if pin['type'] == 'input':
                    f.write("V"+pin['name']+' '+pin['name']+' Gnd 2.5\n')
                elif pin['type'] == 'preset':
                    f.write("V"+pin['name']+' '+pin['name']+" Gnd 0\n")
                elif pin['type'] == 'clear':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + " Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0 ta_start 0 ta_end 2.5)\n")
                elif pin['type'] == 'power':
                    f.write("Vpower "+pin['name']+" Gnd 2.5\n")
                elif pin['type'] == 'clock':
                    f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 tc_start 0 tc_end 2.5)\n')
                elif pin['type'] == 'output':
                    if pin['function'] == 'IQ':
                        out_q = pin['name']
                    elif pin['function'] == 'IQN':
                        out_qm = pin['name']
            f.write('C1 ' + out_q + ' Gnd 10f\n')
            f.write('C2 ' + out_qm + ' Gnd 10f\n')
            f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
            f.write('.tran 50p 100n\n.control\n\tlet slew=0\n\trun\n\tmeas tran slew TRIG v('+
                    out_q+') VAL=0.75 RISE=1 TARG v('+out_q+
                    ') VAL=1.75 RISE=1\n\techo \"$&slew\" > TEMP_OUT.txt\n\tquit\n.endc\n\n.end')

    f.close()


def fill_skeleton_timing_seq(cell, file_name, function, related, input_type, d_val, c_val, s_val, r_val):
    f = open(file_name, "w")
    f.write(".include " + cell.path + "\n\n")
    out_q = 'wrong_output'
    out_qm = 'wrong_output'
    inp = 'wrong_input'

    if function == 'IQ':
        if related == 'clock':
            if input_type == 'pos':
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vpower "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
                        inp = pin['name']
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_q + ') VAL=0.75 RISE=1 TARG v(' + out_q +
                        ') VAL=1.75 RISE=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_q
                        +') VAL = 1.25 RISE=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
            elif input_type == 'zero':
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0\n')
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vpower "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
                        inp = pin['name']
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_q + ') VAL=1.75 FALL=1 TARG v(' + out_q +
                        ') VAL=0.75 FALL=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_q
                        +') VAL = 1.25 FALL=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
        elif related == 'set':
            if r_val == 0:
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + d_val + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 0)\n')
                        inp = pin['name']
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vpower "+pin['name']+" Gnd " + c_val + "\n")
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_q + ') VAL=0.75 RISE=1 TARG v(' + out_q +
                        ') VAL=1.75 RISE=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_q
                        +') VAL = 1.25 RISE=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
        elif related == 'clear':
            if s_val == 0:
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + d_val + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 0)\n')
                        inp = pin['name']
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vpower "+pin['name']+" Gnd " + c_val +"\n")
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_q + ') VAL=1.75 FALL=1 TARG v(' + out_q +
                        ') VAL=0.75 FALL=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_q
                        +') VAL = 1.25 FALL=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
            else:
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + d_val + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 0)\n')
                        inp = pin['name']
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vpower "+pin['name']+" Gnd " + c_val + "\n")
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew_fall TRIG v(' +
                         out_q + ') VAL=1.75 FALL=1 TARG v(' + out_q +
                        ') VAL=0.75 FALL=1\n\tmeas tran delay_fall TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_q
                        +') VAL = 1.25 FALL=1\n\tmeas tran slew_rise TRIG v(' +
                        out_q + ') VAL=0.75 RISE=1 TARG v(' + out_q +
                        ') VAL=1.75 RISE=1\n\tmeas tran delay_rise TRIG(' +
                        inp + ') VAL=1.25 FALL=1 TARG v(' +
                        out_q +') VAL=1.25 RISE=1\n\techo \"slew_fall $&slew_fall delay_fall $&delay_fall slew_rise $&slew_rise delay_rise $&delay_rise\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')

    f.close()

def make_skeleton_files(cell):
    if cell.type == 'combinational':
       for pin in cell.pins:
           if pin['type'] == 'output':
               for timing in pin['timing']:
                   if timing['timing_sense'] == 'binate':
                       if timing['binate_type'] == 'positive 0':
                           fname_in_ris_out_ris = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] +\
                                                  '_rising_' + timing['other_pin'] + '_0_' + pin['name'] + '_rising_skeleton.txt'
                           fname_in_ris_out_fal = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_rising_' + timing['other_pin'] + '_1_' + pin['name'] + '_falling_skeleton.txt'
                           fname_in_fal_out_fal = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_falling_' + timing['other_pin'] + '_0_' + pin['name'] + '_falling_skeleton.txt'
                           fname_in_fal_out_ris = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_falling_' + timing['other_pin'] + '_1_' + pin['name'] + '_rising_skeleton.txt'

                           fill_skeleton_files(cell, fname_in_ris_out_ris, timing['related_pin'],
                                              timing['other_pin'], True, True, 0)
                           fill_skeleton_files(cell, fname_in_ris_out_fal, timing['related_pin'],
                                              timing['other_pin'], True, False, 2.5)
                           fill_skeleton_files(cell ,fname_in_fal_out_fal, timing['related_pin'],
                                              timing['other_pin'], False, False, 0)
                           fill_skeleton_files(cell, fname_in_fal_out_ris, timing['related_pin'],
                                              timing['other_pin'], False, True, 2.5)
                       elif timing['binate_type'] == 'negative 0':
                           fname_in_ris_out_ris = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_rising_' + timing['other_pin'] + '_1_' + pin['name'] + '_rising_skeleton.txt'
                           fname_in_ris_out_fal = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_rising_' + timing['other_pin'] + '_0_' + pin['name'] + '_falling_skeleton.txt'
                           fname_in_fal_out_fal = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_falling_' + timing['other_pin'] + '_1_' + pin['name'] + '_falling_skeleton.txt'
                           fname_in_fal_out_ris = 'skeleton_files/' + cell.name + '/timing_' + timing['related_pin'] + \
                                                  '_falling_' + timing['other_pin'] + '_0_' + pin['name'] + '_rising_skeleton.txt'

                           fill_skeleton_files(cell, fname_in_ris_out_ris, timing['related_pin'],
                                              timing['other_pin'], True, True, 2.5)
                           fill_skeleton_files(cell, fname_in_ris_out_fal, timing['related_pin'],
                                              timing['other_pin'], True, False, 0)
                           fill_skeleton_files(cell, fname_in_fal_out_fal, timing['related_pin'],
                                              timing['other_pin'], False, False, 2.5)
                           fill_skeleton_files(cell, fname_in_fal_out_ris, timing['related_pin'],
                                              timing['other_pin'], False, True, 0)
    else:
        for pin in cell.pins:
            if pin['type'] == 'input':
                for timing in pin['timing']:
                    if timing['type'] == "setup_rising":
                        #print(pin['name'])
                        fname_setup_rising_rise = 'skeleton_files/' + cell.name + '/setup/rise/' + cell.name + '_skeleton.txt'
                        fname_setup_rising_fall = 'skeleton_files/' + cell.name + '/setup/fall/' + cell.name + '_skeleton.txt'
                        fill_skeleton_setup_hold(cell, fname_setup_rising_rise, "setup", True)
                        fill_skeleton_setup_hold(cell, fname_setup_rising_fall, "setup", False)
                    elif timing['type'] == "hold_rising":
                        fname_hold_rising_rise = 'skeleton_files/' + cell.name + '/hold/rise/' + cell.name + '_skeleton.txt'
                        fname_hold_rising_fall = 'skeleton_files/' + cell.name + '/hold/fall/' + cell.name + '_skeleton.txt'
                        fill_skeleton_setup_hold(cell, fname_hold_rising_rise, "hold", True)
                        fill_skeleton_setup_hold(cell, fname_hold_rising_fall, "hold", False)
            elif pin['type'] == 'preset':
                for timing in pin['timing']:
                    if timing['type'] == 'recovery_rising':
                        fname_recovery = 'skeleton_files/' + cell.name + '/recovery/set/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_recovery, 'recovery', True)
                    elif timing['type'] == 'removal_rising':
                        fname_removal = 'skeleton_files/' + cell.name + '/removal/set/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_removal, 'removal', True)
            elif pin['type'] == 'clear':
                for timing in pin['timing']:
                    if timing['type'] == 'recovery_rising':
                        print("Hiho")
                        fname_recovery = 'skeleton_files/' + cell.name + '/recovery/clear/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_recovery, 'recovery', False)
                    elif timing['type'] == 'removal_rising':
                        fname_removal = 'skeleton_files/' + cell.name + '/removal/clear/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_removal, 'removal', False)
            elif pin['type'] == 'output':
                if pin['function'] == 'IQ':
                    for timing in pin['timing']:
                        print(timing)
                        if timing['type'] == 'rising_edge':
                            fname_pos_input = 'skeleton_files/' + cell.name + '/timing/out/rel_clock/pos/' + cell.name + '_skeleton.txt'
                            fname_neg_input = 'skeleton_files/' + cell.name + '/timing/out/rel_clock/zero/' + cell.name + '_neg_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_pos_input, 'IQ', 'clock', 'pos', 1, 1, 1, 1)
                            fill_skeleton_timing_seq(cell, fname_neg_input, 'IQ', 'clock', 'zero', 1, 1, 1, 1)



def run_setup(cell):
    max_iter = 10000
    step = 0.1
    tc_start = 20
    td_init = 6

    meas_setup_rise_files = os.listdir("measure_files/" + cell.name + "/setup/rise/")
    meas_setup_fall_files = os.listdir("measure_files/" + cell.name + "/setup/fall/")

    for file in meas_setup_rise_files:
        f_meas = open("measure_files/"+cell.name+"/setup/rise/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew)/0.4
        constrained_start_end = float(constrained_slew)/0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('D_START', str(td_init + i*step)+'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                setup_rise = tc_start + related_start_end/2 - (td_init + i*step + constrained_start_end/2)
                if setup_rise > 0:
                    setup_rise *= 1.05
                else:
                    setup_rise *= 0.95
                f_meas_out = open("out_measure_files/"+cell.name + "/setup/rise/" + file, 'w')
                f_meas_out.write(str(setup_rise))
                f_meas_out.close()
                break

    for file in meas_setup_fall_files:
        f_meas = open("measure_files/" + cell.name + "/setup/fall/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('D_START', str(td_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                setup_fall = tc_start + related_start_end/2- (td_init + i*step + constrained_start_end/2)
                if setup_fall > 0:
                    setup_fall *= 1.05
                else:
                    setup_fall *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/setup/fall/" + file, 'w')
                f_meas_out.write(str(setup_fall))
                f_meas_out.close()
                break


def run_hold(cell):
    max_iter = 10000
    step = -0.1
    tc_start = 20
    td_init = 24

    meas_setup_rise_files = os.listdir("measure_files/" + cell.name + "/hold/rise/")
    meas_setup_fall_files = os.listdir("measure_files/" + cell.name + "/hold/fall/")

    for file in meas_setup_rise_files:
        f_meas = open("measure_files/" + cell.name + "/hold/rise/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('D_START', str(td_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                hold_rise = -tc_start - related_start_end / 2 + (td_init + i * step + constrained_start_end / 2)
                if hold_rise > 0:
                    hold_rise *= 1.05
                else:
                    hold_rise *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/hold/rise/" + file, 'w')
                f_meas_out.write(str(hold_rise))
                f_meas_out.close()
                break

    for file in meas_setup_fall_files:
        f_meas = open("measure_files/" + cell.name + "/hold/fall/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('D_START', str(td_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                hold_fall = -tc_start - related_start_end / 2 + (td_init + i * step + constrained_start_end / 2)
                if hold_fall > 0:
                    hold_fall *= 1.05
                else:
                    hold_fall *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/hold/fall/" + file, 'w')
                f_meas_out.write(str(hold_fall))
                f_meas_out.close()
                break


def run_recovery(cell):
    max_iter = 10000
    step = 0.1
    tc_start = 20
    ta_init = 15

    meas_recovery_set_files = os.listdir("measure_files/" + cell.name + "/recovery/set/")
    meas_recovery_clear_files = os.listdir("measure_files/" + cell.name + "/recovery/clear/")

    for file in meas_recovery_set_files:
        f_meas = open("measure_files/" + cell.name + "/recovery/set/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('A_START', str(ta_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                recovery_set = tc_start + related_start_end / 2 - (ta_init + i * step + constrained_start_end / 2)
                if recovery_set > 0:
                    recovery_set *= 1.05
                else:
                    recovery_set *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/recovery/set/" + file, 'w')
                f_meas_out.write(str(recovery_set))
                f_meas_out.close()
                break

    for file in meas_recovery_clear_files:
        f_meas = open("measure_files/" + cell.name + "/recovery/clear/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('A_START', str(ta_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                recovery_clear = tc_start + related_start_end / 2 - (ta_init + i * step + constrained_start_end / 2)
                if recovery_clear > 0:
                    recovery_clear *= 1.05
                else:
                    recovery_clear *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/recovery/clear/" + file, 'w')
                f_meas_out.write(str(recovery_clear))
                f_meas_out.close()
                break


def run_removal(cell):
    max_iter = 10000
    step = -0.1
    tc_start = 20
    ta_init = 35

    meas_removal_set_files = os.listdir("measure_files/" + cell.name + "/removal/set/")
    meas_removal_clear_files = os.listdir("measure_files/" + cell.name + "/removal/clear/")

    for file in meas_removal_set_files:
        f_meas = open("measure_files/" + cell.name + "/removal/set/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('A_START', str(ta_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                removal_set = -tc_start - related_start_end / 2 + (ta_init + i * step + constrained_start_end / 2)
                if removal_set > 0:
                    removal_set *= 1.05
                else:
                    removal_set *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/removal/set/" + file, 'w')
                f_meas_out.write(str(removal_set))
                f_meas_out.close()
                break

    for file in meas_removal_clear_files:
        f_meas = open("measure_files/" + cell.name + "/removal/clear/" + file, 'r')
        meas_data = f_meas.read()
        f_meas.close()
        file_name_list = file.split('_')
        related_slew = file_name_list[-3]
        constrained_slew = file_name_list[-2]
        related_start_end = float(related_slew) / 0.4
        constrained_start_end = float(constrained_slew) / 0.4

        for i in range(max_iter):
            f_temp = open("meas_con_temp.spice", 'w')
            temp_data = meas_data.replace('A_START', str(ta_init + i * step) + 'n')
            f_temp.write(temp_data)
            f_temp.close()
            os.system("ngspice meas_con_temp.spice > suppress.txt")
            f_temp_out = open("TEMP_OUT.txt", 'r')
            temp_out_data = f_temp_out.read()
            f_temp_out.close()
            if temp_out_data == '0\n':
                removal_clear = -tc_start - related_start_end / 2 + (ta_init + i * step + constrained_start_end / 2)
                if removal_clear > 0:
                    removal_clear *= 1.05
                else:
                    removal_clear *= 0.95
                f_meas_out = open("out_measure_files/" + cell.name + "/removal/clear/" + file, 'w')
                f_meas_out.write(str(removal_clear))
                f_meas_out.close()
                break


config_path = "/home/znikolaos-g/VLSI/Project/Part2/config.json"
cells = parse_config(config_path)

try:
    delete('skeleton_files')
    delete('measure_files')
    delete('out_measure_files')
except ValueError:
    print('Running for the first time!')
    pass

try:
    os.mkdir('skeleton_files')
    os.mkdir('measure_files')
    os.mkdir('out_measure_files')
except FileExistsError:
    print('Warning: some files already exist!\n')
    pass

for cell in cells:
    try:
        os.mkdir('skeleton_files/'+cell.name)
        os.mkdir('measure_files/' + cell.name)
        os.mkdir('out_measure_files/' + cell.name)
    except FileExistsError:
        print('Warning: some files already exist!\n')
        pass

    if cell.type == 'sequential':
        try:
            os.mkdir('skeleton_files/' + cell.name + '/setup')
            os.mkdir('skeleton_files/' + cell.name + '/setup/rise')
            os.mkdir('skeleton_files/' + cell.name + '/setup/fall')
            os.mkdir('skeleton_files/' + cell.name + '/hold')
            os.mkdir('skeleton_files/' + cell.name + '/hold/rise')
            os.mkdir('skeleton_files/' + cell.name + '/hold/fall')
            os.mkdir('skeleton_files/' + cell.name + '/recovery')
            os.mkdir('skeleton_files/' + cell.name + '/recovery/set')
            os.mkdir('skeleton_files/' + cell.name + '/recovery/clear')
            os.mkdir('skeleton_files/' + cell.name + '/removal')
            os.mkdir('skeleton_files/' + cell.name + '/removal/set')
            os.mkdir('skeleton_files/' + cell.name + '/removal/clear')
            os.mkdir('skeleton_files/' + cell.name + '/timing')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clock')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clock/pos')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clock/zero')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_set')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_set/dn_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_set/dn_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_set/d_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_set/d_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_cn_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_c_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_cn_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_c_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clock')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clock/pos')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clock/zero')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_set')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_set/dn_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_set/dn_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_set/d_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_set/d_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_c_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_cn_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_cn_r')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_c_rn')
            os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_c_r')

            os.mkdir('measure_files/' + cell.name + '/setup')
            os.mkdir('measure_files/' + cell.name + '/setup/rise')
            os.mkdir('measure_files/' + cell.name + '/setup/fall')
            os.mkdir('measure_files/' + cell.name + '/hold')
            os.mkdir('measure_files/' + cell.name + '/hold/rise')
            os.mkdir('measure_files/' + cell.name + '/hold/fall')
            os.mkdir('measure_files/' + cell.name + '/recovery')
            os.mkdir('measure_files/' + cell.name + '/recovery/set')
            os.mkdir('measure_files/' + cell.name + '/recovery/clear')
            os.mkdir('measure_files/' + cell.name + '/removal')
            os.mkdir('measure_files/' + cell.name + '/removal/set')
            os.mkdir('measure_files/' + cell.name + '/removal/clear')
            os.mkdir('measure_files/' + cell.name + '/timing')
            os.mkdir('measure_files/' + cell.name + '/timing/out')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clock')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clock/pos')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clock/zero')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_set')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_set/dn_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_set/dn_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_set/d_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_set/d_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_r')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_r')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_r')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_c_r')
            os.mkdir('measure_files/' + cell.name + '/timing/outn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clock')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clock/pos')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clock/zero')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_set')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_set/dn_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_set/dn_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_set/d_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_set/d_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_r')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_r')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_r')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_rn')
            os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_r')

            os.mkdir('out_measure_files/' + cell.name + '/setup')
            os.mkdir('out_measure_files/' + cell.name + '/setup/rise')
            os.mkdir('out_measure_files/' + cell.name + '/setup/fall')
            os.mkdir('out_measure_files/' + cell.name + '/hold')
            os.mkdir('out_measure_files/' + cell.name + '/hold/rise')
            os.mkdir('out_measure_files/' + cell.name + '/hold/fall')
            os.mkdir('out_measure_files/' + cell.name + '/recovery')
            os.mkdir('out_measure_files/' + cell.name + '/recovery/set')
            os.mkdir('out_measure_files/' + cell.name + '/recovery/clear')
            os.mkdir('out_measure_files/' + cell.name + '/removal')
            os.mkdir('out_measure_files/' + cell.name + '/removal/set')
            os.mkdir('out_measure_files/' + cell.name + '/removal/clear')
            os.mkdir('out_measure_files/' + cell.name + '/timing')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clock')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clock/pos')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clock/zero')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_set')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_set/dn_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_set/dn_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_set/d_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_set/d_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_c_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clock')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clock/pos')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clock/zero')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_set')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_set/dn_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_set/dn_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_set/d_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_set/d_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_r')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_rn')
            os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_r')
        except FileExistsError:
            print('Warning: some files already exist!\n')
            pass


    make_skeleton_files(cell)
    make_measure_files(cell)


for cell in cells:
    if cell.type == 'sequential':
        #run_setup(cell)
        #run_hold(cell)
        #run_recovery(cell)
        #run_removal(cell)
        print("hi")


#spice_dirs = os.listdir("measure_files/")

#for spice_dir in spice_dirs:
#    spice_files = os.listdir("measure_files/"+spice_dir+'/')
#    for spice_file in spice_files:
#        if os.path.isfile("measure_files/"+spice_dir+"/"+spice_file):
#            # for combinational gates
#            os.system("ngspice "+"measure_files/"+spice_dir+"/"+spice_file)
