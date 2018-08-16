# Author: Jiahui Wu

import datetime
from collections import defaultdict

import pandas as pd

from src import constants as C
from src.xy_gen import y_cnt_event


class TM_ROLLER:
    def __init__(self, method, named_x_events, y_events, eval_sd, eval_ed, roll_step=1, eval_tw=1, verbose=0):
        """

        Parameters
        ----------
        :param method:
        :param named_x_events: pd.Series, indexed and sorted by date. --> {name: pd.Series}
        :param y_events: pd.Series, indexed and sorted by date.
            events means they are not mapped as features for spaital units

        :param eval_sd: str (format='%Y-%m-%d') or Datetime obj
            the start_date of the time window for evaluation

        :param eval_ed: str (format='%Y-%m-%d') or Datetime obj
            the end_date of the time window for evaluation

        :param roll_step, int, default 1
            the number of days to move at each time rolling

        :param eval_tw: int, default 1
            the number of future days to be considered for evaluation

        :param verbose: int, verbosity level

        """
        self.method = method
        if isinstance(named_x_events, pd.Series):
            named_x_events = {'autoname': named_x_events}
            if verbose > 0: print('wrap pd.Series with dict key')
        self.x_events = named_x_events
        self.y_events = y_events
        self.eval_sd = datetime.datetime.strptime(eval_sd, '%Y-%m-%d') if isinstance(eval_sd, str) else eval_sd
        self.eval_ed = datetime.datetime.strptime(eval_ed, '%Y-%m-%d') if isinstance(eval_ed, str) else eval_ed
        self.eval_tw = eval_tw
        self.roll_step = roll_step
        self.verbose = verbose

    def get_data_date_range(self):
        # TODO: intersect the date range of Y with X, or Union(which it is now)
        min_date, max_date = self.y_events.index.min(), self.y_events.index.max()
        for d in self.x_events.values():
            mini, maxi = d.index.min(), d.index.max()
            if mini < min_date:
                min_date = mini
            if maxi > max_date:
                max_date = maxi

        return min_date, max_date

    def rolling(self):
        """
        """

        if self.x_events is None: raise ValueError('set data first')

        # dates = self.data.index.unique()
        # eval_dates = dates[(dates >= self.sd) & (dates <= self.ed)]

        data_sd, data_ed = self.get_data_date_range()
        if self.verbose > 0: print('Date: [%s, %s]' % (data_sd.strftime(C.COL.date_format),
                                                       data_ed.strftime(C.COL.date_format)))
        # num_days includes both start and end date, thus +1
        num_days = (data_ed - data_sd).days + 1

        # TODO: detailed check for date, tw, sd, ed, num_experiment
        assert num_days >= self.eval_tw + self.roll_step, ('len of dates (%d) is less than time_window + 1 step (%d)'
                                                           % (num_days, self.eval_tw + self.roll_step))
        assert data_sd < self.eval_sd, ('data start date %s >= required evaluation start date %s' %
                                        (data_sd, self.eval_sd))
        assert data_ed >= self.eval_ed, ('data end date %s < required evaluation end date %s' %
                                         (data_ed, self.eval_ed))

        if self.verbose > 0:
            num_experiment = ((self.eval_ed - self.eval_sd).days + 1) // self.roll_step
            print('total number of experiment: ~%d' % num_experiment)

        tw_sd = self.eval_sd
        num_loops = 1
        while tw_sd <= self.eval_ed:
            # TODO what if a time window, either train or test_x_events, or either X or Y, is empty
            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            tw_ed = tw_sd + datetime.timedelta(days=self.eval_tw - 1)
            train_ed = tw_sd - datetime.timedelta(days=1)
            if self.verbose > 0:
                if self.verbose == 1 and num_loops % 10 != 0:
                    pass
                print('No.%d exp, testing period: %s ~ %s' % (
                    num_loops, tw_sd.strftime('%Y-%m-%d'), tw_ed.strftime('%Y-%m-%d')))

            train_x_events = {name: data.loc[:train_ed] for name, data in self.x_events.items()}
            # there won't be test_x_events, since that is in the future
            # test_x_events = {name: data.loc[tw_sd: tw_ed] for name, data in self.x_events.items()}
            train_y_events = self.y_events.loc[:train_ed]
            test_y_events = self.y_events.loc[tw_sd: tw_ed]
            yield {
                'train_x_events': train_x_events,  # 'test_x_events': test_x_events,
                'train_y_events': train_y_events, 'test_y_events': test_y_events,
                'tw_sd'         : tw_sd, 'tw_ed': tw_ed, 'train_ed': train_ed
            }
            tw_sd += datetime.timedelta(days=self.roll_step)
            num_loops += 1

    def eval(self, metrics, sp_units):
        """
        :param metrics: a list of metrics for evaluation;
            if it is callable, wrap it in a list
        """
        if callable(metrics):
            metrics = [metrics]

        result = defaultdict(dict)
        for r in self.rolling():
            # TODO: methods.fit/pred doesn't work for supervised learning. maybe pred->rank?
            # this fit doesn't work for supervised learning,
            # need to specify at fit-phase
            # the spatial units and associated y
            # instead of just y_events

            # fit and pred risk score
            self.method.fit(r['train_x_events'], r['train_y_events'], last_date=r['train_ed'])
            risk_score = self.method.pred(sp_units[C.COL.center], now_date=r['tw_sd'])

            # build attributes of spatial units for metrics
            su_attr = sp_units.copy()
            su_attr[C.COL.risk] = risk_score
            su_attr[C.COL.num_events] = y_cnt_event(sp_units, r['test_y_events'])
            for m in metrics:
                eval_pred = m(su_attr)
                period_str = '%s~%s' % (r['tw_sd'].strftime('%Y-%m-%d'), r['tw_ed'].strftime('%Y-%m-%d'))
                result[m.__name__][period_str] = eval_pred

        res_df = {}
        for m in metrics:
            # print(m.__name__)
            res_df[m.__name__] = pd.DataFrame.from_dict(result[m.__name__])
        return res_df


def main():
    from src.utils.data_prep import prep_911
    from src.utils.spatial_unit import baltimore_grids
    from src import eval_metric
    from src.model.bsln_rtm import RTM
    d911_by_cat = prep_911(path='../' + C.PathDev.p911, verbose=1)
    d911_by_cat = {key: d911_by_cat[key] for key in ['burglary', 'abuse']}
    # d911_coords = {name: data[C.COL.coords] for name, data in d911_by_cat.items()}
    d911_y = d911_by_cat['abuse']
    vstep = 1
    vtw = 1
    vsd = '2015-03-02'
    ved = '2015-03-02'
    grid_size = 200
    train_tw = 60

    grids = baltimore_grids(grid_size=grid_size,
                            cityline_path='../data/open-baltimore/raw/Baltcity_Line/baltcity_line.shp')
    method = RTM(grid_size=grid_size, bw=400, tw=train_tw, verbose=1)
    tmroller = TM_ROLLER(method, d911_by_cat, d911_y, vsd, ved, roll_step=vstep, eval_tw=vtw, verbose=2)

    metrics = [
        eval_metric.hit_rate_auc, eval_metric.search_efficient_rate_auc,
        eval_metric.prediction_accuracy_index_auc, eval_metric.area_to_perimeter_ratio_auc,
        eval_metric.hit_rate_bin, eval_metric.search_efficient_rate_bin,
        eval_metric.prediction_accuracy_index_bin, eval_metric.area_to_perimeter_ratio_bin,
    ]
    res = tmroller.eval(metrics, grids)
    for m in metrics:
        print('==================')
        print(m.__name__)
        print('==================')
        print(res[m.__name__])
    pass


if __name__ == '__main__':
    main()
