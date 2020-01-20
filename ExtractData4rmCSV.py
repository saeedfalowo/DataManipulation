def ExtractData4rmCSV(csvfilepath):
    
    """
    This function's purpose is to convert a csv file containing signal values into a single dataFrame
    """
    
    import csv
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    import datetime
    
    content = []    
    with open(csvfilepath, newline='') as csvfile:
        csv_read = csv.reader(csvfile,delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
        for row in csv_read:
            content.append(row)
    
    numrows = len(content)
    numcols  = len(content[0])    
    print('content consists of %d rows and %d columns' %(numrows,numcols))
    
    signames = content[0]
    dataset = content[1:numrows]
    
    df = pd.DataFrame(dataset)
    
    dflastrow = len(df)-1
    df = df.drop([dflastrow], axis=0)
    
    df.columns = signames
    
    df.shape[0] # number of rows in a dataframe
    df.shape[1] # number of cols in a dataframe
    
    maxtime_sec = max(df['Time'])
    time = str(datetime.timedelta(seconds=round(max(df['Time']))))
    time_splt = time.split(":")
    
    print('dataFrame shape: %d by %d (rows by columns)\n' %(df.shape[0],df.shape[1]))
    print('These are the signals found in the csv file\n'), print(signames)
    print('\n The test ran for %d seconds, which is %s hours, %s minutes, and %s seconds!\n' %(maxtime_sec, time_splt[0], time_splt[1], time_splt[2]))
    print(type(df))
    
    return df