import copy
from itertools import chain

import pandas as pd

from src.constants import COL
from src.e0_load_tr_de_spu import LOAD_FUNCS, get_spu
from src.utils import get_df_categories, subdf_by_categories
from src.utils.temporal_roll import Rolling
from src.xy_gen import prepare_temporal_data_for_model


class NamedData:
    def __str__(self):
        return "Data {name}, dname of {keys}".format(name=self.name, keys=list(self.named_data.keys()))

    def __init__(self, name, atemporal=False, verbose=0):
        self.named_data = {}
        self.name = name
        self.atemporal = atemporal
        self.verbose = verbose

    def slice_data(self, sd, ed, dnames=None):
        if dnames:
            if isinstance(dnames, str):
                data = {dnames: self.named_data[dnames]}
            else:
                data = {dname: self.named_data[dname] for dname in dnames}
        else:
            data = self.named_data
        subset = {dname: d[sd:ed] for dname, d in data.items()}
        return subset


class CompileData:

    def __str__(self):
        return ('Compile Data Module:\n'
                '\t- {x}\n'
                '\t- {y}\n'
                '\t- Spatial Unit: {spu_name}\n'
                ''.format(x=self.data_x, y=self.data_y, spu_name=self.spu_name)
                )

    def __init__(self, spu_name=None, verbose=0):
        self.verbose = verbose
        self.spu_name = spu_name
        self.spu = get_spu(spu_name)
        # init Data container
        self._data_loaded = NamedData('Loaded', verbose=verbose)
        self.data_context = NamedData('context', verbose=verbose)
        self.data_y = NamedData('y', verbose=verbose)
        self.data_x = NamedData('X', verbose=verbose)

    def load_data(self, dname):
        """select data loading function by name"""

        if dname not in LOAD_FUNCS:
            raise ValueError('Name=%s cannot be loaded, it hasnt been implemented. Supported data: %s' % (
                dname, ', '.join(LOAD_FUNCS.keys())))

        if self.verbose:
            print('loading data ' + dname)

        func = LOAD_FUNCS[dname]
        data = func(self.spu_name, self.verbose, merge_tr_de=True)
        self._data_loaded.named_data[dname] = data

    def is_loaded(self, dname):
        """assert data sets are loaded in both train and dev set; if the data is not loaded, load the data

        Parameters:
        ----------
        :param dname: str
            the name of data to be loaded
        """

        if dname not in self._data_loaded.named_data:
            self.load_data(dname)

    def set_y(self, dname):
        """set data for y
        :param dname: str
            the name of the data (e.g., crime)
            or name/category (e.g., crime/shooting)
            or name/categories (e.g., crime/shooting+homicide)
            for y
        """
        categories = None
        dname_cat = dname

        if '/' in dname:
            dname, categories = dname_cat.split('/')
            categories = categories.split('+')

        self.is_loaded(dname)
        data = self._data_loaded.named_data[dname]

        if categories:
            data_cat = get_df_categories(data)
            for c in categories:
                assert c in data_cat, 'category: %s is not in dataset (%s)' % (c, data_cat)
            data = data[data[COL.category].isin(categories)]

        self.data_y.named_data[dname_cat] = data
        if self.verbose >= 1:
            print('set data for y, dname/categories=%s' % dname_cat)

    def set_x(self, dnames, by_category=True, category_groups=None):
        """Set data for X.

        :param dnames: list.
            List of dnames to be used to generate feature X.
        :param by_category: bool or list of Boolean, default True.
            whether or not to divide the data by categories.
            Specify list for multiple datasets.
            If this is a list of bools, must match the length of the dnames.
        :param category_groups: dict
            key: dname;
            value: list of groups of categories.
            define categories that should be treated as groups for each dname.

        Examples:
        ----------

        >>> compile_data.set_x(['crime', '911'], by_category=[True, False],
        ...               category_groups={'crime': [['burglary', 'theft_larceny']]})

        """
        if not isinstance(by_category, (tuple, list)):
            by_category = [by_category] * len(dnames)
        assert len(by_category) == len(dnames), 'Len of by_category != dnames'

        for dname, byc in zip(dnames, by_category):
            self.is_loaded(dname)
            has_group = category_groups is not None and dname in category_groups
            groups = category_groups[dname] if has_group else []
            cat_in_g = set(chain(*groups))

            # categories in groups are treated as homogeneous
            if has_group:
                if self.verbose:
                    print('set_x: adding groups for data ' + dname)
                for g in groups:
                    dname_cat = '%s/%s' % (dname, '+'.join(g))
                    self.data_x.named_data[dname_cat] = subdf_by_categories(self._data_loaded.named_data[dname], g)

            # each category not in groups is treated as a set of independent point
            if byc:
                categories = set(get_df_categories(self._data_loaded.named_data[dname]))

                if self.verbose:
                    print('set_x: adding individual category of data ' + dname)
                    print('all categories in data: {} are: {}.'.format(dname, categories))
                    if has_group:
                        print('individual categories are: {}'.format(categories - cat_in_g))

                for c in categories - cat_in_g:
                    dname_cat = '%s/%s' % (dname, c)
                    self.data_x.named_data[dname_cat] = subdf_by_categories(self._data_loaded.named_data[dname], c)

            # treated as one set of homogeneous points
            if not has_group and not byc:
                if self.verbose:
                    print('set_x: adding whole set of data ' + dname)
                self.data_x.named_data[dname] = self._data_loaded.named_data[dname]

    def gen_x_y_for_model(self, x_setting, y_setting, dates):
        # TODO: add doc string
        past_sd, past_ed, pred_sd, pred_ed = dates
        # use feature in the past predict Y in the future
        # F(x_past) = y_pred
        data_x_past = self.data_x.slice_data(past_sd, past_ed)
        data_y_pred = self.data_y.slice_data(pred_sd, pred_ed)
        x = prepare_temporal_data_for_model(data_x_past, setting=x_setting, index_order=self.spu.index)
        y = prepare_temporal_data_for_model(data_y_pred, setting=y_setting, index_order=self.spu.index)
        if y.shape[1] > 1:
            raise NotImplementedError('Multiple Y not implemented')
        # TODO: add context to x
        return x, y


def data_for_fit(compile_data, x_setting, y_setting, dates=None, stack_roll=False, roller=None, verbose=0):
    # decide to use dates or roller
    use_roller = False
    if dates is None:
        if roller is None:
            raise ValueError('Pleas specify either dates or roller')
        use_roller = True
        if not stack_roll:
            dates = roller.most_recent_period()

    # generate date for fit
    if use_roller and stack_roll:
        raise NotImplementedError('stack roll not implemented')
    else:
        x, y = compile_data.gen_x_y_for_model(x_setting, y_setting, dates)

    # print data setting
    if verbose > 1:
        s = ('data setting:\n'
             '\t- y: {y}\n'
             '\t- x: {x}\n'.format(x=x_setting, y=y_setting))
        if dates is not None:
            s += '\t- tw_past: %s ~ %s\n' % (dates[0], dates[1])
            s += '\t- tw_pred: %s ~ %s\n' % (dates[2], dates[3])
        if use_roller:
            s += '\t- %s\n' % ('Stack of roll slices' if stack_roll else 'The last roll slice')
            s += '\t- %s' % str(roller).replace('\t', '\t\t')
        print(s.strip())

    # .ravel(): change the shape of y from column vector to row vector
    return x.values, y.values.ravel()


def eval(compile_data, train_roller, eval_roller, model, evaluators, refit=False):
    eval_res = []
    tmp_train_roller = copy.copy(train_roller)
    for i, dates in enumerate(eval_roller.roll()):
        past_sd, past_ed, pred_sd, pred_ed = dates
        res = {'period': 'X: %s~%s -> Y: %s~%s' % (past_sd, past_ed, pred_sd, pred_ed)}
        if refit and i != 0:
            tmp_train_roller.red = past_sd
            X, Y = data_for_fit(compile_data, roller=tmp_train_roller, x_setting='event_cnt', y_setting='event_cnt',
                                stack_roll=False, verbose=V)
            model.fit(X, Y)
        eval_x, eval_y = data_for_fit(compile_data, x_setting='event_cnt', y_setting='event_cnt', dates=dates,
                                      verbose=V)
        pred_y = model.predict(eval_x)
        for e in evaluators:
            res[e.__name__] = e(eval_y, pred_y, compile_data.spu)

        eval_res.append(res)
        if i > 3:
            break

    return pd.DataFrame(eval_res)


if __name__ == '__main__':
    import os
    from sklearn.svm import SVR
    from src.utils.metric_single_num import metrics

    if os.getcwd().endswith('src'):
        os.chdir('..')
    print(os.getcwd())
    V = 1

    D = CompileData(verbose=V, spu_name='grid_1000')
    D.set_x(['crime'], by_category=True)
    D.set_y('crime/burglary')

    T_R = Rolling(rsd='2015-01-01', red='2016-07-01', rstep=7, tw_past=60, tw_pred=7)
    #
    # PD = {"max_depth": [3, None],
    #       "max_features": sp_randint(1, 8),
    #       "min_samples_split": sp_randint(2, 11),
    #       "min_samples_leaf": sp_randint(1, 11),
    #       "bootstrap": [True, False],
    #       "criterion": ["gini", "entropy"]
    # }
    # M = RandomizedSearchCV(RandomForestRegressor(), param_distributions=PD, n_iter=20, cv=5, verbose=V)
    # M = LinearRegression()
    M = SVR(gamma='scale')

    X, Y = data_for_fit(D, roller=T_R, x_setting='event_cnt', y_setting='event_cnt', stack_roll=False,
                        verbose=V)

    M.fit(X, Y)
    print('training score: ', M.score(X, Y))

    E_R = Rolling(rsd='2016-07-01', red='2017-07-01', rstep=7, tw_past=60, tw_pred=7)

    EVTORS = metrics
    EVAL_RES = eval(D, T_R, E_R, M, EVTORS, refit=False)
