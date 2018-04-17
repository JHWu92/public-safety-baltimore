# Author: Jiahui Wu

import datetime
from .xy_gen import y_cnt_event

class TM_ROLLER:

    def __init__(self, method, data, sd, ed, step=1, tw=1, verbose=0):
        """

        Parameters
        ----------
        :param method:
        :param data: pd.Series, indexed and sorted by date.

        :param sd: str (format='%Y-%m-%d') or Datetime obj
            the start_date of the time window for evaluation

        :param ed: str (format='%Y-%m-%d') or Datetime obj
            the end_date of the time window for evaluation

        :param step, int, default 1
            the number of days to move at each time rolling

        :param tw: int, default 1
            the number of future days to be considered for evaluation

        :param verbose: int, verbosity level

        """
        self.method = method
        self.data = data
        self.sd = datetime.datetime.strptime(sd, '%Y-%m-%d') if isinstance(sd, str) else sd
        self.ed = datetime.datetime.strptime(ed, '%Y-%m-%d') if isinstance(ed, str) else ed
        self.step = step
        self.tw = tw
        self.verbose = verbose

    def __rolling(self):
        """
        """

        if self.data is None: raise ValueError('set data first')

        dates = self.data.index.unique()
        eval_dates = dates[(dates >= self.sd) & (dates <= self.ed)]

        # TODO: detailed check for date, tw, sd, ed, num_experiment
        if len(dates) <= self.tw:
            raise ValueError('len of dates (%d) is less than time_window (%d)' % (len(dates), self.tw))

        num_experiment = len(eval_dates)

        if self.verbose > 0:
            print('total number of experiment:', num_experiment)

        tw_sd = self.sd
        num_loops = 1
        while tw_sd <= self.ed:
            # pandas time index slice include both begin and last date,
            # to have a time window=tw, the difference should be tw-1
            tw_ed = tw_sd + datetime.timedelta(days=self.tw - 1)
            train_ed = tw_sd - datetime.timedelta(days=1)
            if self.verbose > 0:
                if self.verbose == 1 and num_loops % 10!=0:
                    pass
                print('No.%d exp, testing period: %s ~ %s' %(
                    num_loops, tw_sd.strftime('%Y-%m-%d'), tw_ed.strftime('%Y-%m-%d')))

            train = self.data.loc[:train_ed]
            test = self.data.loc[tw_sd: tw_ed]
            yield {'train': train, 'test': test, 'tw_sd': tw_sd, 'tw_ed': tw_ed, 'train_ed': train_ed}
            tw_sd += datetime.timedelta(days=self.step)
            num_loops+=1

    def eval(self, metric, sp_units):
        """

        metric:

        """
        # TODO multiple metrics
        result = {}
        for r in self.__rolling():
            self.method.fit(r['train'], last_date=r['train_ed'])
            pred = self.method.pred(sp_units['cen_coords'])
            y = y_cnt_event(sp_units, r['test'])
            eval_pred = metric(pred, y)
            result['%s~%s' % (r['tw_sd'].strftime('%Y-%m-%d'), r['tw_ed'].strftime('%Y-%m-%d'))] = eval_pred
        return result
