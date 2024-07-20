import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import zipfile
import base64
import matplotlib.pyplot as plt
import numpy as np
import time
import pydeck as pdk
from urllib.error import URLError

# Cache the data fetching function
@st.cache_data
def fetch_inscriptions(url):
    st.write(f"Fetching data from {url}...")  # Debug info
    response = requests.get(url)
    if response.status_code == 200:
        st.write("Data fetched successfully.")  # Debug info
        return response.json()
    else:
        st.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return []

# Function to filter inscriptions from the last 24 hours and sort by views
def filter_and_sort_inscriptions(inscriptions):
    last_24_hours = datetime.now() - timedelta(hours=24)
    filtered_inscriptions = [
        ins for ins in inscriptions 
        if datetime.fromisoformat(ins['created_at']) > last_24_hours
    ]
    sorted_inscriptions = sorted(filtered_inscriptions, key=lambda x: x['views'], reverse=True)
    return sorted_inscriptions

# Function to download data as CSV
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="inscriptions.csv">Download CSV File</a>'
    return href

# Function to download images as a zip file
def get_zip_download_link(images):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, (img_url, img) in enumerate(images):
            img_data = requests.get(img_url).content
            img_name = f"image_{i}.png"
            zip_file.writestr(img_name, img_data)
    
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="images.zip">Download Images Zip</a>'
    return href

# Fetch example data for map layers
@st.cache_data
def from_data_file(filename):
    url = (
        "https://raw.githubusercontent.com/streamlit/"
        "example-data/master/hello/v1/%s" % filename
    )
    return pd.read_json(url)

# Streamlit UI
st.title('Most Viewed Inscriptions in the Last 24 Hours')

st.markdown(
    """
    <script>
    document.querySelectorAll('input[type="text"]')[0].setAttribute('autocomplete', 'url');
    </script>
    """,
    unsafe_allow_html=True
)

url = st.text_input('Enter URL for inscriptions data', value='https://ordinals.com/api/inscriptions', autocomplete='url')
if url:
    inscriptions = fetch_inscriptions(url)
    if inscriptions:
        st.write(f"Number of inscriptions fetched: {len(inscriptions)}")  # Debug info
        most_viewed_inscriptions = filter_and_sort_inscriptions(inscriptions)
        
        if most_viewed_inscriptions:
            st.write(f"Found {len(most_viewed_inscriptions)} inscriptions in the last 24 hours.")
            
            df = pd.DataFrame(most_viewed_inscriptions)
            
            st.dataframe(df)
            
            st.markdown(get_table_download_link(df), unsafe_allow_html=True)
            
            st.subheader("Views Distribution")
            fig, ax = plt.subplots()
            df['views'].plot(kind='hist', bins=20, ax=ax)
            ax.set_title("Views Distribution")
            st.pyplot(fig)

            st.subheader("Top 10 Most Viewed Inscriptions")
            top_10_df = df.head(10)
            fig, ax = plt.subplots()
            top_10_df.plot(kind='bar', x='title', y='views', ax=ax)
            ax.set_title("Top 10 Most Viewed Inscriptions")
            ax.set_xlabel("Title")
            ax.set_ylabel("Views")
            st.pyplot(fig)
            
            st.subheader("Category Distribution")
            if 'category' in df.columns:
                category_counts = df['category'].value_counts()
                fig, ax = plt.subplots()
                category_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
                ax.set_title("Category Distribution")
                ax.set_ylabel('')
                st.pyplot(fig)
            else:
                st.write("No category data available.")
            
            images = [(ins['image_url'], ins['title']) for ins in most_viewed_inscriptions]
            st.markdown(get_zip_download_link(images), unsafe_allow_html=True)
            
            for ins in most_viewed_inscriptions:
                st.write(f"**Title:** {ins['title']}")
                st.write(f"**Views:** {ins['views']}")
                st.write(f"**Created At:** {ins['created_at']}")
                st.image(ins['image_url'], caption=ins['title'])
                st.write("---")
        else:
            st.write("No inscriptions found in the last 24 hours.")
    else:
        st.write("No data available.")

# Interactive elements for fractal generation
iterations = st.sidebar.slider("Level of detail", 2, 20, 10, 1)
separation = st.sidebar.slider("Separation", 0.7, 2.0, 0.7885)

# Progress bar and placeholders for fractal generation
progress_bar = st.sidebar.progress(0)
frame_text = st.sidebar.empty()
image = st.empty()

# Fractal generation parameters
m, n, s = 960, 640, 400
x = np.linspace(-m / s, m / s, num=m).reshape((1, m))
y = np.linspace(-n / s, n / s, num=n).reshape((n, 1))

for frame_num, a in enumerate(np.linspace(0.0, 4 * np.pi, 100)):
    # Update progress bar and frame text
    progress_bar.progress(frame_num)
    frame_text.text(f"Frame {frame_num + 1}/100")

    # Fractal generation
    c = separation * np.exp(1j * a)
    Z = np.tile(x, (n, 1)) + 1j * np.tile(y, (1, m))
    C = np.full((n, m), c)
    M = np.full((n, m), True, dtype=bool)
    N = np.zeros((n, m))

    for i in range(iterations):
        Z[M] = Z[M] * Z[M] + C[M]
        M[np.abs(Z) > 2] = False
        N[M] = i

    # Update the image placeholder
    image.image(1.0 - (N / N.max()), use_column_width=True)

# Clear the progress bar and frame text
progress_bar.empty()
frame_text.empty()

# Re-run button
st.button("Re-run")

