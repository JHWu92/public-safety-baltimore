from src.e1_compile_data import CompileData
from src.utils.temporal_roll import Rolling




class Train:
    """Train module for the experiment.
    Initiate each train module for each model with given hyper-parameters(hps)
    Model itself can have a strategy to tune its hps (e.g., sklearn's random search cv)
    """

    def __str__(self):
        rolling = str(self.roller).replace('\t', '\t\t')
        train_setting = 'Stack of roll slices' if self.stack_roll else 'The last roll slice'
        return ('Training for {mname}:\n'
                '\t- y: {y}\n'
                '\t- x: {x}\n'
                '\t- trained on: {train_setting}\n'
                '\t- Model: {model}\n'
                '\t- {rolling}\n'
                ''.format(mname=self.model_name, model=self.model,
                          x=self.x_setting, y=self.y_setting,
                          train_setting=train_setting, rolling=rolling
                          )
                )

    def __init__(self, model, model_name, rps, y_setting, x_setting, stack_roll=False):
        """
        :param model: model with given hps
        :param rps: dict.
            rolling parameters. 'roll_back'=True
        :param x_setting: str
            what type of x to generate from the data in tw_past
        :param y_setting: str
            what type of y to generate from the data in tw_pred
        :param stack_roll: bool, default False
            whether or not to stack roll slices to enlarge training set.
            If True, roll thru the data and stack slices as one training set
            If False, train on the last roll slice
        """
        self.model = model
        self.model_name = model_name
        self.rps = rps
        self.roller = Rolling(**self.rps)
        self.x_setting = x_setting
        self.y_setting = y_setting
        self.stack_roll = stack_roll
        self.cdata = None

    @property
    def data_is_set(self):
        return self.cdata is not None

    def train(self):
        if not self.data_is_set:
            raise ValueError('Set data first')

        if not self.stack_roll:
            dates = self.roller.most_recent_period()
            x, y = self.cdata.gen_x_y_for_model(self.x_setting, self.y_setting, dates)
            print(x.shape, y.shape)
            self.model.fit(x.values, y.values.ravel())
        else:
            raise NotImplementedError('stack roll not implemented')
        return x, y


if __name__ == "__main__":
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import RandomizedSearchCV
    from scipy.stats import randint as sp_randint

    import os

    if os.getcwd().endswith('src'):
        os.chdir('..')
    PD = {"max_depth": [3, None],
          "max_features": sp_randint(1, 8),
          "min_samples_split": sp_randint(2, 11),
          "min_samples_leaf": sp_randint(1, 11),
          "bootstrap": [True, False],
          # "criterion": ["gini", "entropy"]
          }
    D = compile_data = CompileData(verbose=1, spu_name='grid_1000')
    D.set_x(['crime'], by_category=True)
    D.set_y('crime/burglary')
    M = RandomizedSearchCV(RandomForestRegressor(), param_distributions=PD, n_iter=20, cv=5, verbose=1)
    RPS = {'rsd': '2015-01-01', 'red': '2016-07-01', 'rstep': 7, 'tw_past': None}
    TR = Train(model=M, model_name='randomSearchedRF', rps=RPS, y_setting='event_cnt', x_setting='event_cnt')
    print(TR)
    TR.cdata = D
    XP, YF = TR.train()
