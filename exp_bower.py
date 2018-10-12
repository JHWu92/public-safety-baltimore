# coding: utf-8

# In[ ]:


from collections import defaultdict

import numpy as np
import datetime
from src.exp_helper import *
from src.model.bsln_bower import Bower
from src.model.bsln_kde import KDE
from src.utils.metric_single_num import hit_rate, search_efficient_rate, prediction_accuracy_index

grid_size = 50
train_tw = 60
verbose = 0

# In[ ]:


d_bower = CompileData(spu_name='grid_%d' % grid_size)
d_bower.set_x(['crime'], category_groups={'crime': [['burglary']]}, by_category=False)
d_bower.set_y('crime/burglary')

# In[ ]:


tr_bower_2 = Rolling(rsd='2015-07-01', red='2017-06-30', rstep=2, tw_past=train_tw, tw_pred=2)
er_bower_2 = Rolling(rsd='2016-07-01', red='2017-06-30', rstep=2, tw_past=train_tw, tw_pred=2)

tr_bower_7 = Rolling(rsd='2015-07-01', red='2017-06-30', rstep=7, tw_past=train_tw, tw_pred=7)
er_bower_7 = Rolling(rsd='2016-07-01', red='2017-06-30', rstep=7, tw_past=train_tw, tw_pred=7)

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

        if refit:
            if verbose > 1:
                print('refitting for evaluate period:', period)
            tmp_train_roller.red = past_sd
            train_x, train_y = data_for_fit(compile_data, roller=tmp_train_roller, x_setting=x_setting,
                                            y_setting=y_setting,
                                            stack_roll=False, verbose=verbose)
            kde.fit(train_x)
            bower.fit(train_x)
            if verbose > 1:
                print('model fit')

        eval_x, eval_y = data_for_fit(compile_data, x_setting=x_setting, y_setting=y_setting, dates=dates,
                                      verbose=verbose)

        pred_res[period]['true_y'] = eval_y

        if verbose > 1:
            print('predicting for each grid_center')

        pred_res[period]['kde200'] = kde.predict(grid_centers).values
        pred_res[period]['bower'] = bower.predict(grid_centers).values

        if (i + 1) % 5 == 0:
            print('%d periods are done' % i, str(datetime.datetime.now()))
        if i == 20 and debug:
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
                print(mname, e.__name__, score)
                eval_res[mname][idx].append(score)
    return eval_res


# In[ ]:
print('EXP with 2day')
pred_res_2d = get_pred(d_bower, tr_bower_2, er_bower_2, kde200, bower, refit=True,
                       x_setting='time_indexed_points', y_setting='event_cnt', debug=True, verbose=0)
eval_res_2d = get_eval(pred_res_2d)

# In[ ]:

print('EXP with 7day')
pred_res_7d = get_pred(d_bower, tr_bower_7, er_bower_7, kde200, bower, refit=True,
                       x_setting='time_indexed_points', y_setting='event_cnt', debug=True, verbose=0)
eval_res_7d = get_eval(pred_res_7d)

# In[ ]:


pd.DataFrame(eval_res_2d).to_csv('exp_res/bower_2day.csv')
pd.DataFrame(eval_res_7d).to_csv('exp_res/bower_7day.csv')

# In[ ]:
