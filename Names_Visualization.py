import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [6.4, 4]

query_params = st.experimental_get_query_params()

first_name = 'CAMILLE'
if 'name' in query_params :
    if isinstance(query_params['name'], list): first_name = query_params['name'][0]
    else: first_name = query_params['name']
first_name = first_name.upper()

@st.cache()
def load_data(default_name='CAMILLE', first_name=first_name, remove_rare=True, remove_X=True):
    file = r"./Data/french_names_1900-2020.csv"
    df = pd.read_csv(file,delimiter=';')
    df.columns = ['sex','name','year','count']
    if remove_rare: df = df[df.name != '_PRENOMS_RARES']
    if remove_X: df = df[df.year != "XXXX"]
    unique_names = df.name.unique()
    if first_name not in unique_names: first_name = default_name
    first_name_index = int(np.where(unique_names == first_name)[0][0])
    return df, unique_names, first_name_index

name_data, unique_names, first_name_index = load_data()

def get_name_data(name, df=name_data, include_X=False):
    name_df = df[df.name == name]
    if not include_X:
        name_df = name_df[name_df.year != 'XXXX']
        name_df = name_df.astype({'year':'int32'})
    name_df = name_df.sort_values(by='year')
    return name_df
    
def plot_name(name, handle_sex='SEPARATE'):
    data=get_name_data(name)
    if handle_sex == 'SUM':
        data=data.groupby(by=['year']).sum().reset_index()
        c='tab:blue'
        plt.plot('year','count', data=data, c=c)
        plt.title(name + ' (males + females)')
        
    elif handle_sex == 'SEPARATE':
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
    fig = plt.gcf()
    st.pyplot(fig)
    
st.header('French Names by Year')
separate = st.checkbox('Separate by sex', True)
name_selected = st.selectbox('Type a name :', unique_names, first_name_index)
st.experimental_set_query_params(name=name_selected.lower())
handle_sex = 'SEPARATE' if separate else 'SUM'
plot_name(name_selected, handle_sex)

st.markdown('INSEE 2021, _Fichier des prénoms_  \n\
            <https://www.insee.fr/fr/statistiques/2540004#documentation>')

st.markdown('#')
st.header('Name Generation (coming soon)')
cols = st.columns(4)
with cols[0]:
    st.selectbox('Gender :', ['Male','Female','Neither'],0)
with cols[1]:
    st.selectbox('Period :', [str(x)+'s' for x in range(1900,2011,10)],11)
with cols[2]:
    st.selectbox('Department :', ['...'],0)
with cols[3]:
    st.markdown('#')
    st.markdown(' ')
    st.button('Generate Names', disabled=True)
