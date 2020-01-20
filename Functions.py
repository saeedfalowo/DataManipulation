def ConvertAng2Radiance(AngSig):
    import math
    #AngSig = math.radians(AngSig)
    return print(AngSig.head())

def SegmentRuns(sig):
    """
    This function's purpose is to use the vehicle speed signal to segment the test into test runs
    The test runs were performed by accelerating till about 10 m/s before releasing the pedals
    and switching to neutral transmission to allow the vehicle to roll to a stop
    This function extracts the portions of the test where the vehicle has reached its peak speed
    and has started its free rolling.
    This function records the start of the free rolling signal index and its signal index when it
    rolls to a complete stop
    """
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
    """
    This function uses the signal segment point indices to ovelay each runs plot over each other to make comparison
    between the total number of runs
    """
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
    """
    This function uses the signal segment point indices to segment focus signals into the number of test runs
    performed and stores these segmented signals into a cascaded dictionary
    Vehicle Acceleration is also calculated in this function
    """
    
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
    """
    This function uses the Runs cascaded dictionary to calculate the vehicle losses at each time step of the signal
    The vehicle loss signal is also added to the runs dictionary
    """
    g = 9.81
    
    # Find out the number of runs within the dictionary
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