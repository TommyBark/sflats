import pandas as pd
import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go
from ipywidgets import widgets
import webbrowser
from IPython.display import display

map_token = 'pk.eyJ1IjoidG9tYXM5OCIsImEiOiJjanZ6YWc5MjkwZW9nM3ltbmI5OW0wNDZlIn0.gP8ItljvkESkSvOKcE_rWQ'

def plot_map(full_df,latest_df,map_token = map_token):
    '''Plots map of all currently available flats using plotly library and mapbox maps together with various filters.
    On click website of the flat is opened.
    
    Sliders:
    Type: possible values ['1+kk','1+1','2+kk','2+1','3+kk','3+1','4+kk','4+1','5+kk','5+1','6','atypické']
    Price: in Czk, from minimum value to 20,000,000Czk , if 20,000,001Czk is selected all flats with price higher than 20M Czk are also included
    Area: in m^2, from minimum value to maximum
    Price change: in %, total price change since initial listing, from minimal change to 100%
    Listing age: Days since the scraper first found the flat
    

    Parameters:
    full_df : pandas DataFrame created from Flats class containing data from all scrapes
    latest_df : pandas DataFrame created from Flats class containing only latest data
    map_token (str): private map_token used for mapbox.com API
    '''

    df = latest_df
    full_df = full_df.set_index(['id','Date'])
    full_df = full_df.sort_values(['id','Date'])

    #Price change since initial listing
    pricechange = np.array([np.round((full_df.loc[(i,),:].tail(1)['Price'].item() / full_df.loc[(i,),:].head(1)['Price'].item() -1)*100,2) for i in df['id'] ])

    #Listing age in days
    listingage = np.array([(full_df.loc[(i,),:].tail(1).index.values[0] - full_df.loc[(i,),:].head(1).index.values[0]).astype('timedelta64[D]').astype(int) for i in df['id']])

    #Text on hover
    texts = ['{}<br>Type: {}<br>Price: {} Czk<br>Area: {} m^2 <a href="$https://www.sreality.cz/detail/prodej/byt/{}/{}/{}$"></a><br>{} Czk/m^2 <br>Listing age: {} days<br>Price change:{}%'.format(
            o,i, j, k, i,l,m,n,p,r) for i,j,k,l,m,n,o,p,r in zip(df['Type'], df['Price'], df['Area'],df['urlLoc'],df['id'],df['Ppm2'],df['Street'],listingage,pricechange)]

    #Markers are colorscaled based on price per m^2
    data = [
        dict(
            type='scattermapbox',
            lat=df['GPS Lat'],
            lon=df['GPS Lon'],
            mode='markers',
            hoverinfo='text',
            marker=go.scattermapbox.Marker(
                size=7,color = df['Ppm2'],showscale=True,cmax=300000,cmin=100, colorscale = [[0,'rgb(75, 244, 66)'],[1,'rgb(244, 65, 65)']]
            ),
            text=texts,
            customdata=list(df['id'])
        )
    ]

    layout = go.Layout(autosize=False, width=1000, height=1000, hovermode='closest', clickmode='event', mapbox=go.layout.Mapbox(
        accesstoken=map_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=50.086,
            lon=14.423
        ),
        pitch=0,
        zoom=13
    ),
    
    ) 

    #Type of flat slider
    types = ['1+kk','1+1','2+kk','2+1','3+kk','3+1','4+kk','4+1','5+kk','5+1','6','atypické']

    Typeslider = widgets.SelectionRangeSlider(
        options=types,
        index=(0,11),
        description='Type:',
        disabled=False,
        readout = True,
        orientation='horizontal',
        continuous_update=False,
        layout = widgets.Layout(width='40%', height='20px')
        
    )  

    #Price slider
    Priceslider = widgets.IntRangeSlider(
        value=[1000,10000000],
        min = 0,
        max = 20000001,
        description='Price:',
        disabled=False,
        readout = True,
        readout_format = 'd',
        orientation='horizontal',
        continuous_update=False,
        layout = widgets.Layout(width='50%', height='30px')
    )

    #Area slider
    Areaslider = widgets.IntRangeSlider(
        value=[40,100],
        min = 1,
        max = np.max(df['Area']),
        description='Area:',
        disabled=False,
        readout = True,
        readout_format = 'd',
        orientation='horizontal',
        continuous_update=False,
        layout = widgets.Layout(width='40%', height='20px')
    )

    #Age of listing
    Ageslider = widgets.IntRangeSlider(
        value=[0,20],
        min = 0,
        max = np.max(listingage),
        description='Listing age:',
        disabled=False,
        readout = True,
        readout_format = 'd',
        orientation='horizontal',
        continuous_update=False,
        layout = widgets.Layout(width='40%', height='20px')
    )

    #Price change slider
    Pricechangeslider = widgets.FloatRangeSlider(
        value=[np.floor(np.min(pricechange))/100,1.0],
        min = np.floor(np.min(pricechange))/100,
        max = 1.0,
        step=0.01,
        description='Price change:',
        disabled=False,
        readout = True,
        readout_format = '.2%',
        orientation='horizontal',
        continuous_update=False,
        layout = widgets.Layout(width='40%', height='20px')
    )
    #Number of flats after filtering
    filtered_number = widgets.IntText(
    value=len(df['Area']),
    description='No. of flats found:',
    disabled=True,
    style = {'description_width': 'initial'}
    )

    #Map figure
    fig = go.FigureWidget(data=data, layout=layout)

    # update function for updating map based on sliders
    def response(change):
        filter_list1 = [i for i in (df['Type'] >= Typeslider.value[0]) & (df['Type'] <= Typeslider.value[1])]
        if (Priceslider.value[1] == 20000001):
            filter_list2 = [i for i in (df['Price'] >= Priceslider.value[0])]
        else:
            filter_list2 = [i for i in (df['Price'] >= Priceslider.value[0]) & (df['Price'] <= Priceslider.value[1])]
        
        filter_list3 = [i for i in (df['Area'] >= Areaslider.value[0]) & (df['Area'] <= Areaslider.value[1])]
        
        filter_list4 = [i for i in (pricechange >= Pricechangeslider.value[0]*100) & (pricechange <= Pricechangeslider.value[1]*100)]
        filter_list5 = [i for i in (listingage >= Ageslider.value[0]) & (listingage <= Ageslider.value[1])]
        
        filter_list0 = np.logical_and(filter_list1,np.logical_and(filter_list2,filter_list3))
        filter_list = np.logical_and(np.logical_and(filter_list5, filter_list4),filter_list0)
        temp_df = df[filter_list]
        filtered_number.value = len(temp_df['Area'])

        temp_text = ['{}<br>Type: {}<br>Price: {} Czk<br>Area: {} m^2 <a href="$https://www.sreality.cz/detail/prodej/byt/{}/{}/{}$"></a><br>{} Czk/m^2 <br>Listing age: {} days<br>Price change:{}%'.format(
                o,i, j, k, i,l,m,n,p,r) for i,j,k,l,m,n,o,p,r in zip(temp_df['Type'], temp_df['Price'], temp_df['Area'],temp_df['urlLoc'],temp_df['id'],temp_df['Ppm2'],temp_df['Street'],listingage[filter_list],pricechange[filter_list])]

        with fig.batch_update():
            fig.data[0]['lat'] = temp_df['GPS Lat']
            fig.data[0]['lon'] = temp_df['GPS Lon']
            fig.data[0]['text'] = temp_text
            fig.data[0].marker.color = temp_df['Ppm2']
            
            
    Typeslider.observe(response,names='value')
    Priceslider.observe(response,names='value')
    Areaslider.observe(response,names='value')
    Pricechangeslider.observe(response,names='value')
    Ageslider.observe(response,names='value')
    filtered_number.observe(response,names='value')

    #function for the clicking behaviour, after clicking on point url of that flat is opened
    def open_url(trace,points,selector):
        text = trace.text[points.point_inds[0]]
        url = text.split('$')[1]
        webbrowser.open(url)

    #Add on click functionality    
    fig.data[0].on_click(open_url)

    #Add all sliders in one VBox
    container1 = widgets.VBox([Typeslider,Priceslider,Areaslider,Pricechangeslider,Ageslider,filtered_number])

    display(widgets.VBox([container1,fig]))