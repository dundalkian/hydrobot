import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import data

def plot():
    all_drinks = data.get_drinks()
    drink_dict = {} #keys are id's, values are a list of timestamps
    for i in all_drinks:
        if i[1] in drink_dict:
            drink_dict[i[1]].append(i[2])
        else:
            drink_dict[i[1]] = [i[2]]
    drink_time_series = Series([i[2] for i in all_drinks], name='Drink_Time')
    df = DataFrame(drink_time_series)
    count = drink_time_series.size
    ones = np.ones(count, dtype=int)
    df['Counts'] = ones
    grouped = df.groupby('Drink_Time').count()

    fig = plt.figure()
    fig.suptitle('Scatter Plot', fontsize=14, fontweight='bold')
    ax = fig.add_subplot(111)
    fig.subplots_adjust(top=0.85)

    ax.set_xlabel('Request Time')
    ax.set_ylabel('Request Count')
    x = grouped.index
    y = grouped.values
    ax.plot_date(x, y, xdate=True, ydate=False, color='skyblue')
    plt.show()


plot()
