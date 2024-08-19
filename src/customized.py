import numpy as np
# import pandas as pd


def getAdditionalDataReader(name, path):
    '''
    The server invokes this function to read each data file into memory, or open a file reader.
    It is invoked once for each data file.
    The dataObj returned will be passed to getAdditionalData() for each frame requested. The server will not use the dataObj itself.
    
    params: 
        name: str, e.g. 'trajectory'. Should be consistent with the 'name' field in 'additionalFields' attribute of the VideoManager component for the frontend. 
        path: str, path of the 'trajectory' file

    return:
        DataObj containing the data, such as a pandas df, or a file reader. Will be passed to getAdditionalData() for each frame requested.
    '''
    # example code to read a csv file into a pandas df
    # if name == 'trajectory':
    #     return pd.read_csv(path)

    # The following lines are for testing purpose. Comment them out when implementing the function. 
    if name == 'canvas1':
        return {'range': [0, 8],
                'data': [[0,0], [10,10], [20,20], [30,30], [40,40], [50,50], [60,60], [70,70], [80,80]]}
    elif name == 'canvas2':
        return {'range': [0, 2], #[0, 59],
                'data': [[[0,0], [50, 50]], [[10,10], [60, 60]], [[20,20], [70, 70]]]}
    elif name == 'chart1':
        return {'range': [0, 59], #[0, 59],
                'data': [71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23]}
    elif name == 'chart2':
        return {'range': [0, 59], 
                'data': [91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43, 91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43, 91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43]}


def getAdditionalData(dataObj, frameNum, range):
    '''
    The server invokes this function to get the data for a specific frame, and a range of frames around it.
    The returned value will be sent to the frontend directly. The format below is expected by the frontend.
    
    params:
        dataObj: obj. the dataObj returned by getAdditionalDataReader()
        frameNum: int. the middle index of data range requested
        range: int. the half size of the data range. 
            E.g. if range=20, frameNum=50, should return data from index 30(50-20), to index 70(50+20), inclusively
                 if range=20, frameNum=1 (start index out of bound), should return from index 0, to index 21(1+20), inclusively.
                 if range=20, frameNum=100 (end index out of bound), and total frame num is 110, should return from index 80 (100-20), to index 109, inclusively.
        
    return:
        {
            range: [startIndex, endIndex],
            data: []
        }
    '''
    #TODO
    '''
    should check if range and frameNum out of bound. 
    If range out of bound, but frameNum isn't, returned array size should be smaller than range
    If frameNum is out of bound, raise error.    
    '''

    # The following lines are for testing purpose. Comment them out when implementing the function.
    return dataObj
    # return {'range': [0, 8], #[0, 59],
    #         'data': [[[0,0], [50, 50]], [[10,10], [60, 60]], [[20,20], [70, 70]]]}
            #[[0,0], [10,10], [20,20], [30,30], [40,40], [50,50], [60,60], [70,70], [80,80]]} 
            # [[[0,0], [50, 50]]]} # 
# [71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23]}
