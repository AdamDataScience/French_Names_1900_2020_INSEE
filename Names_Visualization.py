import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

@st.cache()
def load_data(remove_rare=True):
    file = r"./Data/french_names_1900-2020.csv"
    df = pd.read_csv(file,delimiter=';')
    df.columns = ['sex','name','year','count']
    if remove_rare: df = df[df.name != '_PRENOMS_RARES']
    unique_names = df.name.unique()
    return df, unique_names

name_data, unique_names = load_data()

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
        plt.plot('year','count', data=data)
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
        
    fig = plt.gcf()
    st.pyplot(fig)
    
name_selected = st.selectbox('Choose a name...', unique_names)
plot_name(name_selected, 'SEPARATE')
