import numpy as np
import levelset
import datetime
from skopt import gp_minimize

def gridsearch(gps, X, scandetails):
    thresholds = [-np.inf] + scandetails.thresholds + [np.inf]
    acqval     = np.array([levelset.info_gain(xtest, gps, thresholds, scandetails.meanX) for xtest in scandetails.acqX])

    newx = None
    for i,cacq in enumerate(scandetails.acqX[np.argsort(acqval)]):
        if cacq.tolist() not in X.tolist():
            print('taking new x. best non-existent index {} {}'.format(i,cacq))
            newx = cacq
            return newx,acqval
        else:
            print('{} is good but already there'.format(cacq))
    print('returning None.. something must be wrong')
    return None,None


def batched_gridsearch(gps, X, scandetails, gp_maker = None, batchsize=1):
    newX = np.empty((0,X.shape[-1]))
    my_gps    = gps
    my_y_list = [gp.y_train_ for gp in my_gps]
    myX       = X

    acqinfos = []

    while True:
        newx,acqinfo = gridsearch(my_gps, myX, scandetails)
        newX = np.concatenate([newX,np.asarray([newx])])
        acqinfos.append(acqinfo)
        if(len(newX)) == batchsize:
            print('we got our batch')
            return newX, acqinfos

        print('do fake update')
        myX = np.concatenate([myX,newX])

        newy_list = [gp.predict(newX) for gp in my_gps]
        for i,newy in enumerate(newy_list):
            print('new y i: {} {}'.format(i,newy))
            my_y_list[i] = np.concatenate([my_y_list[i],newy])
        print('build fake gps')
        my_gps = [gp_maker(myX,my_y) for my_y in my_y_list]


def gpsearch(gps, X, scandetails):
    thresholds = [-np.inf] + scandetails.thresholds + [np.inf]

    ranges = list(zip(scandetails.plot_rangedef[:,0],scandetails.plot_rangedef[:,1]))


    def objective(xtest):
        return levelset.info_gain(xtest, gps, thresholds, scandetails.meanX)
    res = gp_minimize(objective, ranges, noise=1e-7, n_calls=350, n_random_starts=350)
    newx = np.asarray(res.x)
    print('returning {}'.format(newx))
    return newx,None