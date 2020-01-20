def ConvertAng2Radiance(AngSig):
    import math
    #AngSig = math.radians(AngSig)
    return print(AngSig.head())

def SegmentRuns(sig):
    rec = 0
    zeroPoints = []
    indx = []
    swta = []
    swtb = []
    swtc = []
    minspd = 0.01
    maxspd = 9
    checkspd = 8
    
    for i in range(len(sig)):
        if sig[i] > maxspd and not swta and not swtb and not swtc:
            swta = 1
            
        elif swta and not swtb and not swtc and sig[i] <= maxspd:
            indx = i
            swtb = 1
            
        elif swta and swtb and not swtc and sig[i] > maxspd:
            swtb = []
            
        elif swta and swtb and not swtc and sig[i] <= checkspd:
            zeroPoints.insert(len(zeroPoints),indx)
            swtc = 1
            
        elif swta and swtb and swtc and sig[i] <= minspd:
            zeroPoints.insert(len(zeroPoints),i)
            swta = []
            swtb = []
            swtc = []
           
    
    return zeroPoints

def PlotDeclSpdOverlay(Time,sig,zeroPoints):
    import matplotlib.pyplot as plt
    
    for i in range(0,len(zeroPoints),2):
        if i == 0:
            startTime = Time[zeroPoints[i]]
            time = Time[zeroPoints[i]:zeroPoints[i+1]]
        else:
            time = Time[zeroPoints[i]:zeroPoints[i+1]]
            time = time - Time[zeroPoints[i]] + startTime
            
            plt.plot(time, sig[zeroPoints[i]:zeroPoints[i+1]])
            
            
    plt.xlabel('Time (s)')
    plt.ylabel('VehicleSpeed kph')
    plt.grid()
    return plt.show()

def BuildRunsDict(df,zeroPoints,sos,Ts):
    
    from scipy.signal import butter, lfilter, freqz, sosfilt
    import numpy as np
    
    Runs_dict = {
        'VehSpd':{},
        'VehAccFilt':{},
        'VehAccRaw':{},
        'VehPitchFilt':{},
        'VehPitchRaw':{},
        'VehRollFilt':{},
        'VehRollRaw':{},
    }
    
    Vehfilt = sosfilt(sos, df['VelForward'])
    
    cnt = 1
    accfilt = []
    accraw = []
    for i in range(0,len(zeroPoints),2):
        
        time = list(df['Time'])[zeroPoints[i]:zeroPoints[i+1]]
        Runs_dict['VehSpd'][('Run'+str(cnt))] = {
            'time':time,
            'data':[df['VelForward'][zeroPoints[i]:zeroPoints[i+1]]]
        }
        
        accfilt = list((np.diff(Vehfilt[zeroPoints[i]:zeroPoints[i+1]]))/Ts)
        accfilt.insert(0,accfilt[0])
        Runs_dict['VehAccFilt'][('Run'+str(cnt))] = {
            'time':time,
            'data':accfilt
        }
        
        accraw = list((np.diff(df['VelForward'][zeroPoints[i]:zeroPoints[i+1]]))/Ts)
        accraw.insert(0,accraw[0])
        Runs_dict['VehAccRaw'][('Run'+str(cnt))] = {
            'time':time,
            'data':accraw
        }
        
        Runs_dict['VehPitchFilt'][('Run'+str(cnt))] = {
            'time':time,
            'data':[df['IsoPitchAngle_filt'][zeroPoints[i]:zeroPoints[i+1]]]
        }
        
        Runs_dict['VehPitchRaw'][('Run'+str(cnt))] = {
            'time':time,
            'data':[df['IsoPitchAngle'][zeroPoints[i]:zeroPoints[i+1]]]
        }
        
        Runs_dict['VehRollFilt'][('Run'+str(cnt))] = {
            'time':time,
            'data':[df['IsoRollAngle_filt'][zeroPoints[i]:zeroPoints[i+1]]]
        }
        
        Runs_dict['VehRollRaw'][('Run'+str(cnt))] = {
            'time':time,
            'data':[df['IsoRollAngle'][zeroPoints[i]:zeroPoints[i+1]]]
        }
        
        cnt = cnt+1
        #print(cnt)
    return Runs_dict,Vehfilt

def WorkOutFgi(mass,Runs_dict):
    g = 9.81
    
    numRuns = len(Runs_dict['VehSpd'].keys())
    Runs_dict['FgiRaw']  = {}
    Runs_dict['FgiFilt'] = {}
    
    for i in range(numRuns):
        time       = Runs_dict['VehAccFilt'][('Run'+str(i+1))]['time']
        AccFilt    = Runs_dict['VehAccFilt'][('Run'+str(i+1))]['data']
        AccRaw     = Runs_dict['VehAccRaw'][('Run'+str(i+1))]['data']
        PitchFilt  = list(Runs_dict['VehPitchFilt'][('Run'+str(i+1))]['data'][0])
        PitchRaw   = list(Runs_dict['VehPitchRaw'][('Run'+str(i+1))]['data'][0])
        FgiFilt    = []
        FgiRaw     = []
        
        for j in range(len(PitchRaw)):
            loss = (-mass*AccRaw[j])+0#(mass*g*math.sin(PitchRaw[j]))
            FgiRaw.append(loss)
            
        for j in range(len(PitchFilt)):
            FgiFilt.append((-mass*AccFilt[j])+0)#(mass*g*math.sin(PitchFilt[j])))
            
        Runs_dict['FgiRaw'][('Run'+str(i+1))] = {'time':time, 'data':FgiRaw}
        Runs_dict['FgiFilt'][('Run'+str(i+1))] = {'time':time, 'data':FgiFilt}
        #print(i)
    
    return Runs_dict