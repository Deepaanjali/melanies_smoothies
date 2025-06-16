# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd
from urllib.parse import quote  # For URL safety

# App title
st.title(":cup_with_straw: Customize your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input for smoothie name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get data from FRUIT_OPTIONS with both columns
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'), col('SEARCH_ON')
)

# Convert Snowpark DataFrame to Pandas
pd_df = my_dataframe.to_pandas()

# Multiselect for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),  # Show fruit names
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Safe lookup of SEARCH_ON
        matching_row = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen]
        if not matching_row.empty and 'SEARCH_ON' in matching_row:
            search_on = matching_row['SEARCH_ON'].iloc[0]
        else:
            search_on = fruit_chosen  # fallback

        st.write(f"The search value for **{fruit_chosen}** is **{search_on}**.")

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Use URL-safe version of search term
        safe_search = quote(search_on.strip().lower())
        api_url = f"https://my.smoothiefroot.com/api/fruit/{safe_search}"

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            sf_data = response.json()
            st.dataframe(data=sf_data, use_container_width=True)
        except Exception as e:
            st.error(f"Could not fetch data for {fruit_chosen}. Error: {str(e)}")

    # Submit order to Snowflake
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            insert_stmt = f""" 
                INSERT INTO smoothies.public.orders(ingredients, name_on_order)
                VALUES ('{ingredients_string.strip()}', '{name_on_order}')
            """
            session.sql(insert_stmt).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Failed to submit order. Error: {str(e)}")
