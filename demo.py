import os, random, logging
from datetime import datetime
from psychopy import visual, core, event, sound
import pandas as pd

# ---------- EIXT ----------
EXIT_FLAG = False

def set_exit():
    global EXIT_FLAG
    EXIT_FLAG = True

# ---------- Initialization ----------
os.environ["PSYCHOPY_FONT_PATHS"] = ""
logging.getLogger("PsychoPy").setLevel(logging.ERROR)
WIN_SIZE, BG_COLOR, FULLSCR = [800,600], "grey", False
FIX_DUR, PRIOR_DUR, GAZE_DUR, MAX_RT, ITI_DUR = 0.5,1.0,0.3,3.0,1.0
IMG = {"prior_1":"face_f.png","prior_2":"face_d.png","gaze_1":"face_l.png","gaze_2":"face_r.png"}
PRACTICE_REPS, MAIN_REPS_PER_COND, BLOCK_TRIALS = 1,30,24
BLOCKS_TOTAL = MAIN_REPS_PER_COND*8//BLOCK_TRIALS  #10
TARGET_POS = {1:(-300,0),2:(300,0)}
KEYMAP = {"f":1,"j":2}

# ---------- Window & Stimuli ----------
win = visual.Window(WIN_SIZE,color=BG_COLOR,units="pix",fullscr=FULLSCR,allowGUI=False)
mouse = event.Mouse(visible=False)

# Esc → set_exit
event.globalKeys.clear(); event.globalKeys.add(key="escape",func=set_exit)

fixation=visual.TextStim(win,text="+",color="white",height=40)
rest_text=visual.TextStim(win,text="Have a rest\n or you can press space to continue",color="black")
instr_text=visual.TextStim(win,text="Instruction:\nAt first, gaze at the fixation cross and following a face stimulus.\nThe face stimulus’ gaze direction becomes left or right side of the display, and then a target stimulus appears at the left or right side of the display.\n• The gaze direction is not related to the location of the target.\nYour task is to judge the target location as fast and accurately as possible.\n\n practice\nF= left J= right\n press space to start",color="black")
transition_text=visual.TextStim(win,text="practice over, next will be formal trails\n press space to continue",color="black")
thanks_text=visual.TextStim(win,text="experiment is over\n thank you!",color="black")
error_beep=sound.Sound("C",secs=0.25)

target_stim=visual.Circle(win,radius=25,fillColor="white",lineColor="black",lineWidth=2)
face_stims={k:visual.ImageStim(win,image=os.path.join(os.getcwd(),v)) for k,v in IMG.items()}

COND_LEVELS=[(e,g,t) for e in(1,2) for g in(1,2) for t in(1,2)]

def make_trials(reps):
    lst=[]
    for _ in range(reps):
        for e,g,t in COND_LEVELS:
            lst.append({"prior_face":e,"gaze_face":g,"target_location":t})
    random.shuffle(lst)
    return lst

def make_block():
    block=[]
    for e,g,t in COND_LEVELS:
        block.extend([{"prior_face":e,"gaze_face":g,"target_location":t} for _ in range(3)])
    random.shuffle(block)
    return block

clock=core.Clock()

def run_one_trial(trial,practice=False):
    global EXIT_FLAG
    res={"trial_number":None,"block_number":None,
         "prior_face":trial["prior_face"],"gaze_face":trial["gaze_face"],
         "target_location":trial["target_location"],
         "congruency":1 if trial["gaze_face"]==trial["target_location"] else 2,
         "response":None,"correct":None,"response_time":None}

    # fix
    fixation.draw(); win.flip(); core.wait(FIX_DUR)
    if EXIT_FLAG: return res
    # prior
    face_stims[f"prior_{trial['prior_face']}"] .draw(); win.flip(); core.wait(PRIOR_DUR)
    if EXIT_FLAG: return res
    # gaze
    face_stims[f"gaze_{trial['gaze_face']}"] .draw(); win.flip(); core.wait(GAZE_DUR)
    if EXIT_FLAG: return res
    # target
    face_stims[f"gaze_{trial['gaze_face']}"] .draw(); target_stim.pos=TARGET_POS[trial["target_location"]]; target_stim.draw(); win.flip()
    clock.reset();
    keys=event.waitKeys(maxWait=MAX_RT,keyList=["f","j"],timeStamped=clock)
    win.flip(); core.wait(ITI_DUR)

    if keys:
        k,rt=keys[0]
        res["response"]=KEYMAP[k]; res["response_time"]=int(rt*1000)
        res["correct"]=1 if res["response"]==trial["target_location"] else 0
        if practice and res["correct"]==0: error_beep.play()
    return res


def run_experiment():
    global EXIT_FLAG
    # practice
    instr_text.draw(); win.flip(); event.waitKeys(keyList=["space"])
    for tr in make_trials(PRACTICE_REPS):
        run_one_trial(tr,practice=True)
        if EXIT_FLAG: break
    if EXIT_FLAG: save_and_quit([])

    transition_text.draw(); win.flip(); event.waitKeys(keyList=["space"])
    results=[]; tid=1
    for blk in range(1,BLOCKS_TOTAL+1):
        for tr in make_block():
            if EXIT_FLAG: break
            res=run_one_trial(tr)
            res["trial_number"],res["block_number"]=tid,blk
            results.append(res); tid+=1
        if EXIT_FLAG or blk==BLOCKS_TOTAL: break
        rest_text.draw(); win.flip(); event.waitKeys(keyList=["space"])
    save_and_quit(results)


def save_and_quit(res_list):
    if res_list:
        df=pd.DataFrame(res_list); ts=datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f"results_{ts}.csv",index=False,encoding="utf-8-sig")
        df.to_excel(f"results_{ts}.xlsx",index=False)
    thanks_text.draw(); win.flip(); core.wait(1)
    win.close(); core.quit()

if __name__=="__main__":
    run_experiment()
