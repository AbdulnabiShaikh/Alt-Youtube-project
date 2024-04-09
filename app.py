from flask import Flask, render_template, request, jsonify
from flask import request
import pandas as pd
import pickle
import random

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('YoutubeVideoDataset.csv')

# Load the model
with open('videos.pkl', 'rb') as f:
    model = pickle.load(f)
# Function to construct the complete YouTube URL
def construct_youtube_url(video_id):
    return f'https://www.youtube.com/watch?v={video_id}'

# Add a new column with the complete YouTube URL
df['CompleteURL'] = df['Videourl'].apply(lambda video_id: construct_youtube_url(video_id))

# Function to extract video ID from the URL
def extract_video_id(url):
    try:
        video_id = url.split('=')[-1]
        return video_id
    except:
        return None

# Add a new column with the embed URL
df['EmbedURL'] = df['CompleteURL'].apply(lambda url: f'https://www.youtube.com/embed/{extract_video_id(url)}')


# function to recommend videos from dataset 
def recommend(category):
    # Filter DataFrame by category
    category_df = df[df['Category'] == category]
    
    # Exclude the clicked video's category
    similar_videos_indices = [index for index, row in df.iterrows() if row['Category'] != category]

    # Shuffle the indices
    random.shuffle(similar_videos_indices)

    # Select top 10 randomly shuffled similar videos
    similar_videos_indices = similar_videos_indices[:10]

    # Return top 10 similar videos
    return df.iloc[similar_videos_indices]


# function to get all the recommendations, added on day 2
def get_all_recommendations():
    all_recommended_videos = pd.DataFrame()
    for category in df['Category'].unique():
        recommended_videos = recommend(category)
        if not recommended_videos.empty:
            all_recommended_videos = pd.concat([all_recommended_videos, recommended_videos], ignore_index=True)
    return all_recommended_videos

#index page
@app.route('/')
def index():
    # Shuffle the DataFrame rows to display videos in a random order each time the page is loaded
    shuffled_df = df.sample(frac=1, random_state= None)

    # Get the page number from the request or set it to 1
    page = int(request.args.get('page', 1))
    # Set the number of videos to display per page
    videos_per_page = 20
    # Calculate the start and end indices for the videos to display
    start_idx = (page - 1) * videos_per_page
    end_idx = start_idx + videos_per_page
    # Get the videos for the current page from the shuffled DataFrame
    current_videos = shuffled_df.iloc[start_idx:end_idx]

    return render_template('index.html', videos=current_videos.to_dict(orient='records'))


@app.route('/recommendations')
def show_recommendations():
    video_id = request.args.get('video_id')
    if video_id:
        video_id = str(video_id)  # Ensure video_id is a string
        filtered_df = df[df['EmbedURL'].str.contains(video_id, na=False)]
        if not filtered_df.empty:
            video_category = filtered_df.iloc[0]['Category']
            recommended_videos = recommend(video_category)
            return render_template('recommendations.html', video_id=video_id, videos=recommended_videos.to_dict(orient='records'))
    return "No recommended videos available."

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    category = data.get('Category')
    recommendations = recommend(category)
    return jsonify(recommendations.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)