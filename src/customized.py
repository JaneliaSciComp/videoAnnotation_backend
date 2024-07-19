import numpy as np
# import pandas as pd


def getAdditionalDataReader(name, path):
    '''
    params: 
        name: str, 'trajectory'
        path: str, path of the 'trajectory'

    return:
        dataObj containing the data, such as a pandas df 
    '''
    #TODO
    # if name == 'trajectory':

    return ''


def getAdditionalData(dataObj, frameNum, range):
    '''
    params:
        dataObj: obj. the dataObj returned by readAdditionalData()
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

    return {'range': [0, 8], #[0, 59],
            'data': [[0,0], [10,10], [20,20], [30,30], [40,40], [50,50], [60,60], [70,70], [80,80]]} # [[[0,0], [50, 50]]]} # # [71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23]}
