from setuptools import setup

setup(name='sflats',
      version='0.1',
      description='Package for scraping and analysis of flat market',
      url='https://github.com/TommyBark/sflats',
      author='TommyBark & mjartanv',
      packages=['sflats'],
      install_requires=['pandas', 'numpy', 'matplotlib',
                        'seaborn', 'folium', 'plotly', 'ipywidgets','bokeh'],
      include_package_data=True,
      zip_safe=False)
