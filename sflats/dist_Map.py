import folium
import json
from IPython.display import display
import pkg_resources


def plot_district_map(df, color_by='None'):
    """Map of the main districts.

    Because database provides data only on some Prague districts, flats in other districts are ignored.

    Parameters:
    df : pandas DataFrame created from Flats class
    color_by (str): default None, one of the 'Ppm2','Area','Price' 
         Colors districts based on value of selected feature.  
    """
    data = df.groupby(['District']).mean()
    data = data.drop('Praha')
    filepath = pkg_resources.resource_filename(__name__, './praha_casti.json')

    with open(filepath) as json_file:
        prague_geo = json.load(json_file)

    names = []
    for i in range(0, len(prague_geo['features'])):
        names.append(prague_geo['features'][i]['properties']['NAZEV_MC'])

    data = data.reindex(names)

    text = []
    for i in range(0, (data.shape[0])):
        text.append('''<b> %s </b> <br> <i> Average Flat Area: </i> %s <br> <i> Average Price per m<sup>2</sup>: </i> %s <br> <i> Average Flat Price: </i> %s''' %
                    (data.index[i], round(data['Area'][i], 2), round(data['Ppm2'][i], 2), round(data['Price'][i], 2)))

    m = folium.Map(location=[50.085, 14.45], zoom_start=11)

    if (color_by == 'Ppm2'):
        folium.Choropleth(
            geo_data=prague_geo,
            data=data,
            columns=[data.index, 'Ppm2'],
            key_on='feature.properties.NAZEV_MC',
            fill_color='YlGnBu',
            fill_opacity=0.5,
            line_opacity=0.7,
            legend_name='Average price per square meter',
            reset=True
        ).add_to(m)
    elif (color_by == 'Area'):
        folium.Choropleth(
            geo_data=prague_geo,
            data=data,
            columns=[data.index, 'Area'],
            key_on='feature.properties.NAZEV_MC',
            fill_color='YlGnBu',
            fill_opacity=0.5,
            line_opacity=0.7,
            legend_name='Average area',
            reset=True
        ).add_to(m)
    elif (color_by == 'Price'):
        folium.Choropleth(
            geo_data=prague_geo,
            data=data,
            columns=[data.index, 'Price'],
            key_on='feature.properties.NAZEV_MC',
            fill_color='YlGnBu',
            fill_opacity=0.5,
            line_opacity=0.7,
            legend_name='Average price',
            reset=True
        ).add_to(m)

    for i, j in zip(range(0, len(prague_geo['features'])), text):
        folium.GeoJson(prague_geo['features'][i], tooltip=j).add_to(m)

    display(m)
