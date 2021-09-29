import pandas as pd
import altair as alt
from pandas.core.algorithms import isin
from vega_datasets import data


# Load flat file 
# mean is per capita space
df = pd.read_csv("data/compiled_final_results.csv")
variables = ['location_id','year_id','state_name','mean','lower','upper','data','model']

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
# for id in df_ids: 
#     state_name = id[2] # 'STATE_NAME'
#     state_id = id[0] # 'STATE'
#     import pdb; pdb.set_trace()
#     assert(state_name not in states_to_ids.keys())
#     states_to_ids[state_name] = state_id

ids = list()
for s in unique_states: 
    ids.append(states_to_ids[s])
assert(len(ids) == 51)

# Figure 2 
# Goal: Highlight geographic patterns 
# Exhibit 2a-f: Figure with six US maps 

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

# Check length of all values in dictionary 
for k, v in values.items(): 
    assert(isinstance(v, list))
    assert(len(v) == 51)
# Create a new df with separate columns for all the model values 
values['id'] = ids
df_2019_vals = pd.DataFrame.from_dict(values)

# Map with estimated health spend per capita, 2019  --> ???
# Map with estimated Medicare spend per total, 2019  --> model == Medicare
# Map with estimated Medicaid spend per total, 2019  --> model == medicaid
# Map with estimated Private insurance spend per total, 2019  --> model == Private
# Map with estimated OOP and Other spend per total, 2019  --> model == OOP || Other  --> What about Other Professional?
# Map with AROC total spend per capita, 2014-2019 --> ???

states = alt.topo_feature(data.us_10m.url, 'states')
variable_list = ['Medicare', 'Medicaid', 'Private', 'OOP']

# chart = alt.Chart(states).mark_geoshape().encode(
#     color='Medicare:Q'
# ).transform_lookup(
#     lookup='id',
#     from_=alt.LookupData(df_2019_vals, 'id', ['Medicare'])
# ).project(
#     type='albersUsa'
# ).properties(
#     width=500,
#     height=300
# )
# chart.save('states.html')

chart = alt.Chart(states).mark_geoshape().encode(
    alt.Color(alt.repeat('row'), type='quantitative')
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(df_2019_vals, 'id', variable_list)
).properties(
    width=500,
    height=300
).project(
    type='albersUsa'
).repeat(
    row=variable_list
).resolve_scale(
    color='independent'
)
chart.save('all_maps.html')



# Figure 3 
# Exhibit 3a-c: Three densities showing growth in spending per capita of total, Medicaid, and Non-Medicaid, with two densities per panel – expansion and non-Medicaid expansion. (Sawyer has code for something similar to this.) Like this but only three of the six panels. à Goal: show that growth rates for expanders and non-expanders weren’t that different.  

# Figure 3 Alternative 
# Box and whisker plot 


# Figure 4 
# Goal: Show many different regression results in an intuitive way. 


# Questions
# Why is Data is missing for some models? 