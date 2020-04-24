import multiprocessing  
from xml.etree.ElementTree import Element, SubElement, Comment
import xml.etree.cElementTree as ET
#from ElementTree_pretty import prettify
import pandas as pd
import os
from pathlib import Path
from shutil import move

global data, dx
data = pd.read_csv('train.csv')
dx = os.listdir('../train/JPEGImages/')

def func(n):
    global data, dx

    print('Total images=', len(dx))
    step = len(dx) // 100
    len1 = len(dx)
    st = len1//4*n
    ed = st+len1//4
    print('start with image index=', st)
    for i in range(st , ed): 
        fn = dx[i][:-4]
        myfile = os.path.join('../train/Annotations/', fn +'.xml')
        if os.path.exists(myfile):
            continue
        idx = data.ImageID==fn

        ob = data[idx]

        label = ob.iloc[:,2].values
        xmin = ob.iloc[:,4].values
        xmax = ob.iloc[:,5].values
        ymin = ob.iloc[:,6].values
        ymax = ob.iloc[:,7].values

#         data = data.drop(data.index[idx])



        top = Element('annotation')
        child_filename = SubElement(top,'filename')
        child_filename.text = fn +'.jpg'


        for x in range(len(label)):     #Iterate for each object in a image. 

            child_obj = SubElement(top, 'object')

            child_name = SubElement(child_obj, 'name')
    #         import pdb
    #         pdb.set_trace()
            child_name.text = label[x] #name

            child_bndbox = SubElement(child_obj, 'bndbox')

            child_xmin = SubElement(child_bndbox, 'xmin')
            child_xmin.text = str(xmin[x]) #xmin

            child_xmax = SubElement(child_bndbox, 'xmax')
            child_xmax.text = str(xmax[x]) #ymin

            child_ymin = SubElement(child_bndbox, 'ymin')
            child_ymin.text = str(ymin[x])#xmax

            child_ymax = SubElement(child_bndbox, 'ymax')
            child_ymax.text = str(ymax[x]) #ymax
        tree = ET.ElementTree(top)
        tree.write(myfile)
        if i % step==0:
            print('Progress: %d at index ^=%d' % (i/step, i))
 
if __name__ == '__main__':

    pool = multiprocessing.Pool(processes=4)
    pool.map(func, range(4))
    pool.close()
    pool.join()   
    print('done')