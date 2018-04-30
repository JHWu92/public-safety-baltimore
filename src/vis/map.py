# coding=utf-8
import folium
from folium.plugins import MarkerCluster, FastMarkerCluster


def add_common_tiles(m):
    folium.TileLayer('Stamen Terrain').add_to(m)
    folium.TileLayer('Stamen Toner').add_to(m)
    folium.TileLayer('Stamen Watercolor').add_to(m)
    folium.TileLayer('CartoDB dark_matter').add_to(m)
    folium.TileLayer('CartoDB positron').add_to(m)  # the last one is the default tiles


def marker_cluster(named_data, lonlat=True, filename='tmp_marker_cluster.html', verbose=0):
    """

    Parameters
    ----------

    :param named_data: dict of lists of coords
        points to be plot on the map
    :param lonlat: boolean, default True
        whether the coords are in (lon, lat) order.
        coords are required in (lat, lon) order in MarkerCluster,
        but usually in geopandas, coords are in (lon, lat)
    :param filename: str
        file name of the map visualization
    :param verbose: int, default 0
        verbosity

    :return: the folium map object

    Examples:
    ----------
    >>> named_data = {'A': [(38.9305064,-77.116761), (38.9195066, -77.1069168)]}
    >>> marker_cluster(named_data, lonlat=True, filename='tmp_marker_cluster.html')

    """

    # TODO: diversify inputs, currently only dict of lists of coords is handled

    # if lonlat, make it (lat, lon)
    if lonlat:
        if verbose > 0: print('transformed to (lat,lon)')
        named_data = {name: [(c[1], c[0]) for c in coords] for name, coords in named_data.items()}

    # get bounding box
    lons, lats = [], []
    for _, coords in named_data.items():
        lats.extend([coord[0] for coord in coords])
        lons.extend([coord[1] for coord in coords])
    w, e, s, n = min(lons), max(lons), min(lats), max(lats)

    # build map
    m = folium.Map()
    add_common_tiles(m)
    m.fit_bounds([(s, w), (n, e)])
    # bind data to map
    for name, coords in named_data.items():
        f = folium.FeatureGroup(name=name)
        if verbose > 0: print('adding layer of', name)
        # TODO: add custom popups
        popups = ['group: {}<br>lon:{}<br>lat:{}'.format(name, lon, lat) for (lat, lon) in coords]
        f.add_child(MarkerCluster(locations=coords, popups=popups))
        m.add_child(f)
    # layer control
    m.add_child(folium.LayerControl())
    m.save(filename)
    return m

def marker_cluster_fast(named_data, lonlat=True,filename='tmp_marker_cluster.html', verbose=0):
    if lonlat:
        if verbose > 0: print('transformed to (lat,lon)')
        named_data = {name: [(c[1], c[0]) for c in coords] for name, coords in named_data.items()}

    # get bounding box
    lons, lats = [], []
    for _, coords in named_data.items():
        lats.extend([coord[0] for coord in coords])
        lons.extend([coord[1] for coord in coords])
    w, e, s, n = min(lons), max(lons), min(lats), max(lats)

    # build map
    m = folium.Map()
    add_common_tiles(m)
    m.fit_bounds([(s, w), (n, e)])
    # bind data to map
    callback = """
    function (row) {{
        var icon, marker;
        icon = L.AwesomeMarkers.icon({{
            icon: "map-marker", markerColor: "{color}"}});
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.setIcon(icon);
        return marker;
    }};
    """
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    for i, (name, coords) in enumerate(named_data.items()):
        if verbose > 0: print('adding layer of', name)
        FastMarkerCluster(data=coords, callback=callback.format(color=colors[i % len(colors)])).add_to(m)
    # layer control
    m.add_child(folium.LayerControl())
    m.save(filename)



def main():
    import geopandas as gp
    from shapely.geometry import Point

    gpdfs = []
    gpdfs.append(gp.GeoDataFrame([Point(-77.116761, 38.9305064), Point(-77.1069168, 38.9195066)], columns=['geometry']))
    gpdfs.append(
        gp.GeoDataFrame([Point(-77.0908494, 38.9045525), Point(-77.0684995, 38.9000923)], columns=['geometry']))

    for gpdf in gpdfs:
        gpdf.crs = {'init': 'epsg:4326', 'no_defs': True}

    named_coords = {'obj a': gpdfs[0].geometry.apply(lambda x: x.coords[0]).tolist()}

    marker_cluster(named_coords, True, verbose=1)
    return


if __name__ == '__main__':
    main()
