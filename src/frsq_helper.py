# coding=utf-8
import pickle
import geopandas as gp
from shapely.geometry import box
from foursquare import FoursquareException
import os

def grid_line(mini, maxi, ngrid=10):
    delta = (maxi - mini) / ngrid
    return [(mini + i * delta, mini + (i + 1) * delta) for i in range(ngrid)]


def grid_area(w, s, e, n, ngrid_1d=10):
    """
    grid area into ngrid_1d^2 grids
    :param w, s, e, n,: the w, s, e, n (min_lon, min_lat, max_lon, max_lat) of the bound box
    :param ngrid: divide area into ngrid^2 grids
    :return: list of grid represented by bound box with s,w,n,e
    """
    grid_lat = grid_line(s, n, ngrid_1d)
    grid_lon = grid_line(w, e, ngrid_1d)
    grids = []
    for i in range(ngrid_1d):
        for j in range(ngrid_1d):
            si, ni = grid_lat[i]
            wj, ej = grid_lon[j]
            grids.append((wj, si, ej, ni))
    return grids


def fs_api():
    import foursquare
    clients_id_secret = [
        # jefwuu
        ('ROKWVVBGNH4ICRFZEX4FMS23WRMENXICTXTKEYBLT4BQGLFL', 'WPSNJXDN0SH0UZCDGBBAFCN00UNXKKFBCE02LUFJKWFAWNEB'),
        # jhwu92
        ('FJLWGSADBT2R1ELM0W14CIHSOSDZ0ZVGGKJOV5CUEC3JSUKM', '0SA5RHLJ5LKRPPPAKQMLJVBB0HCWTQJ2LJD5OPO4LCO3H00L'),
        ('QUKQ3QQUXVAYNJOEYNOJIKLGGFPUTOQ2PWS4PNYJUTVY2UKB', 'BLCCAQAZYXFVLELFDYKJT4EOFLI3WGW4YKMDOIQ2XPFE3J3C'),
        ('B5UXLIK21H3XVVIIKBYVG55XXOAVF50OAEFYT5KNWEZ0AJFS', 'AZGHYGMVF3CPO0VUWQWIFP4DYBEIPUOLCT31SUKVTA3FOQRP'),
        ('VLX3BBUP4VTKT5BP53CBWMTKUWGVGBE34O52S4ULNWAAJURO', '2534VD02WWGCJCILTTRJXXEOPLDTXDVREKXAKGX515HJV3H0'),
        ('VJR0HIRSW5AEWJL1U0YVP2CJNNY1DOMEBRBM3XD15MW55LQZ', 'MM55NWKDFC51M1PU2I3GNXDJQ0NNIDKNVBRNZJSW4COLBQIR'),
        ('CWCA2GY2YJKS4GTCBU4V3KI0KH2KMDVZXVJVKFS5C3VPXGCV', 'NLMSW00OFS2FZDYIEA5ZPM4RH35ZAHHFGQSTTC3BYGGX0OIS'),
        ('GOOWLBFKGWVYJA5E4ES5MUQCF5B2NWITHFNCCVUOLIIN3ZF3', 'UUZ32DS3U5CC22XJ5LIO3RVVMRWL4NFYOM2V3SZ0H1ETWKSC'),
        ('I5QIF0SFJCRMAVBSBV3KEZSCQ02MLQZPJ2JPKIG2UFREDUXL', 'GQDNDG03NP4IXXM0QSIJUL3H3KMX0B2OWRNJRVQX3LH3FFOJ'),
        ('NRAQWNRMKH4W1BP3SQXTLJEKCQKXYOH1G0WPEBPFHVKEGZTM', 'BU2ST3EPY3MSUMKU1XLNTVV00XYBFDWCNWIVJNCWQ502OF11'),
    ]

    clients = [foursquare.Foursquare(client_id=client_id, client_secret=client_secret) for client_id, client_secret in
               clients_id_secret]
    return clients


def raw_venues_in_city(city_path, frsq_venues_raw_path, ngrid_1d=100):
    """
    :return: file line structure: ( (w,s,e,n) of the searching bbox,  cnt of venues, json return by frsq api )
    """
    import time
    clients = fs_api()
    city_poly_gpdf = gp.read_file(city_path)
    city_poly = city_poly_gpdf.geometry.values[0]
    w, s, e, n = city_poly.buffer(0.001).bounds  # buffer a little to handle FS inaccuracy
    grids = grid_area(w, s, e, n, ngrid_1d=ngrid_1d)
    data_cache = []
    bbox_done_path = 'processed-bbox.pkl'
    bbox_done = set() if not os.path.exists(bbox_done_path) else pickle.load(open(bbox_done_path, 'rb'))
    request_cnt = len(bbox_done)
    print('processed bbox_done:', request_cnt)
    time_out_try = 0

    while len(grids) > 0:
        w, s, e, n = grids.pop()
        # if this bbox is done(with # venues<50), skip
        if (w, s, e, n) in bbox_done:
            continue

        bbox = box(w, s, e, n)
        if bbox.intersects(city_poly):
            client = clients[request_cnt % len(clients)]

            while time_out_try < 6:
                try:
                    search = client.venues.search(
                        params={'intent': 'browse', 'sw': '{},{}'.format(s, w), 'ne': '{},{}'.format(n, e),
                                'limit' : 50})
                    time.sleep(0.02)
                    time_out_try = 0
                    break
                except FoursquareException as err:
                    time_out_try+=1
                    print(err)
                    print('time.sleep 30 mins, time out try =',time_out_try)
                    if time_out_try>=6:
                        break   
                    time.sleep(1800)

            if time_out_try>=6:
                break

            # if the number of returned venues >=50,
            # the grid is discarded, will be further divided and make finer requests
            # else this bbox is considered done and saved
            len_venues = search['venues'].__len__()
            if len_venues >= 50:
                new_grids = grid_area(w, s, e, n)
                grids.extend(new_grids)
            else:
                # one bbox is successfully queried
                request_cnt += 1
                data_cache.append('{}\t{}\t{}'.format((w, s, e, n), len_venues, search))
                bbox_done.add((w, s, e, n))

            # save result every 500 requests
            if (request_cnt+1) % 500 == 0:
                # saving venues per grid
                output_file = frsq_venues_raw_path + '{}.txt'.format(request_cnt)
                with open(output_file, 'w', encoding='utf-8') as f:
                    print('writing raw frsq venues: ' + output_file)
                    f.write('\n'.join(data_cache))
                data_cache = []
                # saving processed bboxes
                with open(bbox_done_path, 'wb') as f:
                    pickle.dump(bbox_done, f)

    if len(data_cache) > 0:
        output_file = frsq_venues_raw_path + '{}.txt'.format(request_cnt)
        with open(output_file, 'w', encoding='utf-8') as f:
            print('writing raw frsq venues:  ' + output_file)
            f.write('\n'.join(data_cache))
        with open(bbox_done_path, 'wb') as f:
            pickle.dump(bbox_done, f)


def show_grids_used(city_path, frsq_venues_raw_path):
    import glob
    city_poly_gpdf = gp.read_file(city_path)
    for fn in glob.glob(frsq_venues_raw_path + '*.txt'):
        with open(fn, encoding='utf8') as f:
            wsen_poly = [box(*eval(line.split('\t')[0])) for line in f]
        gpdf = gp.GeoDataFrame(wsen_poly, columns=['geometry'])
        city_poly_gpdf = city_poly_gpdf.append(gpdf, ignore_index=True)
    print('# grids used:', city_poly_gpdf.shape[0] - 1)

    ax = city_poly_gpdf.plot(figsize=(45, 45))
    fig = ax.get_figure()
    fig.savefig(frsq_venues_raw_path + u'show_grids_used.png')


def frsq_venues_in_city_geojson(city_path, frsq_venues_raw_path, frsq_venues_in_city_path):
    from pandas.io.json import json_normalize
    import shapely.geometry as shpgeo
    import glob
    all_venues = []
    for fn in glob.glob(frsq_venues_raw_path + '*.txt'):
        with open(fn, encoding='utf8') as f:
            for line in f:
                wsen, vcnt, data = line.split('\t')
                data = eval(data)
                venues = data['venues']
                all_venues.extend(venues)

    df_venues = json_normalize(all_venues)
    df_venues['categories.name'] = df_venues.categories.apply(lambda x: x[0]['name'] if x else '')
    df_venues['categories.id'] = df_venues.categories.apply(lambda x: x[0]['id'] if x else '')
    df_venues['geometry'] = df_venues.apply(lambda x: shpgeo.Point(x['location.lng'], x['location.lat']), axis=1)
    columns = ['id', 'geometry', 'name', 'stats.checkinsCount', 'stats.tipCount', 'stats.usersCount', 'categories.name']
    df_no_dup = df_venues[columns].drop_duplicates('id').copy()
    df_no_dup.columns = ['id', 'geometry', 'name', 'checkins', 'tips', 'users', 'category']

    city_poly_gpdf = gp.read_file(city_path)
    city_poly = city_poly_gpdf.geometry.values[0]
    print('# venues in/not in city')
    print(df_no_dup.geometry.apply(lambda x: x.intersects(city_poly)).value_counts())
    df_no_dup_in_city = df_no_dup[df_no_dup.geometry.apply(lambda x: x.intersects(city_poly))].copy()

    with open(frsq_venues_in_city_path, 'w', encoding='utf8') as f:
        f.write(gp.GeoDataFrame(df_no_dup_in_city).to_json())


def parse_frsq_taxonomy(frsq_taxonomy_json_path, frsq_taxonomy_csv_path, frsq_taxonomy_tree_path, max_level=6):
    """
    output parsed_tree(top parent is absent, need manual assignment); direct_parent and node name csv
    API for frsq taxonomy: https://developer.foursquare.com/docs/venues/categories
    json used on 2017-01-01 is accessed by
    https://api.foursquare.com/v2/venues/categories?oauth_token=1AY1GV2K2SXJW0OQGD0XXE440H5W21FX50FK5OOFE2B5EOUN&v=20170101
    """

    import json
    import pandas as pd

    with open(frsq_taxonomy_json_path) as f:
        js = json.load(f)
        categories = js['response']['categories']

    # parse children categories recursively
    def parse_categories(categories, parent_id, level):
        result = []
        for order, cate in enumerate(categories):
            cid, pluralName, shortName, name, icon = cate['id'], cate['pluralName'], cate['shortName'], cate['name'], \
                                                     cate['icon']
            sub_result = []
            if 'categories' in cate and cate['categories']:
                sub_result = parse_categories(cate['categories'], cid, level + 1)
            result.append([parent_id, cid, pluralName.strip(), shortName.strip(), name.strip(), icon, level, order])
            result.extend(sub_result)
            #         break
        return result

    df = pd.DataFrame(parse_categories(categories, 'root', 1))
    df.columns = ['parent_id', 'cid', 'pluralName', 'shortName', 'name', 'icon', 'level', 'order']

    print('parsed FourSquare taxonomy')
    for i in range(1, max_level + 1):
        sub_df = df.query('level==%d' % i)
        print('level=', i, '# categories', sub_df.shape[0], 'parent categories',
              sub_df.parent_id.value_counts().shape[0])

    df.drop('icon', axis=1).to_csv(frsq_taxonomy_csv_path, encoding='utf-8')

    with open(frsq_taxonomy_tree_path, 'w') as f:
        f.write('\n'.join(df.apply(lambda x: '{}{}'.format('\t' * x.level, x['name'].encode('utf-8')), axis=1).values))
