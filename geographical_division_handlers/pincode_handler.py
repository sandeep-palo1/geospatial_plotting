import os
import pandas as pd
import folium
import geopandas as gpd
import h3.api.basic_int as h3
from shapely.geometry import mapping
from folium.plugins import MarkerCluster

# Load the environment variables for file paths
data_file_path = os.getenv('DATA_FILE_PATH')
shape_file_path = os.getenv('SHAPE_FILE_PATH')
print(data_file_path, shape_file_path)

if not data_file_path or not shape_file_path:
    raise ValueError("Environment variables DATA_FILE_PATH and SHAPE_FILE_PATH must be set.")

# Load the Excel files
data = pd.read_excel(data_file_path)

# Ensure the pincode columns have the same datatype (string) and filter out NaNs
data['Pincode'] = data['Pincode'].astype(str).str.replace(r'\.0$', '', regex=True)

# Load GeoDataFrame (gdf)
gdf = gpd.read_file(shape_file_path)

# Filter gdf with combined pincodes
filtered_gdf = gdf[gdf["pincode"].isin(data['Pincode'])]

# Check if the filtered_gdf is empty
if filtered_gdf.empty:
    print("Filtered GeoDataFrame is empty. Check the pincode values and ensure they match.")
else:
    # Merge sr_data and plan_data with gdf to get lat/lng based on Pincode
    data = data.merge(gdf[['pincode', 'geometry']], left_on='Pincode', right_on='pincode', how='left')

    # Extract latitude and longitude from geometry for sr_data
    data['PLat'] = data['geometry'].apply(lambda x: x.centroid.y if x else None)
    data['PLng'] = data['geometry'].apply(lambda x: x.centroid.x if x else None)

    # Drop rows with missing geometry
    data = data.dropna(subset=['PLat', 'PLng'])

    # Convert GeoDataFrame to GeoJSON
    gdf_json = filtered_gdf.to_json()

    # Calculate the bounds of the combined extent of all geometries
    bounds = filtered_gdf.total_bounds  # This gives [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds
    bounds = [[miny, minx], [maxy, maxx]]

    # Create Folium map without initial center and zoom
    m = folium.Map(zoom_start=10)

    # Function to generate h3 hexagons
    hex_resolution = 6  # Adjust resolution to reduce computational load
    hexagons = []

    def generate_hexagons(geometry):
        if geometry.geom_type == 'Polygon':
            return h3.polyfill_geojson(mapping(geometry), hex_resolution)
        elif geometry.geom_type == 'MultiPolygon':
            hexagons = []
            for polygon in geometry.geoms:
                hexagons.extend(h3.polyfill_geojson(mapping(polygon), hex_resolution))
            return hexagons
        else:
            return []

    # Iterate over each row (polygon) in the GeoDataFrame
    for index, row in filtered_gdf.iterrows():
        geometry = row['geometry']
        hexagons.extend(generate_hexagons(geometry))

    # Convert h3 hexagons to GeoJSON with hexadecimal representation and area calculation
    hex_features = [{
        'geometry': {'type': 'Polygon', 'coordinates': [h3.h3_to_geo_boundary(h, geo_json=True)]},
        'type': 'Feature',
        'properties': {
            'hex_id': h,
            'area_km2': h3.cell_area(h, unit='km^2')
        }
    } for h in hexagons]

    # Add GeoJSON layer of polygons with tooltips showing pincode
    folium.GeoJson(gdf_json,
                   name='Polygons',
                   style_function=lambda x: {'color': 'blue', 'opacity': 0.5, 'weight': 3},
                   tooltip=folium.GeoJsonTooltip(fields=['pincode'], aliases=['Pincode:'], labels=True, sticky=True)).add_to(m)

    # Add GeoJSON layer of h3 hexagons with tooltips showing hex_id in hexadecimal and area in km^2
    folium.GeoJson(
        {'type': 'FeatureCollection', 'features': hex_features},
        name='h3 Hexes',
        style_function=lambda x: {'color': 'green', 'opacity': 0.7, 'weight': 2},
        tooltip=folium.GeoJsonTooltip(fields=['hex_id', 'area_km2'], aliases=['Hex ID', 'Area (km^2)'], labels=True, sticky=True)
    ).add_to(m)

    # Create MarkerCluster objects for sr_data and plan_data
    marker_cluster = MarkerCluster(name='Data Points').add_to(m)

    # Add points from the sr_data DataFrame to the sr_marker_cluster
    for _, row in data.iterrows():
        folium.Marker(
            location=[row['PLat'], row['PLng']],
            # popup=folium.Popup(f"Ref no: {row['Ref no']}<br>Service Center Name: {row['Service Center Name']}<br>Pincode: {row['Pincode']}<br>Category Type: {row['Category Type']}<br>Brand: {row['Brand']}<br>Process Type: {row['Process Type']}", max_width=300),
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(marker_cluster)

    # Fit the map bounds to the combined bounds of filtered geometries and points
    m.fit_bounds(bounds)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Save and display the map
    m.save('/data/pincode_map.html')
