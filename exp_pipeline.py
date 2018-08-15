from src.e1_compile_data import CompileData
from src.e2_training import Train
from sklearn.ensemble import RandomForestClassifier

if __name__ == "__main__":
    # # SET SPATIAL UNITS
    SN = 'bnia_nbh'
    # because the number of units in BNIA is small, stack rolling as training set
    STACK_ROLL = True

    # # LOAD DATA
    DATA = CompileData(spu_name=SN, verbose=1)
    DATA.set_y('crime/shooting')
    DATA.set_x(['crime'])
    print(DATA)

    # # TRAINING PHASE
    RPS = {
        'rstep': 7,
        'rsd': '2013-07-01',
        'red': '2016-07-01',
        'tw_past': 60,
        'tw_pred': 7,
        'rback': True
    }

    # tw_past should remain the same to be compatible, but some models designed for time series(e.g., LSTM)
    # RPS['tw_past'] = None

    MNXYs = [
        ('M1', 'Mname1', 'x_setting1', 'y_setting1'),
        ('M2', 'Mname2', 'x_setting2', 'y_setting2')
    ]

    for M, N, X, Y in MNXYs:
        TR = Train(model=M, model_name=N, rps=RPS, y_setting=Y, x_setting=X, stack_roll=STACK_ROLL)
        print(TR)
