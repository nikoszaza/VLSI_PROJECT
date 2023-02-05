
import os
from pathlib import Path
import json
import shutil
import sys

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
    def __init__(self, name, type, path, signature, pins, drive='X1'):
        self.name = name
        self.path = path
        self.type = type
        self.signature = signature
        self.pins = pins
        self.drive = drive


def parse_config(config_path):
    f = open(config_path)
    data = json.load(f)
    cells = []
    for cell_info in data:
        cells.append(Cell(cell_info['name'], cell_info['type'], cell_info['path'], cell_info['signature'], cell_info['pins'], cell_info['drive']))
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


def fill_measure_files_tim_seq(sub_name, source_slews, loads):
    f_skeleton = open('skeleton_files/' + sub_name + '_skeleton.txt', "r")
    skeleton_data = f_skeleton.read()
    f_skeleton.close()

    for source_slew in source_slews:
        for load in loads:
            f_measure = open('measure_files/' + sub_name + '_' + str(source_slew)
                             + '_' + str(load) + '_.txt', "w")
            t1 = source_slew / 0.4 + 20
            measure_data = skeleton_data.replace("T_END", str(t1) + 'n')
            measure_data = measure_data.replace("LOAD", str(load) + 'p')
            measure_data = measure_data.replace("MEAS_OUT.txt", "out_measure_files/" + sub_name + "_" + str(source_slew)
                                                + '_' + str(load) + '_meas.txt')
            f_measure.write(measure_data)
            f_measure.close()


def make_measure_files(cell):
    if cell.type == 'combinational':
        for pin in cell.pins:
            if pin['type'] == 'output':
                for timing in pin['timing']:
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
            elif pin['type'] == 'output':
                if pin['function'] == 'IQ':
                    for timing in pin['timing']:
                        loads = [float(load) for load in timing['loads']]
                        source_slews = [float(source_slew) for source_slew in timing['source_slews']]
                        if timing['related_pin'] == 'CLK':
                            fname_timing = cell.name + '/timing/out/rel_clock/pos/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_clock/zero/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                        elif timing['related_pin'] == 'R':
                            fname_timing = cell.name + '/timing/out/rel_clear/d_c_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_clear/d_cn_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_clear/dn_c_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_clear/dn_cn_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                        elif timing['related_pin'] == 'S':
                            fname_timing = cell.name + '/timing/out/rel_set/d_c_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_set/d_cn_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_set/dn_c_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/out/rel_set/dn_cn_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                elif pin['function'] == 'IQN':
                    for timing in pin['timing']:
                        loads = [float(load) for load in timing['loads']]
                        source_slews = [float(source_slew) for source_slew in timing['source_slews']]
                        if timing['related_pin'] == 'CLK':
                            fname_timing = cell.name + '/timing/outn/rel_clock/pos/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_clock/zero/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                        elif timing['related_pin'] == 'R':
                            fname_timing = cell.name + '/timing/outn/rel_clear/d_c_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_clear/d_cn_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_clear/dn_c_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_clear/dn_cn_sn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                        elif timing['related_pin'] == 'S':
                            fname_timing = cell.name + '/timing/outn/rel_set/d_c_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_set/d_cn_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_set/dn_c_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)
                            fname_timing = cell.name + '/timing/outn/rel_set/dn_cn_rn/' + cell.name
                            fill_measure_files_tim_seq(fname_timing, source_slews, loads)



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
                        f.write("Vclock "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
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
                        f.write("Vclock "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
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
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + str(d_val) + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n')
                        inp = pin['name']
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vclock "+pin['name']+" Gnd " + str(c_val) + "\n")
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
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + str(d_val) + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n')
                        inp = pin['name']
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vclock "+pin['name']+" Gnd " + str(c_val) +"\n")
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
    # Is IQN
    else:
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
                        f.write("Vclock "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
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
                        out_qm + ') VAL=1.75 FALL=1 TARG v(' + out_qm +
                        ') VAL=0.75 FALL=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_qm
                        +') VAL = 1.25 FALL=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
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
                        f.write("Vclock "+pin['name']+" Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n")
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
                        out_qm + ') VAL=0.75 RISE=1 TARG v(' + out_qm +
                        ') VAL=1.75 RISE=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_qm
                        +') VAL = 1.25 RISE=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
        elif related == 'set':
            if r_val == 0:
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + str(d_val) + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n')
                        inp = pin['name']
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vclock "+pin['name']+" Gnd " + str(c_val) + "\n")
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_qm + ') VAL=1.75 FALL=1 TARG v(' + out_qm +
                        ') VAL=0.75 FALL=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_qm
                        +') VAL = 1.25 FALL=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')
        elif related == 'clear':
            if s_val == 0:
                for pin in cell.pins:
                    if pin['type'] == 'input':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd ' + str(d_val) + '\n')
                    elif pin['type'] == 'preset':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 2.5 PWL(0 2.5 2n 2.5 2.1n 0)\n')
                    elif pin['type'] == 'clear':
                        f.write("V" + pin['name'] + ' ' + pin['name'] + ' Gnd 0 PWL(0 0 20n 0 T_END 2.5)\n')
                        inp = pin['name']
                    elif pin['type'] == 'power':
                        f.write("Vpower " + pin['name'] + " Gnd 2.5\n")
                    elif pin['type'] == 'clock':
                        f.write("Vclock "+pin['name']+" Gnd " + str(c_val) +"\n")
                    elif pin['type'] == 'output':
                        if pin['function'] == 'IQ':
                            out_q = pin['name']
                        elif pin['function'] == 'IQN':
                            out_qm = pin['name']
                f.write('C1 ' + out_q + ' Gnd LOAD\n')
                f.write('C2 ' + out_qm + ' Gnd LOAD\n')
                f.write('X1 ' + cell.signature + ' ' + cell.name + '\n')
                f.write('.tran 50p 100n\n.control\n\trun\n\tmeas tran slew TRIG v(' +
                        out_qm + ') VAL=0.75 RISE=1 TARG v(' + out_qm +
                        ') VAL=1.75 RISE=1\n\tmeas tran delay TRIG v('+ inp
                        +') VAL = 1.25 RISE=1 TARG v(' + out_qm
                        +') VAL = 1.25 RISE=1\n\techo \"slew $&slew delay $&delay\" > MEAS_OUT.txt\n\tquit\n.endc\n\n.end')

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
                        fname_recovery = 'skeleton_files/' + cell.name + '/recovery/clear/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_recovery, 'recovery', False)
                    elif timing['type'] == 'removal_rising':
                        fname_removal = 'skeleton_files/' + cell.name + '/removal/clear/' + cell.name + '_skeleton.txt'
                        fill_skeleton_recovery_removal(cell, fname_removal, 'removal', False)
            elif pin['type'] == 'output':
                # fill_skeleton_timing_seq(cell, file_name, function, related, input_type, d_val, c_val, s_val, r_val)
                if pin['function'] == 'IQ':
                    for timing in pin['timing']:
                        if timing['type'] == 'rising_edge':
                            fname_pos_input = 'skeleton_files/' + cell.name + '/timing/out/rel_clock/pos/' + cell.name + '_skeleton.txt'
                            fname_neg_input = 'skeleton_files/' + cell.name + '/timing/out/rel_clock/zero/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_pos_input, 'IQ', 'clock', 'pos', None, None, None, None)
                            fill_skeleton_timing_seq(cell, fname_neg_input, 'IQ', 'clock', 'zero', None, None, None, None)
                        elif timing['type'] == 'clear':
                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/out/rel_clear/d_c_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQ', 'clear', None, 2.5, 2.5, 0, None)


                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/out/rel_clear/d_cn_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQ', 'clear', None, 2.5, 0, 0, None)

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_c_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQ', 'clear', None, 0, 2.5, 0, None)

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_cn_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQ', 'clear', None, 0, 0, 0, None)
                        elif timing['type'] == 'preset':
                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/out/rel_set/d_c_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQ', 'set', None, 2.5, 2.5, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/out/rel_set/d_cn_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQ', 'set', None, 2.5, 0, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/out/rel_set/dn_c_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQ', 'set', None, 0, 2.5, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/out/rel_set/dn_cn_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQ', 'set', None, 0, 0, None, 0)
                elif pin['function'] == 'IQN':
                    for timing in pin['timing']:
                        if timing['type'] == 'rising_edge':
                            fname_pos_input = 'skeleton_files/' + cell.name + '/timing/outn/rel_clock/pos/' + cell.name + '_skeleton.txt'
                            fname_neg_input = 'skeleton_files/' + cell.name + '/timing/outn/rel_clock/zero/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_pos_input, 'IQN', 'clock', 'pos', None, None, None, None)
                            fill_skeleton_timing_seq(cell, fname_neg_input, 'IQN', 'clock', 'zero', None, None, None, None)
                        elif timing['type'] == 'clear':

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_c_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQN', 'clear', None, 2.5, 2.5, 0, None)

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_cn_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQN', 'clear', None, 2.5, 0, 0, None)

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_c_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQN', 'clear', None, 0, 2.5, 0, None)

                            fname_d_c_s = 'skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_sn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_s, 'IQN', 'clear', None, 0, 0, 0, None)
                        elif timing['type'] == 'preset':
                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/outn/rel_set/d_c_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQN', 'set', None, 2.5, 2.5, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/outn/rel_set/d_cn_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQN', 'set', None, 2.5, 0, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/outn/rel_set/dn_c_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQN', 'set', None, 0, 2.5, None, 0)

                            fname_d_c_r = 'skeleton_files/' + cell.name + '/timing/outn/rel_set/dn_cn_rn/' + cell.name + '_skeleton.txt'
                            fill_skeleton_timing_seq(cell, fname_d_c_r, 'IQN', 'set', None, 0, 0, None, 0)


def run_setup(cell):
    max_iter = 10000
    step = 0.05
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
    step = -0.05
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
    step = 0.05
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
    step = -0.05
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

def run_timing(cell):
    if cell.type== 'sequential':
        tim_dirs = os.listdir("measure_files/"+cell.name+"/timing/")
        for out_dir in tim_dirs:
            for rel_in_dir in os.listdir("measure_files/"+cell.name+"/timing/"+out_dir):
                for inp_val_dir in os.listdir("measure_files/"+cell.name+"/timing/"+out_dir+'/'+rel_in_dir):
                    for spice_file in os.listdir("measure_files/"+cell.name+"/timing/"+out_dir+'/'+rel_in_dir+'/'+inp_val_dir):
                        os.system("ngspice " + "measure_files/"+cell.name+"/timing/"+out_dir+'/'+rel_in_dir+'/'+inp_val_dir+'/'+spice_file+" >suppress.txt")
    elif cell.type == 'combinational':
        tim_dirs = os.listdir("measure_files/" + cell.name+'/')
        for spice_file in tim_dirs:
            os.system("ngspice measure_files/"+cell.name+"/"+spice_file+" >suppress.txt")


def make_library(cells):
    #header
    f_library = open("library.txt", 'w')
    f_library.write('library(ece327Library) {\n')
    f_library.write('\n  /* Documentation Attributes */\n  date                    		: "Mon 16 Jan 2023, 18:11:58";\n')
    f_library.write('  revision                		: "revision 1.0";\n')
    f_library.write('  comment                 		: "ECE327 UTH TEMPLATE LIBERTY";\n')
    f_library.write('\n  /* General Attributes */\n  delay_model : table_lookup;\n\n')
    f_library.write('  nom_process     : 1.0;\n  nom_temperature : 125;\n  nom_voltage     : 2.5;\n\n')
    f_library.write('  time_unit               : \"1ns\";\n')
    f_library.write('  voltage_unit            : \"1V\";\n  current_unit            : \"1mA\";\n')
    f_library.write('  pulling_resistance_unit : \"1kohm\";\n  leakage_power_unit      : \"1pW\";\n')
    f_library.write('  capacitive_load_unit(1, pf);\n')
    f_library.write('\n  /* Library Description: Default Attributes */\n')
    f_library.write('  default_output_pin_cap       : 0.0;\n  default_inout_pin_cap        : 1.0;\n  default_input_pin_cap        : 1.0;\n')
    f_library.write('  default_fanout_load          : 1.0;\n  default_cell_leakage_power   : 0.0;\n  default_max_transition       : 10;\n')
    f_library.write('\n  in_place_swap_mode : match_footprint;\n\n  /* Library Operating Conditions */\n\n')
    f_library.write('  operating_conditions(SLOW) {\n\tprocess     :  1.0 ;\n\ttemperature :  125 ;\n\tvoltage     :  2.5 ;\n\ttree_type   : balanced_tree ;\n  }\n')
    f_library.write('\n  default_operating_conditions : SLOW ;\n\n  /* TLF attributes */\n')
    f_library.write('  default_leakage_power_density  : 0.0;\n  slew_derate_from_library : 1;\n  slew_lower_threshold_pct_fall  : 30.0;\n')
    f_library.write('  slew_upper_threshold_pct_fall  : 70.0;\n  slew_lower_threshold_pct_rise  : 30.0;\n  slew_upper_threshold_pct_rise  : 70.0;\n')
    f_library.write('  input_threshold_pct_fall : 50.0;\n  input_threshold_pct_rise : 50.0;\n  output_threshold_pct_fall   : 50.0;\n  output_threshold_pct_rise   : 50.0;\n')
    f_library.write('\n  /* Library Look_Up Tables Templates */\n\n')
    f_library.write('  lu_table_template(Timing_template_6_7) {\n')
    f_library.write('\tvariable_1 : total_output_net_capacitance;\n\tvariable_2 : input_net_transition;\n\tindex_1 ("0.0017, 0.0062, 0.0232, 0.0865, 0.3221, 1.2");\n\tindex_2 ("0.0042, 0.0307, 0.0768, 0.192, 0.48, 1.2, 3");\n  }\n')
    f_library.write('\n  lu_table_template(Constraint_5_5) {\n\tvariable_1 : related_pin_transition;\n\tvariable_2 : constrained_pin_transition;\n\t')
    f_library.write('index_1 ("0.0042, 0.0307, 0.0768, 0.48, 3");\n\tindex_2 ("0.0042, 0.0307, 0.0768, 0.48, 3");\n  }\n')

    #modules/cells

    for cell in cells:
        f_library.write('\n  /******************************************************************************************\n')
        f_library.write('   Module          	: ' + cell.name + '\n   Cell Description	:')
        if cell.type == 'combinational':
            f_library.write(' Combinational cell ('+cell.name+') with drive strength'+cell.drive+'\n')
        elif cell.type == 'sequential':
            f_library.write(' Pos.edge D-Flip-Flop with active low reset, and active low set, and drive strength' + cell.drive + '\n')
        f_library.write('  *******************************************************************************************/\n')
        f_library.write('  cell ('+cell.name+') {\n')
        if cell.type == 'sequential':
            f_library.write('\tff(\"IQ\",\"IQN\") {\n\t  next_state : \"D\";\n\t  clocked_on : \"CLK\";')
            f_library.write('\n\t  preset : \"S\";\n\t  clear : \"R\";\n\t}\n')
        f_library.write('\tarea : 1.0;\n\tpg_pin("VDD") {\n\t  voltage_name : \"VDD\";\n\t  pg_type      : primary_power;\n\t}\n')
        f_library.write('\tpg_pin("VSS") {\n\t  voltage_name : \"VSS\";\n\t  pg_type      : primary_ground;\n\t}\n\n')
        for pin in cell.pins:
            if not pin['type'] == 'power':
                f_library.write('\tpin(\"'+pin['name']+'\") {\n\t  related_power_pin : "VDD";\n\t  related_ground_pin : "VSS";\n')
            if pin['type'] == 'clock':
                f_library.write('\t  clock : true;\n')
            if pin['type'] == 'input' or pin['type'] == 'preset' or pin['type'] == 'clear' or pin['type'] == 'clock':
                f_library.write('\t  capacitance : '+pin['capacitance']+';\n\t  direction : input;\n')
            elif pin['type'] == 'output':
                f_library.write('\t  max_capacitance : '+pin['max_capacitance']+';\n\t  direction : output;\n\t  function : \"' + pin['function'] +'\";\n')
            #timing
            if cell.type == 'combinational':
                if pin['type'] == 'output':
                    for timing in pin['timing']:
                        f_library.write('\n\t  timing() {\n\t\trelated_pin : \"'+timing['related_pin']+'\";\n')
                        f_library.write('\t\twhen : \"!'+timing['other_pin']+'\"\n\t\tsdf_cond : \"('+timing['other_pin']+' == 1\'b0)\";\n')
                        if timing['binate_type'] == 'positive 0':
                            f_library.write('\t\ttiming_sense : positive_unate;\n')
                        else:
                            f_library.write('\t\ttiming_sense : negative_unate;\n')
                        f_library.write('\t  }\n\n')

                        f_library.write('\n\t  timing() {\n\t\trelated_pin : \"' + timing['related_pin'] + '\";\n')
                        f_library.write('\t\twhen : \"' + timing['other_pin'] + '\"\n\t\tsdf_cond : \"('+timing['other_pin']+' == 1\'b1)\";\n')
                        if timing['binate_type'] == 'positive 0':
                            f_library.write('\t\ttiming_sense : negative_unate;\n')
                        else:
                            f_library.write('\t\ttiming_sense : positive_unate;\n')
                        f_library.write('\t  }\n\n')
            if not pin['type'] == 'power':
                f_library.write('\t}\n')

        f_library.write('  }\n')




    f_library.write('}\n')

config_path = "/home/znikolaos-g/VLSI/Project/Part2/config.json"
cells = parse_config(config_path)


if len(sys.argv) != 2:
    print('Error: Invalid number of arguments. 2 arguments must be provided')
    exit(-1)
elif sys.argv[1] == '--run':
    print('Making measure files...')
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
                os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_cn_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/dn_c_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_cn_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/out/rel_clear/d_c_sn')
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
                os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/dn_c_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_cn_sn')
                os.mkdir('skeleton_files/' + cell.name + '/timing/outn/rel_clear/d_c_sn')

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
                os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/out/rel_clear/d_c_sn')
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
                os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_sn')
                os.mkdir('measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_sn')

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
                os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_cn_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/dn_c_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_cn_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/out/rel_clear/d_c_sn')
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
                os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_cn_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/dn_c_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_cn_sn')
                os.mkdir('out_measure_files/' + cell.name + '/timing/outn/rel_clear/d_c_sn')
            except FileExistsError:
                print('Warning: some files already exist!\n')
                pass


        make_skeleton_files(cell)
        make_measure_files(cell)

    print('Running ngspice...')
    for cell in cells:
        print('\n---Cell: ' + cell.name+' Type: '+cell.type+'---')
        if cell.type == 'sequential':
            print('Measuring setup...')
            run_setup(cell)
            print('Measuring hold...')
            run_hold(cell)
            print('Measuring recovery...')
            run_recovery(cell)
            print('Measuring removal...')
            run_removal(cell)
            print('Measuring combinational time...')
            run_timing(cell)
        elif cell.type == 'combinational':
            print('Measuring combinational time...')
            run_timing(cell)

    print('\nDone!')
elif sys.argv[1] == '--make':
    print('Making library...')

    if not os.path.isdir('skeleton_files'):
        print('Error, no prior execution with --run argument!')
        exit(-1)

    make_library(cells)

    print('Done')
elif sys.argv[1] == '--help':
    print('\n-----------------------------Valid Arguments----------------------------------------')
    print('--run: constructs skeleton/measure files based on config file and runs ngspice.')
    print('--make: makes library based on the ouput measure files made with --run argument.\n')
else:
    print('Error, invalid argument: Run with --help to see the valid arguments')
#spice_dirs = os.listdir("measure_files/")

#for spice_dir in spice_dirs:
#    spice_files = os.listdir("measure_files/"+spice_dir+'/')
#    for spice_file in spice_files:
#        if os.path.isfile("measure_files/"+spice_dir+"/"+spice_file):
#            # for combinational gates
#            os.system("ngspice "+"measure_files/"+spice_dir+"/"+spice_file)
