import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [6.4, 4]

query_params = st.experimental_get_query_params()

first_names = ['CAMILLE','DOMINIQUE']
if 'name' in query_params :
    if isinstance(query_params['name'], list): first_names = query_params['name']
    else: first_names = query_params['name']
for i, name in enumerate(first_names):
    first_names[i] = first_names[i].upper()

@st.cache()
def load_data(default_names=['CAMILLE','DOMINIQUE'], first_names=first_names, remove_rare=True, remove_X=True):
    file = r"./Data/french_names_1900-2020.csv"
    df = pd.read_csv(file,delimiter=';')
    df.columns = ['sex','name','year','count']
    if remove_rare: df = df[df.name != '_PRENOMS_RARES']
    if remove_X: df = df[df.year != "XXXX"]
    unique_names = df.name.unique()
    valid_names = []
    for name in first_names:
        if name in unique_names: valid_names.append(name)
    if not valid_names: # if list empty
        valid_names = default_names
    return df, unique_names, valid_names

name_data, unique_names, valid_names = load_data()

def get_name_data(name, df=name_data, include_X=False):
    name_df = df[df.name == name]
    if not include_X:
        name_df = name_df[name_df.year != 'XXXX']
        name_df = name_df.astype({'year':'int32'})
    name_df = name_df.sort_values(by='year')
    return name_df
    
def plot_name(names, handle_sex='SEPARATE'):
    n_colors = (2*len(names) +1) if handle_sex=='SEPARATE' else (len(names) +1)
    cmap = plt.cm.get_cmap('tab10', n_colors)
    # for i in range(n_colors): st.write(cmap(i))
    i=0
    for name in names:
        data=get_name_data(name)
        if handle_sex == 'SUM':
            label=name
            data=data.groupby(by=['year']).sum().reset_index()
            plt.plot('year','count', data=data, label=label, c=cmap(i))
            i+=1

        elif handle_sex == 'SEPARATE':
            for sex in data.sex.unique():
                if sex == 1:
                    label=name + ' males'
                    c=cmap(i)
                    linestyle='dashed'
                elif sex == 2:
                    label=name + ' females'
                    c=cmap(i)
                    linestyle='dotted'
                data_temp = data[data.sex==sex]
                plt.plot('year','count',data=data_temp, label=label, c=c, linestyle=linestyle)
            i+=1

        elif handle_sex in ['MALE','MALES','FEMALE','FEMALES']:
            if handle_sex in ['MALE','MALES']:
                sex=1
                label=name + ' males'
                c=cmap(i)
                title='males'
            else:
                sex=2
                label=name + ' females'
                c=cmap(i)
                title='females'
            data_temp = data[data.sex==sex]
            plt.plot('year','count',data=data_temp, label=label,c=c)
            i+=1
            
    if handle_sex=='SUM': plt.title('French names (males + females)')
    elif handle_sex=='SEPARATE': plt.title('French names (males vs females)')
    else: plt.title(f"French names ({title})")
    plt.legend(loc=(1,0))
        
    plt.xticks(np.floor(plt.xticks()[0])) # round xticks
    fig = plt.gcf()
    st.pyplot(fig)
    
st.header('French names by year')
separate = st.checkbox('Separate by sex', True)
names_selected = st.multiselect('Type names :', unique_names, valid_names)
st.experimental_set_query_params(name=names_selected)
handle_sex = 'SEPARATE' if separate else 'SUM'
plot_name(names_selected, handle_sex)

st.markdown('INSEE 2021, _Fichier des prénoms_  \n\
            <https://www.insee.fr/fr/statistiques/2540004#documentation>')
