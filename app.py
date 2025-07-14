##pip install pandas streamlit altair plotly
#import the libraries
import streamlit as st
import pandas as pd
import altair
#import plotly.express as px

st.set_page_config(
    page_title="BBMP Grievances",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

altair.themes.enable("dark")

# Load CSVs directly from GitHub
df_2025 = pd.read_csv("https://raw.githubusercontent.com/bluess21/GIS/main/2025-grievances.csv")
df_2024 = pd.read_csv("https://raw.githubusercontent.com/bluess21/GIS/main/2024-grievances.csv")


# Add year column
df_2025["year"] = 2025
df_2024["year"] = 2024

df_grievances = pd.concat([df_2024, df_2025], ignore_index=True)

# Sidebar filters
with st.sidebar:
    st.title('🏂 BBMP Grievances')

    # Year selection
    year_list = sorted(df_grievances['year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", year_list)

    # Filter by year
    df_filtered = df_grievances[df_grievances['year'] == selected_year]

    # Category
    category_list = sorted(df_filtered['Category'].dropna().unique())
    selected_category = st.selectbox("Select Category", category_list)

    #Sub Category
    sub_category_list = sorted(
    df_filtered[df_filtered['Category'] == selected_category]['Sub Category'].dropna().unique()
    )
    selected_sub_category = st.selectbox("Select Sub-Category", sub_category_list)

    # Ward Name
    ward_list = sorted(df_filtered['Ward Name'].dropna().unique())
    selected_ward = st.selectbox("Select Ward", ward_list)

    # Color Theme
    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

df_filtered.head()

#Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = altair.Chart(input_df).mark_rect().encode(
            y=altair.Y(f'{input_y}:O', axis=altair.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=altair.X(f'{input_x}:O', axis=altair.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=altair.Color(f'max({input_color}):Q',
                             legend=None,
                             scale=altair.Scale(scheme=input_color_theme)),
            stroke=altair.value('black'),
            strokeWidth=altair.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    return heatmap

# Apply all filters
df_final = df_filtered[
    (df_filtered['Category'] == selected_category) &
    (df_filtered['Sub Category'] == selected_sub_category) &
    (df_filtered['Ward Name'] == selected_ward)
]

# Check that filtered data is not empty
if df_final.empty:
    st.warning("No data found for the selected filters.")
else:
    # Generate heatmap
    heatmap = make_heatmap(
        input_df=df_final,
        input_y="year",  # could be another field like 'ward_name' if needed
        input_x="sub_category",  # or whatever dimension you want on X-axis
        input_color="count",  # or the appropriate numeric field
        input_color_theme=selected_color_theme
    )

    st.altair_chart(heatmap, use_container_width=True)


import json

# Load GeoJSON for BBMP wards
with open("BBMP.geojson", "r") as file:
    wards_geojson = json.load(file)

# Your function to make the choropleth using 'ward_name'
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(
        input_df,
        geojson=wards_geojson,
        featureidkey="properties.ward_name",  # <- field from GeoJSON
        locations=input_id,                   # <- must match names exactly
        color=input_column,
        color_continuous_scale=input_color_theme,
        labels={input_column: input_column.replace('_', ' ').capitalize()}
    )

    choropleth.update_geos(
        fitbounds="locations",
        visible=False
    )

    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )

    return choropleth


# Calculate summary as before
category_counts = df_final.groupby('Ward Name')[['Category', 'Sub Category']].agg(
    lambda x: set(zip(df_final.loc[x.index, 'Category'], df_final.loc[x.index, 'Sub Category']))
).applymap(len).rename(columns={'Category': 'num_category_subcategory'})

complaint_counts = df_final.groupby('Ward Name')['Complaint ID'].nunique().reset_index()
complaint_counts = complaint_counts.rename(columns={'Complaint ID': 'num_complaints'})

summary_df = category_counts.reset_index().merge(complaint_counts, on='Ward Name')

# Display in columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🔢 Unique Categories/Sub-Categories")
    st.dataframe(summary_df[['Ward Name', 'num_category_subcategory']].sort_values(by='num_category_subcategory', ascending=False))

with col2:
    st.markdown("#### 🧾 Total Complaints")
    st.dataframe(summary_df[['Ward Name', 'num_complaints']].sort_values(by='num_complaints', ascending=False))

with col3:
    st.markdown("#### 📌 Select Ward to View Details")
    selected_ward = st.selectbox("Choose a Ward", summary_df['Ward Name'])

    ward_data = summary_df[summary_df['Ward Name'] == selected_ward]

    if not ward_data.empty:
        st.metric("Categories/Sub-Categories", int(ward_data['num_category_subcategory'].iloc[0]))
        st.metric("Total Complaints", int(ward_data['num_complaints'].iloc[0]))
    else:
        st.warning("No data found for the selected ward.")
