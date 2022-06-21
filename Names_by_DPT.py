import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import json
# from geopy.geocoders import Nominatim # only to obtain variable location coordinates
# import geopandas as gpd...
import folium
from streamlit_folium import folium_static
from st_aggrid import AgGrid
import zipfile

import matplotlib as mpl
dpi = 81 # average dpi
ratio = 1.2
width = 550
height = width/ratio
map_offset_height = 20
# map_offset_width = map_offset_height*ratio
mpl.rcParams['figure.figsize'] = [width/dpi,height/dpi]

st.set_page_config(
     page_title="French Names by Year & Department",
#      page_icon="🧊",
     layout="wide",
#      initial_sidebar_state="expanded",
     menu_items={
#          'Get Help': 'https://www.extremelycoolapp.com/help',
#          'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "## https://adam-data-science.wixsite.com/portfolio"
     }
 )

query_params = st.experimental_get_query_params()

# PLOT

first_name = 'CAMILLE'
if 'name' in query_params :
    if isinstance(query_params['name'], list): first_name = query_params['name'][0]
    else: first_name = query_params['name']
first_name = first_name.upper()

@st.cache()
def load_data(default_name='CAMILLE', remove_rare=True, remove_X=True): # first_name=first_name
#      file = r"./Data/french_names_1900-2020.csv"
     file = r"dpt2020.csv"
     file_zip = r"./Data/dpt2020_csv.zip"
     zf = zipfile.ZipFile(file_zip)
     #     with open(file) as f:
     df = pd.read_csv(zf.open(file),delimiter=';')
     #     df = pd.read_csv(file,delimiter=';')
     df.columns = ['sex','name','year','dpt','count']
     if remove_rare: df = df[df.name != '_PRENOMS_RARES']
     if remove_X:
        df = df[df.year != "XXXX"]
        df = df[df.dpt != "XX"]
        df = df.astype({'year':'int32'})
     unique_names = df.name.unique()
     df = df.sort_values(by='year')
     dpt_pop_file = r"./Data/French_dpt_population.csv"
     dpt_pop = pd.read_csv(dpt_pop_file,delimiter=',', index_col=None)
#      dpt_pop.columns = ['dpt_name','dpt','pop']
     dpt_pop = dpt_pop.drop(columns=['dpt_name'])
     return df, unique_names, dpt_pop # first_name_index

name_data, unique_names, dpt_pop = load_data() # first_name_index
# st.write(dpt_pop)

if first_name not in unique_names: first_name = default_name
first_name_index = int(np.where(unique_names == first_name)[0][0])

def get_name_data(name, df=name_data, include_X=False):
    name_df = df[df.name == name]
#     if not include_X:
#         name_df = name_df[name_df.year != 'XXXX']
#         name_df = name_df.astype({'year':'int32'})
#     name_df = name_df.sort_values(by='year')
    # fill missing years with 0:
    new_index = pd.MultiIndex.from_product([range(1900,2021,1),name_df.dpt.unique(),name_df.sex.unique()], names=['year','dpt','sex'])
    name_df = name_df.set_index(['year','dpt','sex'])
    name_df = name_df.reindex(new_index, fill_value=0).reset_index()
#     st.write(name_df.astype(str))
    return name_df
    
def plot_name(name, data, handle_sex='SEPARATE'):
#     data=get_name_data(name)
    if handle_sex == 'SUM':
        data=data.groupby(by=['year']).sum().reset_index()
        c='tab:blue'
        plt.plot('year','count', data=data, c=c)
        plt.title(name + ' (males + females)')
        
    elif handle_sex == 'SEPARATE':
        data=data.groupby(by=['year','sex']).sum().reset_index()
        for sex in data.sex.unique():
            if sex == 1:
                label='males'
                c='deepskyblue'
            elif sex == 2:
                label='females'
                c='pink'
            data_temp = data[data.sex==sex]
            plt.plot('year','count',data=data_temp, label=label,c=c)
        plt.title(name + ' (males vs females)')
        plt.legend()
        
    elif handle_sex in ['MALE','MALES','FEMALE','FEMALES']:
        data=data.groupby(by=['year','sex']).sum().reset_index()
        if handle_sex in ['MALE','MALES']:
            sex=1
            label='males'
            c='deepskyblue'
            title='males'
        else:
            sex=2
            label='females'
            c='pink'
            title='females'
        data_temp = data[data.sex==sex]
        plt.plot('year','count',data=data_temp, label=label,c=c)
        plt.title(f"{name} ({title})")
        plt.legend()
        
    plt.xticks(np.floor(plt.xticks()[0])) # round xticks
    plt.yticks(np.floor(plt.yticks()[0]))
    fig = plt.gcf()
    st.pyplot(fig)
    
st.header('French Names by Year & Department')
separate = st.checkbox('Separate by gender', True)
name_selected = st.selectbox('Type a name :', unique_names, first_name_index)
handle_sex = 'SEPARATE' if separate else 'SUM'

cols = st.columns(2)
with cols[0]:
    data=get_name_data(name_selected)
    plot_name(name_selected, data, handle_sex)
st.experimental_set_query_params(name=name_selected.lower())

# MAP

# @st.cache()
def load_map_data():
    geojson_file = r"./Data/france_departments_corse_merged.json"
    with open(geojson_file) as f:
        geojson = json.load(f)
    return geojson

map_name_data = data.groupby(['dpt']).sum().drop(columns=['sex','year']).reset_index()
# st.write(map_name_data)

# fill absent dpts with 0
new_index = pd.Index(np.arange(1,96,1), name='dpt',dtype=str).append(pd.Index([971,972,973,974], name='dpt',dtype=str))
new_index = new_index.str.zfill(2)
map_name_data = map_name_data.set_index(['dpt']).reindex(new_index,fill_value=0).reset_index()
# merge with dpt population:
map_name_data = pd.merge(map_name_data.astype({'dpt':int}), dpt_pop.astype({'dpt':int}), how='inner', on='dpt')
# get percentage of pop
map_name_data['prop'] = ((map_name_data['count'].astype(float) / map_name_data['pop'].astype(float)) *100) # .astype(int)
map_name_data.dpt = map_name_data.dpt.astype(str).str.zfill(2)
# with cols[1]: st.write(map_name_data)
    
geojson = load_map_data()
# add count to geojson data:
# with cols[1]: st.write(len(geojson['features']))
for idx in range(len(geojson['features'])): # 95
     geojson['features'][idx]['properties']['name'] = name_selected.title()
     geojson['features'][idx]['properties']['count'] = int(map_name_data['count'][idx])
     geojson['features'][idx]['properties']['population'] = int(map_name_data['pop'][idx])
     geojson['features'][idx]['properties']['proportion'] = float(map_name_data['prop'][idx])
    

# # find arbitrary country/city's coordinates:
# # from geopy.geocoders import Nominatim
# @st.cache()
# def get_center():
#    address = 'France'
#    geolocator = Nominatim(user_agent="id_explorer")
#    location = geolocator.geocode(address)
#    return location.latitude, location.longitude

# center = get_center()

# instead, enter them manually for France:
center = (46.603354, 1.8883335)

tiles = ['OpenStreetMap', 'Stamen Terrain','Stamen Toner','CartoDB positron'][3]

map = folium.Map(tiles=tiles, location=center, width='100%', height='100%', zoom_start=5, max_bounds=True, name='France Names')
# with cols[1]: folium_static(map)

threshold = np.linspace(map_name_data['prop'].min(), map_name_data['prop'].max(), 10, dtype=float).tolist()
# st.write(threshold)

map_layer = folium.Choropleth(geo_data=geojson, data=map_name_data, columns=['dpt','prop'],
                              key_on='feature.properties.code',
                              threshold_scale=threshold,
                              fill_color='YlOrRd', fill_opacity=0.7, line_opacity=1,
                              legend_name=f""""{name_selected}" name count by department""",
                              highlight=True, reset=True, name='Count Overlay'
                              )#.add_to(map)

# remove layer from layer control button:
# map_layer.control=False

# remove legend:
for key in map_layer._children:
#     print(key)
    if key.startswith('color_map'):
#         pass
        del(map_layer._children[key])
# folium.LayerControl(name='France Names').add_to(map)
map_layer.add_to(map)


folium.LayerControl(name='France Names').add_to(map)
map_layer.geojson.add_child(folium.features.GeoJsonTooltip
                                (fields=['name','count','nom','population','proportion'],
                                aliases=['Name :','Count :','Department :','Population :','Proportion (%) :'],
                                labels=True))

# # add map title not working
# loc = 'Corpus Christi'
# title_html = f'''
#              <h3 align="center" style="font-size:16px"><b>{name_selected} in France Departments</b></h3>
#              '''.format(loc)
# map.get_root().html.add_child(folium.Element(title_html))

with cols[1]:
#      st.markdown(f"{name_selected.title()} in France Departments")
#      st.markdown('')
     folium_static(map, width=width, height=height-map_offset_height)


# SOURCE

cols = st.columns(2)
with cols[0]:
     st.markdown('INSEE 2021, _Fichier des prénoms_  \n\
            <https://www.insee.fr/fr/statistiques/2540004#documentation>')

with cols[1]:
     st.markdown('Note : French Overseas Departments (DOM-TOM / DROM-COM) omitted')


# QUERY

st.markdown('#')
st.header('Name Search (coming soon)')

with st.form('search_form'):
     cols = st.columns(4)
     with cols[0]:
          search_gender = st.selectbox('Gender :', ['Both','Male','Female'],0, key='search_gender')
     with cols[1]:
          search_period = st.selectbox('Period :', [str(x)+'s' for x in range(1900,2011,10)],11, key='search_period')
     with cols[2]:
          search_dpt = st.selectbox('Department :', ['...'],0, key='search_dpt')
     with cols[3]:
#          st.checkbox('Only show original names',True)
#          st.markdown('#')
#          st.markdown(' ')
          search_number = st.number_input('Number of names :', 1,100,5,1, key='search_number')
#           search_button = st.button('Search Names', key='search_button', disabled=True)
          search_button = st.form_submit_button('Search Names') # ,key='search_button',disabled=False)
if search_button:
#      st.write(name_data.head(search_number))
     grid = AgGrid(name_data.head(search_number), editable=True)


# GENERATION

st.markdown('#')
st.header('Name Generation (coming soon)')
with st.form('gen_form'):
     cols = st.columns(4)
     with cols[0]:
         st.selectbox('Gender :', ['Male','Female','Neither'],0)
     with cols[1]:
         st.selectbox('Period :', [str(x)+'s' for x in range(1900,2011,10)],11)
     with cols[2]:
         st.selectbox('Department :', ['...'],0)
     with cols[3]:
          gen_number = st.number_input('Number of names :', 1,100,5,1, key='gen_number')
          st.checkbox('Only show original names',True)
     #     st.markdown('#')
     #     st.markdown(' ')
#          st.button('Generate Names', disabled=True)
          gen_button = st.form_submit_button('Generate Names') # ,key='gen_button',disabled=False)
if gen_button:
#      pass
#      st.write(name_data.head(gen_number))
     grid = AgGrid(name_data.head(search_number), editable=False)

     
     
# CREDITS

st.markdown('#')
st.markdown('Author : Adam M.  \n\
               https://adam-data-science.wixsite.com/portfolio')
