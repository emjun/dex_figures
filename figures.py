import os
from typing import List
import pandas as pd
import altair as alt
from pandas.core.algorithms import isin
from vega_datasets import data

states_to_ids = dict()
def load_state_ids(): 
    global states_to_ids

    # State names to FIPS
    df_ids = pd.read_csv("data/state_fips.csv", header=0)
    # Map the state names to their FIPS id numbers
    states_to_ids = dict()
    states_names = df_ids['STATE_NAME']
    states_ids = df_ids['STATE']

    for i in range(len(states_names)): 
        name = states_names[i]
        id = states_ids[i]
        assert(name not in states_to_ids.keys())
        states_to_ids[name] = id

def look_up_state_id(state_name: str): 
    global states_to_ids

    return states_to_ids[state_name]
    
def wrangle_data(df: pd.DataFrame): 
    # Check properties of the dataset 
    unique_models = pd.unique(df['model'])
    print(f"Unique model names: {unique_models}")

    unique_states = pd.unique(df["state_name"]).tolist()
    assert(isinstance(unique_states, list))
    assert(len(unique_states) == 51)
    # State names to FIPS
    df_ids = pd.read_csv("data/state_fips.csv", header=0)
    # Map the state names to their FIPS id numbers
    states_to_ids = dict()
    states_names = df_ids['STATE_NAME']
    states_ids = df_ids['STATE']

    for i in range(len(states_names)): 
        name = states_names[i]
        id = states_ids[i]
        assert(name not in states_to_ids.keys())
        states_to_ids[name] = id

    ids = list()
    for s in unique_states: 
        ids.append(states_to_ids[s])
    assert(len(ids) == 51)

    # Get only 2019 data
    df_2019 = df.query("year_id == 2019")

    values = dict()
    for u in unique_models: 
        values[u] = list() 

    for s in unique_states: 
        df_state_vals = df_2019.query(f"state_name == '{s}'")
        for u in unique_models: 
            u_row = df_state_vals.query(f"model == '{u}'")
            assert(len(u_row) == 1)
            u_val = u_row.iloc[0]['mean']
            
            # Append to dictionary of values 
            values[u].append(u_val)

    # Create per total values 
    models_of_interest = ['Medicare', 'Medicaid', 'Private', 'OOP']
    aggregate_per_capita = values['Aggregate']
    for u in models_of_interest: 
        u_per_capita_data = values[u]
        assert(len(u_per_capita_data) == len(aggregate_per_capita))

        u_per_total_data = list()
        for i in range(len(u_per_capita_data)): 
            val = u_per_capita_data[i] / aggregate_per_capita[i]
            u_per_total_data.append(val)

        u_per_total_name = u + "_per_total"
        values[u_per_total_name] = u_per_total_data

    # Check length of all values in dictionary 
    for k, v in values.items(): 
        assert(isinstance(v, list))
        assert(len(v) == 51)


    # Create a new df with separate columns for all the model values 
    values['id'] = ids
    df_2019_vals = pd.DataFrame.from_dict(values)

    return df_2019_vals

# Figure 2 
# Goal: Highlight geographic patterns 
# Exhibit 2a-f: Figure with six US maps 
# Map with estimated Medicare spend per total, 2019  --> model == Medicare / model == Aggregate
# Map with estimated Medicaid spend per total, 2019  --> model == medicaid
# Map with estimated Private insurance spend per total, 2019  --> model == Private
# Map with estimated OOP and Other spend per total, 2019  --> model == OOP || Other  --> What about Other Professional?
def plot_maps(df: pd.DataFrame, models: List[str], output_filename: str):    
    df_wrangled = wrangle_data(df)

    states = alt.topo_feature(data.us_10m.url, 'states')

    chart = alt.Chart(states).mark_geoshape().encode(
        alt.Color(alt.repeat('row'), type='quantitative')
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(df_wrangled, 'id', models)
    ).properties(
        width=500,
        height=300
    ).project(
        type='albersUsa'
    ).repeat(
        row=models
    ).resolve_scale(
        color='independent'
    )
    chart.save(output_filename)



def plot_maps_wrapped_facet(df: pd.DataFrame, models: List[str], output_filename: str):    
    # Filter to only look at 2019 data
    df_2019 = df.query("year_id == 2019")
    # Filter to only look at data from specific models
    df_2019_filtered = df_2019[df_2019['model'].isin(models)]
    states = df_2019_filtered['state_name']
    res = map(look_up_state_id, states)
    df_2019_filtered['id'] = list(res)

    states = alt.topo_feature(data.us_10m.url, 'states')
    chart = alt.Chart(df_2019_filtered).mark_geoshape().encode(
    shape='geo:G',
    color='mean:Q',
    tooltip=['state_name:N', 'mean:Q'],
    facet=alt.Facet('model:N', columns=2),
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(data=states, key='id'),
        as_='geo'
    ).properties(
        width=300,
        height=175,
    ).project(
        type='albersUsa'
    )
    chart.save(output_filename)

    
# def plot_map(df, models: List[str], output_filename: str): 
    # states = alt.topo_feature(data.us_10m.url, 'states')
    # # Map with estimated health spend per capita, 2019  --> Aggregate
    # # Map with AROC total spend per capita, 2014-2019 --> AROC scores
    # chart = alt.Chart(states).mark_geoshape().encode(
    #     color='Medicare:Q'
    # ).transform_lookup(
    #     lookup='id',
    #     from_=alt.LookupData(df, 'id', ['Medicare'])
    # ).project(
    #     type='albersUsa'
    # ).properties(
    #     width=500,
    #     height=300
    # )
    # chart.save('states.html')

def plot_stacked_bar_chart(df: pd.DataFrame, models: List[str], output_filename: str):
    df_filtered = df.loc[df['model'].isin(models)]
    chart = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X('sum(mean)', stack="normalize"),
        y='state_name',
        color='model'
    )
    chart.save(output_filename)


if __name__ == "__main__": 
    # Load state ids global dict
    load_state_ids()

    # Load flat file 
    # TODO: Take the CSV in as an argument
    file_path = os.path.relpath("data/compiled_final_results.csv")
    df = pd.read_csv(file_path, header=0)
    # variables = ['location_id','year_id','state_name','mean','lower','upper','data','model']
    # Exhibit 2a
    models_of_interest = ['Aggregate']
    plot_maps(df, models_of_interest, "aggregate_map.html")

    # Exhibit 2b-e, maps
    models_of_interest = ['Medicare_per_total', 'Medicaid_per_total', 'Private_per_total', 'OOP_per_total']
    plot_maps(df, models_of_interest, "all_maps.html")
    models_of_interest = ['Medicare', 'Medicaid', 'Private', 'OOP']
    plot_maps_wrapped_facet(df, models_of_interest, "all_maps_faceted.html")
    
    # Exhibit 2b-e, stacked bar
    models_of_interest = ['Dental','Home health','Hospital','Skilled nursing','Other professional','Other','Pharmaceuticals', 'Physician/clinical services','Medicaid','Medicare','OOP','Private']
    plot_stacked_bar_chart(df, models_of_interest, "stacked_bar.html")
    models_of_interest = ['Medicare', 'Medicaid', 'Private', 'OOP']
    plot_stacked_bar_chart(df, models_of_interest, "stacked_bar_selected.html")


# Figure 3 
# Exhibit 3a-c: Three densities showing growth in spending per capita of total, Medicaid, and Non-Medicaid, with two densities per panel – expansion and non-Medicaid expansion. (Sawyer has code for something similar to this.) Like this but only three of the six panels. à Goal: show that growth rates for expanders and non-expanders weren’t that different.  

# Figure 3 Alternative 
# Box and whisker plot 