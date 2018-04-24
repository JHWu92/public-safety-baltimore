# Author: Jiahui Wu

import datetime

from src.xy_gen import y_cnt_event
import pandas as pd


class TM_ROLLER:
    def __init__(self, method, data, eval_sd, eval_ed, roll_step=1, eval_tw=1, verbose=0):
        """

        Parameters
        ----------
        :param method:
        :param data: pd.Series, indexed and sorted by date. --> {name: pd.Series}

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
        if isinstance(data, pd.Series): data = {'autoname': data}
        self.data = data
        self.eval_sd = datetime.datetime.strptime(eval_sd, '%Y-%m-%d') if isinstance(eval_sd, str) else eval_sd
        self.eval_ed = datetime.datetime.strptime(eval_ed, '%Y-%m-%d') if isinstance(eval_ed, str) else eval_ed
        self.eval_tw = eval_tw
        self.roll_step = roll_step
        self.verbose = verbose

    def get_data_date_range(self):
        min_date, max_date = None, None
        for d in self.data.values():
            mini, maxi = d.index.min(), d.index.max()
            if min_date is None or mini < min_date:
                min_date = mini
            if max_date is None or maxi > max_date:
                max_date = maxi
        return min_date, max_date

    def rolling(self):
        """
        """

        if self.data is None: raise ValueError('set data first')

        # dates = self.data.index.unique()
        # eval_dates = dates[(dates >= self.sd) & (dates <= self.ed)]

        data_sd, data_ed = self.get_data_date_range()
        if self.verbose>0: print('Date: [%s, %s]' % (data_sd, data_ed))
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
            num_experiment = (self.eval_ed - self.eval_sd).days // self.roll_step
            print('total number of experiment:', num_experiment)

        tw_sd = self.eval_sd
        num_loops = 1
        while tw_sd <= self.eval_ed:
            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            tw_ed = tw_sd + datetime.timedelta(days=self.eval_tw - 1)
            train_ed = tw_sd - datetime.timedelta(days=1)
            if self.verbose > 0:
                if self.verbose == 1 and num_loops % 10 != 0:
                    pass
                print('No.%d exp, testing period: %s ~ %s' % (
                    num_loops, tw_sd.strftime('%Y-%m-%d'), tw_ed.strftime('%Y-%m-%d')))

            train = {name: data.loc[:train_ed] for name, data in self.data.items()}
            test = {name: data.loc[tw_sd: tw_ed] for name, data in self.data.items()}
            yield {'train': train, 'test': test, 'tw_sd': tw_sd, 'tw_ed': tw_ed, 'train_ed': train_ed}
            tw_sd += datetime.timedelta(days=self.roll_step)
            num_loops += 1

    def eval(self, metric, sp_units):
        """

        metric:

        """
        # TODO multiple metrics
        result = {}
        for r in self.rolling():
            self.method.fit(r['train'], last_date=r['train_ed'])
            # TODO allow diverse parameters for pred
            pred = self.method.pred(sp_units['cen_coords'])
            y = y_cnt_event(sp_units, r['test'])
            eval_pred = metric(pred, y)
            result['%s~%s' % (r['tw_sd'].strftime('%Y-%m-%d'), r['tw_ed'].strftime('%Y-%m-%d'))] = eval_pred
        return result


def main():
    from src.data_prep import prep_911_by_category
    from src import constants as C
    d911_by_cat = prep_911_by_category(path='../'+C.PATH_DEV.p911, verbose=1)
    d911_coords = {name: data[C.COL.coords] for name, data in d911_by_cat.items()}
    vstep = 1
    vtw = 1
    vsd = '2015-03-02'
    ved = '2015-03-10'
    tmroller = TM_ROLLER(None, d911_coords, vsd, ved, roll_step=vstep, eval_tw=vtw, verbose=2)
    for x in tmroller.rolling():
        print(1)
    pass

if __name__ == '__main__':
    main()