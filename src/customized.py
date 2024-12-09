import numpy as np
# import pandas as pd


def getAdditionalData(name, path):
    '''
    The server invokes this function to read the data for a give file path.
    params:
        name: 'canvas1'. The name of the additional field, corresponding to the field name defined in the VideoMangager component for the client.
        path: 'someDir/someFile.csv'. The path to the file, corresponding to the path the user input to the VideoManager component when they add video.
        
    return:
        [valueForFrame0, valueForFrame1, ...]. Length of the list should be equal to the number of frames in the video.
    '''
    #TODO
    

    # The following lines are for testing purpose. Comment them out when implementing the function.
    if name == 'canvas1':
        return [[0,0], [10,10], [20,20], [30,30], [40,40], [50,50], [60,60], [70,70], [80,80]]
    elif name == 'canvas2':
        return [[[0,0], [50, 50]], [[10,10], [60, 60]], [[20,20], [70, 70]]]
    elif name == 'chart1':
        return [71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23,71,56,-24,56,26,42,10,-82,82,47,-77,29,54,-40,54,91,96,-15,90,23]
    elif name == 'chart2':
        return [91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43, 91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43, 91, 76, -4, 76, 46, 62, 30, -62, 102, 67, -57, 49, 74, -20, 74, 111, 116, 5, 110, 43]

