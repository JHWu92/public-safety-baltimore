import numpy as np
import pandas as pd

from src.exp_helper import CompileData
from src.utils.spatial_unit import grid2nbh


# TODO: haven't adapted to bower,kde in separate files
def bnia_stats(pred_res, data, xday):
    top20 = lambda x: x > np.percentile(x, 80)
    above_mean = lambda x: x > x.mean()
    above_mean_std = lambda x: x > (x.mean() + x.std())
    sum_risk = lambda x: x
    for name, stats_func in [('above_mean', above_mean), ('top20', top20), ('above_mean_std', above_mean_std),
                             ('sum_risk', sum_risk)]:
        res = []
        for idx, row in pred_res.iterrows():
            kde_stats = stats_func(row.kde200)
            kde_stats = pd.Series(kde_stats, index=data.spu.index, name='stat')
            kde_stats = grid2nbh(kde_stats).values.tolist()
            bower_stats = stats_func(row.bower)
            bower_stats = pd.Series(bower_stats, index=data.spu.index, name='stat')
            bower_stats = grid2nbh(bower_stats).tolist()
            res.append({'period': idx, 'kde200': kde_stats, 'bower': bower_stats})
        res = pd.DataFrame(res).set_index('period')
        res.to_csv('exp_res/bower_%dday_bnia_%s_hotspots.csv' % (xday, name))


def bnia_fpn(data, ys, bower, kde200, xday=2, save_file=True):
    top20 = lambda x: x > np.percentile(x, 80)
    above_mean = lambda x: x > x.mean()
    above_mean_std = lambda x: x > (x.mean() + x.std())
    hotspot_def = [('above_mean', above_mean), ('top20', top20), ('above_mean_std', above_mean_std)]

    for hname, hfunc in hotspot_def:
        for fname in ['fp', 'fn']:
            fpn_res = {}
            for p in ys.columns:
                p_fpn_res = {}
                for mname, model in [('bower', bower), ('kde200', kde200)]:
                    h = hfunc(model[p])  # is hotspot or not
                    y = ys[p].astype(bool)  # has crime or not
                    fpn = (h & ~y) if fname == 'fp' else (~h & y)
                    fpn = pd.Series(fpn, index=data.spu.index, name='stat')
                    fpn = grid2nbh(fpn).values.tolist()
                    p_fpn_res['%s' % (mname)] = fpn
                fpn_res[p] = p_fpn_res
            # TODO update the file path once the exp is done
            if save_file:
                pd.DataFrame.from_dict(fpn_res, 'index').to_csv(
                    'tmp/bower_%dday_bnia_%s_hotspots_%s.csv' % (xday, hname, fname))


grid_size = 50
train_tw = 60
verbose = 0
d_bower = CompileData(spu_name='grid_%d' % grid_size)
d_bower.set_x(['crime'], category_groups={'crime': [['burglary']]}, by_category=False)
d_bower.set_y('crime/burglary')

# TODO update file paths once the exp is done on the server
bower_2d = pd.read_pickle('tmp/bower.pickle').to_dense()
ys_2d = pd.read_pickle('tmp/true_y.pickle').to_dense()
kde200_2d = pd.read_pickle('tmp/kde.pickle')
bnia_fpn(d_bower, ys_2d, bower_2d, kde200_2d, 2, save_file=True)
