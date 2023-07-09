#!/usr/bin/env python
# -*- coding: latin-1 -*-
import csv
import yaml
import random
import atexit
import codecs

from typing import List, Dict, Tuple
from os.path import join
from psychopy import visual, event, logging, gui, core


@atexit.register
def save_beh_results() -> None:
    file_name = PART_ID + '_beh.csv'
    with open(join('results', file_name), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name: str, insert: str = '') -> str:
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key: str = 'f7') -> None:
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win: visual.Window, file_name: str, insert: str = '') -> None:
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth=900)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err: str) -> None:
    logging.critical(err)
    raise Exception(err)


# GLOBALS

RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Block number', 'Trial number', 'Button pressed', 'Reaction time', 'Correctness', 'Stim word',
                'Trial type'])  # ... Results header
clock = core.Clock()


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info: Dict = {'ID': '', 'Sex': ['M', "F"], 'Age': ''}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Experiment title, fill by your name!')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')

    # load config, all params should be there
    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)
    frame_rate: int = conf['FRAME_RATE']
    screen_res: List[int] = conf['SCREEN_RES']
    # === Scene init ===
    win = visual.Window(screen_res, fullscr=False, monitor='testMonitor', units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible

    PART_ID = info['ID'] + info['Sex'] + info['Age']
    logging.LogFile(join('results', f'{PART_ID}.log'), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(screen_res))

    # === Prepare stimulus here ===

    # === Training ===
    show_info(win, join('.', 'messages', 'Instruction_1.txt'))
    show_info(win, join('.', 'messages', 'Instruction_2.txt'))
    show_info(win, join('.', 'messages', 'Instruction_3.txt'))
    show_info(win, join('.', 'messages', 'before_training.txt'))

#    color_key = None
 #   if color=

    for trial_no in range((conf['TRAIN_CONGRUENT_IN_BLOCK']) + (conf['TRAIN_INCONGRUENT_IN_BLOCK']) + (conf['TRAIN_CONTROL_IN_BLOCK'])):
        key_pressed, rt, corr = run_experiment(win, conf, clock)  # stim_word, trial_type
        corr = 1 if key_pressed == 'z' else 0
        corr = 2 if key_pressed == 'no_key' else corr
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']),
                                 timeStamped=clock.getTime())  # , timeStamped=clock
        rt = clock.getTime()
        if reaction:  # break if any button was pressed
            break
        RESULTS.append([PART_ID, 'training', trial_no, key_pressed, rt, corr])  # rt, stim_word, trial_type])

        # it's a good idea to show feedback during training trials
        feedb = "Poprawnie" if corr == 1 else "Niepoprawnie"
        feedb = "Brak odpowiedzi" if corr == 2 else feedb
        feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])

        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()

    # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))



    for block_no in range(conf['EXP_NO_BLOCKS']):
        for _ in range((conf['EXP_CONGRUENT_IN_BLOCK']) + (conf['EXP_INCONGRUENT_IN_BLOCK']) + (conf['EXP_CONTROL_IN_BLOCK'])):
            key_pressed, rt, corr = run_experiment(win, conf, clock)
            trial_no += 1
            RESULTS.append([PART_ID, block_no, trial_no, key_pressed, rt, corr])

    # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_experiment(win, conf, clock):
    # === Start pre-trial  stuff (Fixation cross etc.)===

    stimlist = []
    stimlist.extend(['congruent']*conf['EXP_CONGRUENT_IN_BLOCK'])
    stimlist.extend(['incongruent']*conf['EXP_INCONGRUENT_IN_BLOCK'])
    stimlist.extend(['control']*conf['EXP_CONTROL_IN_BLOCK'])

    stim_word = random.choice(conf['STIM_WORD'])

    congruent_color = None
    incongruent_color = None
    if stim_word == 'zolty':
        congruent_color = 'yellow'
        incongruent_color = ['red', 'blue', 'green']
    elif stim_word == 'czerwony':
        congruent_color = 'red'
        incongruent_color = ['yellow', 'blue', 'green']
    elif stim_word == 'niebieski':
        congruent_color = 'blue'
        incongruent_color = ['red', 'yellow', 'green']
    elif stim_word == 'zielony':
        congruent_color = 'green'
        incongruent_color = ['red', 'blue', 'yellow']

    stim_congruent = visual.TextStim(win, text=stim_word, height=conf['STIM_SIZE'], color=congruent_color)
    stim_incongruent = visual.TextStim(win, text=stim_word, height=conf['STIM_SIZE'], color=random.choice(incongruent_color))
    stim_control = visual.TextStim(win, text=random.choice(conf['CONTROL_WORD']), height=conf['STIM_SIZE'], color=random.choice(conf['STIM_COLOR']))
    stim = None

    fix = visual.TextStim(win, text='+', height=50, color=conf['FIX_CROSS_COLOR'])
    # stim = visual.TextStim(win, text=random.choice(conf['STIM_WORD']), height=conf['STIM_SIZE'], color=random.choice(conf['STIM_COLOR']))
    #stim = visual.TextStim(win, text=random.choice(stim_list), height=conf['STIM_SIZE'],
    #                       color=random.choice(conf['STIM_COLOR']))
    # stim_list = random.choice([conf['STIM_WORD'], conf['CONTROL_WORD']])


    stim_type = 0
    for trial_no in range(len(stimlist)):
        previous_stim = stim_type
        stim_type = random.choice(stimlist)
        if previous_stim == 0:
            stim_type = 'congruent'
        if stim_type == 'congruent':
            stim = stim_congruent
        elif stim_type == 'incongruent':
            stim = stim_incongruent
        elif stim_type == 'control':
            stim = stim_control
    stimlist.remove(stim_type)


    for _ in range(conf['FIX_CROSS_TIME']):
        fix.draw()
        win.flip()
        core.wait(1)
    stim.draw()
    event.clearEvents()
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):  # present stimuli
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']))  # , timeStamped=clock
        rt = clock.getTime()
        if reaction:  # break if any button was pressed
            break
        stim.draw()
        win.flip()

    # === Trial ended, prepare data for send  ===
    if reaction:
        key_pressed = reaction[0]
        rt = rt
        corr = 1 if key_pressed == 'z' else 0
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0
        corr = 2

    return key_pressed, rt, corr  # return all data collected during trial


if __name__ == '__main__':
    PART_ID = ''
    main()
