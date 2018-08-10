import os
import pandas as pd
import geopandas as gp
from src.data_prep import prep_911, prep_crime
from src.constants import PathData, PathShape, COL


def add_spu_to_data(dname, train, dev, verbose):
    spu_train = assigning_spu(spu_name, dname+'-train', train, verbose)
    train = train.merge(spu_train)
    spu_dev = assigning_spu(spu_name, dname+'-dev', dev, verbose)
    dev = dev.merge(spu_dev)
    return train, dev


def load_911(spu_name=None, verbose=0):
    train = prep_911(PathData.tr_911, by_category=False, coords_series=False, gpdf=True)
    dev = prep_911(PathData.de_911, by_category=False, coords_series=False, gpdf=True)
    if spu_name is not None:
        train, dev = add_spu_to_data('911', train, dev, verbose)
    return train, dev


def load_crime(spu_name=None, verbose=0):
    train = prep_crime(PathData.tr_crime, by_category=False, coords_series=False, gpdf=True)
    dev = prep_crime(PathData.de_crime, by_category=False, coords_series=False, gpdf=True)
    if spu_name is not None:
        train, dev = add_spu_to_data('crime', train, dev, verbose)
    return train, dev


LOAD_FUNCS = {'crime': load_crime, '911': load_911}


def get_spu_path(name):
    return PathShape.spu_dir + name + '.geojson'


def get_assignment_path(dname):
    return PathShape.spu_dir + 'assignment_%s.csv' % dname


def assigning_spu(spu_name, dname, data, verbose=0):
    # running the code below would change the index name of data
    # create a copy to avoid that
    data = data[[COL.ori_index, 'geometry']].copy()

    # Get existing assignment
    apath = get_assignment_path(dname)
    if os.path.exists(apath):
        assignment = pd.read_csv(apath, index_col=0)
    else:
        # not exist, create an empty assignment with index=data[ori_index]
        if verbose:
            print('no assignment existed')
        assignment = pd.DataFrame(index=data[COL.ori_index])

    # if spu_name exist in assignment, return cached assignment
    if spu_name in assignment.columns:
        if verbose:
            print('assignment for data %s in spu %s existed' % (dname, spu_name))
    else:
        print('assignment for data %s in spu %s does not exist, spatial intersecting...' % (dname, spu_name))
        spu = gp.read_file(get_spu_path(spu_name))
        joined = gp.sjoin(spu, data)[[COL.ori_index]]
        joined = joined.reset_index().rename(columns={'index': spu_name}).set_index(COL.ori_index)
        assignment = assignment.join(joined, how='left')
        assignment.to_csv(apath)

    spu_assign = assignment[spu_name].reset_index().drop_duplicates()
    # print some warning

    if spu_assign[COL.ori_index].value_counts().max() > 1:
        print('****WARNING**** Some data get multiple assignments')
    if spu_assign[spu_name].isnull().sum() > 0:
        print('****WARNING**** Some data get 0 assignment')

    return spu_assign


def main():
    return


if __name__ == "__main__":
    import os

    if os.getcwd().endswith('src'):
        os.chdir('..')
    dname = 'crime'
    # spu_name = 'bnia_nbh'
    # spu_name = 'city_nbh'
    spu_name = 'grid_100'
    TR, DEV = LOAD_FUNCS[dname]()
    a = assigning_spu(spu_name, dname + '-train', TR, verbose=1)
    b = assigning_spu(spu_name, dname + '-dev', DEV, verbose=1)
