
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
                        print(pin['name'])
                        fname_setup_rising_rise = 'skeleton_files/' + cell.name + '/setup/rise/' + cell.name + '_skeleton.txt'
                        fname_setup_rising_fall = 'skeleton_files/' + cell.name + '/setup/fall/' + cell.name + '_skeleton.txt'
                        fill_skeleton_setup_hold(cell, fname_setup_rising_rise, "setup", True)
                        fill_skeleton_setup_hold(cell, fname_setup_rising_fall, "setup", False)
                    elif timing['type'] == "hold_rising":
                        fname_hold_rising_rise = 'skeleton_files/' + cell.name + '/hold/rise/' + cell.name + '_skeleton.txt'
                        fname_hold_rising_fall = 'skeleton_files/' + cell.name + '/hold/fall/' + cell.name + '_skeleton.txt'
                        fill_skeleton_setup_hold(cell, fname_hold_rising_rise, "hold", True)
                        fill_skeleton_setup_hold(cell, fname_hold_rising_fall, "hold", False)


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
                setup_rise = 1.05*(tc_start + related_start_end/2 - (td_init + i*step + constrained_start_end/2))
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
                setup_fall = 1.05*(tc_start + related_start_end/2- (td_init + i*step + constrained_start_end/2))
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
                hold_rise = 1.05 * (
                            -tc_start - related_start_end / 2 + (td_init + i * step + constrained_start_end / 2))
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
                hold_fall = 1.05 * (
                            -tc_start - related_start_end / 2 + (td_init + i * step + constrained_start_end / 2))
                f_meas_out = open("out_measure_files/" + cell.name + "/hold/fall/" + file, 'w')
                f_meas_out.write(str(hold_fall))
                f_meas_out.close()
                break


config_path = "/home/znikolaos-g/VLSI/Project/Part2/config.json"
cells = parse_config(config_path)

delete('skeleton_files')
delete('measure_files')
delete('out_measure_files')

try:
    os.mkdir('skeleton_files')
    os.mkdir('measure_files')
    os.mkdir('out_measure_files')
except FileExistsError:
    pass

for cell in cells:
    try:
        os.mkdir('skeleton_files/'+cell.name)
        os.mkdir('measure_files/' + cell.name)
        os.mkdir('out_measure_files/' + cell.name)
    except FileExistsError:
        pass

    if cell.type == 'sequential':
        try:
            os.mkdir('skeleton_files/' + cell.name + '/setup')
            os.mkdir('skeleton_files/' + cell.name + '/setup/rise')
            os.mkdir('skeleton_files/' + cell.name + '/setup/fall')
            os.mkdir('skeleton_files/' + cell.name + '/hold')
            os.mkdir('skeleton_files/' + cell.name + '/hold/rise')
            os.mkdir('skeleton_files/' + cell.name + '/hold/fall')
            os.mkdir('skeleton_files/' + cell.name + '/recover')
            os.mkdir('skeleton_files/' + cell.name + '/recover/rise')
            os.mkdir('skeleton_files/' + cell.name + '/recover/fall')
            os.mkdir('skeleton_files/' + cell.name + '/removal')
            os.mkdir('skeleton_files/' + cell.name + '/removal/rise')
            os.mkdir('skeleton_files/' + cell.name + '/removal/fall')

            os.mkdir('measure_files/' + cell.name + '/setup')
            os.mkdir('measure_files/' + cell.name + '/setup/rise')
            os.mkdir('measure_files/' + cell.name + '/setup/fall')
            os.mkdir('measure_files/' + cell.name + '/hold')
            os.mkdir('measure_files/' + cell.name + '/hold/rise')
            os.mkdir('measure_files/' + cell.name + '/hold/fall')
            os.mkdir('measure_files/' + cell.name + '/recover')
            os.mkdir('measure_files/' + cell.name + '/recover/rise')
            os.mkdir('measure_files/' + cell.name + '/recover/fall')
            os.mkdir('measure_files/' + cell.name + '/removal')
            os.mkdir('measure_files/' + cell.name + '/removal/rise')
            os.mkdir('measure_files/' + cell.name + '/removal/fall')

            os.mkdir('out_measure_files/' + cell.name + '/setup')
            os.mkdir('out_measure_files/' + cell.name + '/setup/rise')
            os.mkdir('out_measure_files/' + cell.name + '/setup/fall')
            os.mkdir('out_measure_files/' + cell.name + '/hold')
            os.mkdir('out_measure_files/' + cell.name + '/hold/rise')
            os.mkdir('out_measure_files/' + cell.name + '/hold/fall')
            os.mkdir('out_measure_files/' + cell.name + '/recover')
            os.mkdir('out_measure_files/' + cell.name + '/recover/rise')
            os.mkdir('out_measure_files/' + cell.name + '/recover/fall')
            os.mkdir('out_measure_files/' + cell.name + '/removal')
            os.mkdir('out_measure_files/' + cell.name + '/removal/rise')
            os.mkdir('out_measure_files/' + cell.name + '/removal/fall')
        except FileExistsError:
            pass


    make_skeleton_files(cell)
    make_measure_files(cell)


for cell in cells:
    if cell.type == 'sequential':
        #run_setup(cell)
        #run_hold(cell)
        print("hi")


#spice_dirs = os.listdir("measure_files/")

#for spice_dir in spice_dirs:
#    spice_files = os.listdir("measure_files/"+spice_dir+'/')
#    for spice_file in spice_files:
#        if os.path.isfile("measure_files/"+spice_dir+"/"+spice_file):
#            # for combinational gates
#            os.system("ngspice "+"measure_files/"+spice_dir+"/"+spice_file)
