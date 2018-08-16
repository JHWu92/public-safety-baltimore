import geopandas as gp

from src import constants as C


def get_grids(shape, grid_side=200, crs=None):
    from shapely.geometry import Polygon, LineString, box
    import numpy as np

    # if shape is tuple, set it to false
    do_intersect = True

    if isinstance(shape, tuple):
        if len(shape) == 4:
            lon_min, lat_min, lon_max, lat_max = shape
            do_intersect = False
        else:
            raise ValueError('shape is a tuple, but its len != 4')
    elif isinstance(shape, LineString):
        if shape.is_closed:
            lon_min, lat_min, lon_max, lat_max = shape.bounds
            shape = Polygon(shape)
        else:
            raise ValueError('shape is LineString but not closed, which is not supported here')
    elif isinstance(shape, Polygon):
        lon_min, lat_min, lon_max, lat_max = shape.bounds
    else:
        raise ValueError('shape is not bbox tuple, closed LineString or Polygon')

    grid_lon, grid_lat = np.mgrid[lon_min:lon_max+grid_side:grid_side, lat_min:lat_max+grid_side:grid_side]
    grids_poly = []

    for j in range(grid_lat.shape[1] - 1):
        for i in range(grid_lon.shape[0] - 1):
            g = box(grid_lon[i, j], grid_lat[i, j], grid_lon[i + 1, j + 1], grid_lat[i + 1, j + 1])
            if do_intersect and not g.intersects(shape):
                continue
            grids_poly.append(g)

    grids = gp.GeoDataFrame(grids_poly).rename(columns={0: 'geometry'})
    grids[C.COL.center] = grids.geometry.apply(lambda x: x.centroid.coords[0])
    if crs is not None:
        # for unknown reason, sometimes grids.crs is not set by assigning once
        while grids.crs is None:
            grids.crs = crs

    grids[C.COL.area] = grids.geometry.apply(lambda x: x.area)
    return grids


def baltimore_grids(grid_side=200, cityline_path=None):
    if cityline_path is None:
        cityline_path = C.Path_shape.cityline
    cityline = gp.read_file(cityline_path)
    cityline = cityline.to_crs(epsg=3559)
    grids = get_grids(cityline.geometry[0], grid_side, crs=cityline.crs)
    return grids


def main():
    import pandas as pd
    grids = baltimore_grids(cityline_path='../'+C.Path_shape.cityline)
    # print(grids.head())
    print(pd.DataFrame([grids.Area, grids.Cen_coords]).T.head())
    a = grids.Area
    a.name = 'aaaa'
    print(pd.DataFrame([a, grids.Cen_coords]).T.head())

    return


if __name__ == '__main__':
    main()