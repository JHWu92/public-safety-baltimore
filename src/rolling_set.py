import datetime
import math
from src.utils import parse_date_str


class Rolling:
    def __str__(self):
        s = ''
        for attr in ['rstep', 'rsd', 'red', 'rnd', 'rback', 'num_step', 'tw_past', 'tw_pred']:
            s += '\t- %s: %s\n' % (attr, getattr(self, attr))
        return ('Rolling:\n'
                '{}'.format(s))

    def __init__(self, rstep, rsd=None, red=None, rnd=None, rback=False, num_step=math.inf,
                 tw_past=math.inf, tw_pred=7):
        """

        :param rstep: int, required
            number of days for each rolling step

        :param rsd: datetime.datetime, or string, default None
            The start date of the rolling period.
            Should not be None:
                - if rback=False, or
                - if rback=True and num_step=math.inf

        :param red: datetime.datetime, or string, default None
            The end date of the rolling period.
            Should not be None:
                - if rback=True, or
                - if rback=False and num_step=math.inf

        :param rnd: datetime.datetime, or string, default None
            The now date of the beginning of the rolling.
            Useful for evaluation phase

        :param rback: bool, default False
            Rolling backward in Time (if True)
            or forward in Time (if False)

        :param num_step: int, default infinite
            num_step=0 means no_roll, get the last recent slice of data
            num_step=math.inf means stop rolling defined by :param rsd or :param red
        :param tw_past: int, math.inf or None. Default infinite
            the size of the time windows of the observable past.
            if None, tw_past = math.inf
        :param tw_pred: int, default 7
            the size of the time window of the future to predict.
        """
        self.rstep = rstep
        self.rsd = parse_date_str(rsd) if rsd is not None else None
        self.red = parse_date_str(red) if red is not None else None
        self.rnd = parse_date_str(rnd) if rnd is not None else None
        self.rback = rback
        self.num_step = num_step
        self.tw_past = tw_past if tw_past is not None else math.inf
        self.tw_pred = tw_pred

    def legit(self):
        if self.rback:
            if self.red is None:
                raise ValueError("Roll backward should define end date to start rolling")
            if self.num_step == math.inf and self.rsd is None:
                raise ValueError("Roll backward with infinite step should define start date to stop rolling")
        if not self.rback:
            if self.rsd is None:
                raise ValueError("Roll forward should define start date to start rolling")
            if self.num_step == math.inf and self.red is None:
                raise ValueError("Roll backward with infinite step should define end date to stop rolling")
        if self.num_step < 0:
            raise ValueError("Number of step should be >= 0")

    @property
    def valid(self):
        try:
            self.legit()
            return True
        except ValueError:
            return False

    def get_rsd(self):
        self.legit()
        if self.rsd is not None:
            return self.rsd

        return parse_date_str(self.red) - datetime.timedelta(days=self.num_step * self.rstep)

    def get_red(self):
        self.legit()
        if self.red is not None:
            return self.red

        return parse_date_str(self.rsd) + datetime.timedelta(days=self.num_step * self.rstep)

    def roll(self, to_str=False):
        rsd = self.get_rsd()
        red = self.get_red()
        sd = pred_ed = rsd
        cnt = 0
        dates = []
        # pred_ed is strictly < end date of rolling. the pred_ed of next step will be beyond red
        while (pred_ed + datetime.timedelta(days=self.rstep, seconds=1)) < red:
            if cnt > self.num_step:
                break
            past_sd = sd
            if self.tw_past == math.inf:
                past_ed = red - datetime.timedelta(days=self.tw_pred, seconds=1)
            else:
                past_ed = sd + datetime.timedelta(days=self.tw_past,
                                                  seconds=-1)  # make sure past and pred don't overlap
            pred_sd = past_ed + datetime.timedelta(seconds=1)
            pred_ed = pred_sd + datetime.timedelta(days=self.tw_pred, seconds=-1)

            sd += datetime.timedelta(days=self.rstep)

            dates.append([past_sd, past_ed, pred_sd, pred_ed])

        if self.rback:
            dates = list(reversed(dates))

        if to_str:
            dates = [[str(d) for d in pairs] for pairs in dates]
        return dates

    def most_recent_period(self):
        dates = self.roll()
        if self.rback:
            return dates[0]
        return dates[-1]


if __name__ == "__main__":
    rsp = {'rstep': 5}
    try:
        R = Rolling(**rsp)
        D = R.roll(True)
    except ValueError:
        print('It failed as expected')

    # infinite past, with fixed rsd and red
    rsp = {'rstep': 5, 'rsd': '2018-01-01', 'red': '2018-02-01'}
    R = Rolling(**rsp)
    D_inf_past = R.roll(True)
    print(D_inf_past)

    # fixed tw_past, rsd and red, going forward
    rsp = {'rstep': 8, 'rsd': '2018-01-01', 'red': '2018-02-01', 'tw_past': 4, 'rback': False}
    R = Rolling(**rsp)
    D_forward = R.roll(True)
    print(D_forward)

    # fixed tw_past, rsd and red, going backward
    rsp = {'rstep': 8, 'rsd': '2018-01-01', 'red': '2018-02-01', 'tw_past': 4, 'rback': True}
    R = Rolling(**rsp)
    D_back = R.roll(True)
    print(D_back)

    # TODO: other scenarios.
    # infinite past, fixed red, no rsd, fixed nd to set the start of rolling
    # rsp = {'rstep': 5,  'red': '2018-02-01', 'tw_past': 4, 'rback': False}
    # R=Rolling(**rsp)
    # D_inf_past_norsd=R.roll(True)
    # print(D_inf_past_norsd)
