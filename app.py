import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import zipfile
import base64
import matplotlib.pyplot as plt

# Function to fetch inscriptions data from ordinals.com
def fetch_inscriptions(url):
    response = requests.get(url)
    if response.status_code == 200:
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
        most_viewed_inscriptions = filter_and_sort_inscriptions(inscriptions)
        
        if most_viewed_inscriptions:
            st.write(f"Found {len(most_viewed_inscriptions)} inscriptions in the last 24 hours.")
            
            # Convert to DataFrame for easy manipulation
            df = pd.DataFrame(most_viewed_inscriptions)
            
            # Display DataFrame
            st.dataframe(df)
            
            # Download CSV link
            st.markdown(get_table_download_link(df), unsafe_allow_html=True)
            
            # Display charts
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
            
            # Prepare images for zip download
            images = [(ins['image_url'], ins['title']) for ins in most_viewed_inscriptions]
            st.markdown(get_zip_download_link(images), unsafe_allow_html=True)
            
            # Display the most viewed inscriptions
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
\
