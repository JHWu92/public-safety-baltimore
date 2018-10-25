# coding: utf-8

# In[ ]:


import datetime
from collections import defaultdict

import numpy as np

from src.exp_helper import *
from src.model.bsln_bower import Bower
from src.model.bsln_kde import KDE
from src.utils.metric_single_num import hit_rate, search_efficient_rate, prediction_accuracy_index
from src.utils.spatial_unit import grid2nbh

grid_size = 50
train_tw = 60
verbose = 0

# In[ ]:


d_bower = CompileData(spu_name='grid_%d' % grid_size)
d_bower.set_x(['crime'], category_groups={'crime': [['burglary']]}, by_category=False)
d_bower.set_y('crime/burglary')

# In[ ]:


tr_bower_2 = Rolling(rsd='2015-07-01', red='2017-06-30', rstep=1, tw_past=train_tw, tw_pred=2)
er_bower_2 = Rolling(rsd='2016-07-01', red='2017-06-30', rstep=1, tw_past=train_tw, tw_pred=2)

tr_bower_7 = Rolling(rsd='2015-07-01', red='2017-06-30', rstep=1, tw_past=train_tw, tw_pred=7)
er_bower_7 = Rolling(rsd='2016-07-01', red='2017-06-30', rstep=1, tw_past=train_tw, tw_pred=7)

# In[ ]:


bower = Bower(grid_size, bw=400, tw=train_tw, verbose=verbose)
kde200 = KDE(bw=200, tw=train_tw, verbose=verbose)

# In[ ]:


evaluators = [hit_rate, search_efficient_rate, prediction_accuracy_index]


# In[ ]:


def get_pred(compile_data, train_roller, eval_roller, kde, bower, refit=False,
             x_setting='time_indexed_points', y_setting='event_cnt', verbose=0, debug=False):
    grid_centers = compile_data.spu.Cen_coords.apply(lambda x: eval(x))

    tmp_train_roller = copy.copy(train_roller)

    pred_res = defaultdict(dict)

    for i, dates in enumerate(eval_roller.roll()):
        past_sd, past_ed, pred_sd, pred_ed = dates
        period = 'X: %s~%s -> Y: %s~%s' % (past_sd, past_ed, pred_sd, pred_ed)

        if i % 5 == 0:
            print('beginning the %dth periods' % i, str(datetime.datetime.now()))
        # if refit:
        #     if verbose > 1:
        #         print('refitting for evaluate period:', period)
        #     tmp_train_roller.red = past_sd
        #     train_x, train_y = data_for_fit(compile_data, roller=tmp_train_roller, x_setting=x_setting,
        #                                     y_setting=y_setting,
        #                                     stack_roll=False, verbose=verbose)
        #     kde.fit(train_x)
        #     bower.fit(train_x)
        #     if verbose > 1:
        #         print('model fit')

        eval_x, eval_y = data_for_fit(compile_data, x_setting=x_setting, y_setting=y_setting, dates=dates,
                                      verbose=verbose)

        pred_res[period]['true_y'] = eval_y

        if verbose > 0:
            print('fitting kde, bower on X: %s~%s' % (past_sd, past_ed))
        kde200.fit(eval_x)
        bower.fit(eval_x)

        if verbose > 1:
            print('predicting for each grid_center')

        pred_res[period]['kde200'] = kde.predict(grid_centers).values
        pred_res[period]['bower'] = bower.predict(grid_centers).values

        if i == 1 and debug:
            break
    return pd.DataFrame.from_dict(pred_res, 'index')


# In[ ]:


def get_eval(pred_res):
    eval_res = defaultdict(lambda: defaultdict(list))
    for idx, row in pred_res.iterrows():
        true_y = row.true_y
        for mname, pred_y in row.drop('true_y').items():
            hotspot_mask = pred_y > np.percentile(pred_y, 80)
            for e in evaluators:
                score = e(true_y, hotspot_mask, d_bower.spu)
                # print(mname, e.__name__, score)
                eval_res[mname][idx].append(score)
    return eval_res


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


# In[ ]:
print('EXP with 2day')
pred_res_2d = get_pred(d_bower, tr_bower_2, er_bower_2, kde200, bower, refit=True,
                       x_setting='time_indexed_points', y_setting='event_cnt', debug=False, verbose=0)
eval_res_2d = get_eval(pred_res_2d)
pd.DataFrame(eval_res_2d).to_csv('exp_res/bower_2day.csv')
bnia_stats(pred_res_2d, d_bower, 2)

# In[ ]:

print('EXP with 7day')
pred_res_7d = get_pred(d_bower, tr_bower_7, er_bower_7, kde200, bower, refit=True,
                       x_setting='time_indexed_points', y_setting='event_cnt', debug=False, verbose=0)
eval_res_7d = get_eval(pred_res_7d)
pd.DataFrame(eval_res_7d).to_csv('exp_res/bower_7day.csv')
bnia_stats(pred_res_7d, d_bower, 7)
