
def train_model(compile_data, roller, model, x_setting, y_setting, stack_roll=False, model_name=None):
    if model_name is None:
        model_name = type(model).__name__

    def __str__():
        rolling = str(roller).replace('\t', '\t\t')
        stack_roll_str = 'Stack of roll slices' if stack_roll else 'The last roll slice'
        return ('Training for {mname}:\n'
                '\t- y: {y}\n'
                '\t- x: {x}\n'
                '\t- trained on: {stack_roll_str}\n'
                '\t- Model: {model}\n'
                '\t- {rolling}\n'
                ''.format(mname=model_name, model=model,
                          x=x_setting, y=y_setting,
                          stack_roll_str=stack_roll_str, rolling=rolling
                          )
                )

    if not stack_roll:
        dates = roller.most_recent_period()
        x, y = compile_data.gen_x_y_for_model(x_setting, y_setting, dates)
        print(x.shape, y.shape)
        model.fit(x.values, y.values.ravel())
    else:
        raise NotImplementedError('stack roll not implemented')


if __name__ == "__main__":
    import os

    if os.getcwd().endswith('src'):
        os.chdir('..')