import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
from bokeh.palettes import Category20

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def plotquantiles(df, col, minq=0.2, maxq=0.8, n=7, plot_mean=True, plot_med=True, title='',flat_type=[]):
    ''' Plots the changes in specified quantiles through time

    Parameters:
    df : pandas DataFrame created from Flats class
    col (str): Label of feature column to be plotted
    minq (float): Lowest quantile to be displayed (0,1)
    maxq (float): Highest quantile to be displayed (0,1)
    n (int): Number of levels between minq and maxq
    plot_mean (bool): Plot mean line 
    plot_med (bool): Plot median line 
    title (str): Title of the plot, if empty col is used as title
    flat_type (list): identical to flat_type from allplots fnc but used only for creating titles of plots

    Returns:
    matplotlib.axes._subplots.AxesSubplot object
    '''
    if len(flat_type)>0:
        title = ''.join(str(i)+'/' for i in flat_type)+' '+ col + title
    
    quantiles = df.groupby('Date')[[col]].quantile(q=np.linspace(minq,maxq,n),axis=0).unstack().T
    
    pal = pal = ["#8fe2e4","#46ffa7","#1d5c5a","#9de6b0","#6b8b8b","#00b26d","#a5c4ac","#00ae8d","#00907e"]
    sns.set_palette(pal) 
    plt.locator_params(axis='y', nbins=6)
    plt.xticks(rotation=30)
    plt.ticklabel_format(style='plain', axis='y')
    
    if len(title)==0: 
        plt.title(col,fontdict={'fontsize':20})
    else:
        plt.title(title,fontdict={'fontsize':20})
    for i in range(n-1):
        plt.fill_between(quantiles.columns, quantiles.iloc[i,:].values, quantiles.iloc[i+1,:].values, alpha=0.3, color=pal[i])
    
    if plot_mean:
        mean = df.groupby('Date')[[col]].mean().unstack().T
        plt.plot(quantiles.columns, mean, color='b',label='Mean')
    if plot_med:
        med = df.groupby('Date')[[col]].quantile(q=0.5,axis=0).unstack().T
        plt.plot(quantiles.columns, med, color='r',label='Median')
        
    plt.legend()
    
    return plt.gca() 

def my_autopct(pct):
    ''' Shows labels in pie chart if the percentage is greater than 7 to prevent label clusters and overlaps.
    '''
    return ('%1.1f%%' % pct) if pct > 7 else ''

def pie_chart(data):
    ''' Creates a pie chart for flat types
    
    Parameters:
    data: pandas Dataframe created from Flats class
    
    Returns:
    matplotlib plot object
    
    '''
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=Category20[20]) 
    
    categories = data['Type'].value_counts()
    total = sum(categories)
    
    plt.subplots(figsize=(7,4))

    plt.pie(categories, autopct=my_autopct, pctdistance=0.8)
    plt.legend(labels=['%s (%1.1f%%)' % (l, (float(s) / total) * 100) for l, s in zip(categories.index, categories)],
               loc='upper left')
    plt.tight_layout()
    plt.axis('equal')
    plt.title('Flat Types')
    
    plt.show()

def allplots(df, quant=['Area', 'Price', 'Ppm2'], pie=True, flat_count=True, Ppm2_detail=True,flat_type=[]):
    ''' Plots quantile plots, pie charts, flat count plot and detail of median/mean plot

    Parameters:
    df : pandas DataFrame created from Flats class
    quant (list): List of column names to be used for quantile plots, 10th - 90th quantile are used 
    pie (bool): Plot pie chart for flat types
    flat_count (bool): Plot number of available flats through time
    Ppm2_detail (bool): Plot Ppm2 "zoom" showing only mean, median and 45th and 55th quantile
    flat_type (list): List of types of flats used for calculation, example: ['1+kk','4+kk'], if empty uses all types

    Returns:
    matplotlib plot object

    '''
    row_n = (len(quant)+pie+flat_count+Ppm2_detail)//2 + 1
    
    if len(flat_type)>0:
        df = df[df['Type'].isin(flat_type)]
    
    for i,col in enumerate(quant):
        plt.figure(1,figsize=(20,25))
        plt.subplot(row_n, 2, i+1)
        plotquantiles(df,col,0.1,0.9,9,flat_type=flat_type)
    j = i + 1
    
    if flat_count:
        plt.subplot((len(quant)+pie)//2 + 1, 2, j+1)
        plt.plot(df.groupby('Date')['Area'].count())
        plt.title('Number of available flats',fontdict={'fontsize':20})
        plt.xticks(rotation=30)
        j = j+1
    
    if Ppm2_detail:
        plt.subplot(row_n, 2, j+1)
        plotquantiles(df,'Ppm2',0.45,0.55,n=3,plot_mean=True,plot_med=True,title='detail',flat_type=flat_type)
        j = j+1
    
    if pie:
        pie_chart(df)
    
    plt.show()
