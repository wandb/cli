import wandb
from wandb import util
chart_limit = wandb.Table.MAX_ROWS

def xy(x, y):
    data = []
    #TODO: there must be a more efficient way?
    for x_i, y_i in zip(x, y):
        data.append([x_i, y_i])
    table = wandb.Table(data=data, columns=["x", "y"])
    fields = {"fieldSettings" : {"x" : "x", "y" : "y", "run_name" : "name"}}
    return wandb.log({
                'xy' : wandb.plot_table("builtin:xy", "xy", table,  fields)})

