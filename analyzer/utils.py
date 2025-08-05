import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
nltk.download('stopwords')
from nltk.corpus import stopwords
from wordcloud import WordCloud
from collections import Counter
import io 
import matplotlib.pyplot as plt
import base64

sia = SentimentIntensityAnalyzer()

def extract_video_id(url):
    match = re.search(r"(?:v=|\/live\/|youtu\.be\/|\/embed\/|\/v\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def clean_comment(comment):
    from nltk.corpus import stopwords
    import re
    stop_words = set(stopwords.words('english'))
    comment = re.sub(r'<.*?>', '', comment)
    comment = re.sub(r'http\S+', '', comment)
    comment = re.sub(r'[^A-Za-z\s]+', '', comment)
    comment = comment.lower().strip()
    words = comment.split()
    return ' '.join([w for w in words if w not in stop_words])

def get_sentiment(comment):
    score = sia.polarity_scores(comment)['compound']
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    return "Neutral"

def get_comments(video_id):
    from googleapiclient.discovery import build
    api_key = 'AIzaSyDV9kcpMoTthsm8fHdT5lA_5Kld1ZaFx6Q'
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments, likes = [], []
    token = None

    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=token,
            textFormat='plainText'
        ).execute()

        for item in response['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comments.append(snippet['textDisplay'])
            likes.append(snippet.get('likeCount', 0))

        token = response.get('nextPageToken')
        if not token:
            break
    return comments, likes

def generate_pdf(df, summary):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="YouTube Sentiment Report", ln=True, align='C')
    pdf.ln(10)

    total = len(df)
    pdf.cell(200, 10, txt=f"Total Comments: {total}", ln=True)
    for sentiment, count in summary.items():
        pdf.cell(200, 10, txt=f"{sentiment}: {count}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt="Top 5 Comments:", ln=True)
    for i in range(min(5, total)):
        row = df.iloc[i]
        pdf.multi_cell(0, 10, f"{i+1}. [{row['Sentiment']}] {row['Comment']} (Likes: {row['Likes']})")

    pdf.output("sentiment_report.pdf")
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return image_base64

# ✅ Word cloud image (returns two base64 strings)
def generate_wordclouds(df):
    positive_text = ' '.join(df[df['Sentiment'] == 'Positive']['Cleaned'])
    negative_text = ' '.join(df[df['Sentiment'] == 'Negative']['Cleaned'])

    wc_pos = WordCloud(width=800, height=400, background_color='white').generate(positive_text)
    wc_neg = WordCloud(width=800, height=400, background_color='white').generate(negative_text)

    fig_pos, ax1 = plt.subplots()
    ax1.imshow(wc_pos, interpolation='bilinear')
    ax1.axis('off')
    ax1.set_title("Positive Comments WordCloud")

    fig_neg, ax2 = plt.subplots()
    ax2.imshow(wc_neg, interpolation='bilinear')
    ax2.axis('off')
    ax2.set_title("Negative Comments WordCloud")

    return fig_to_base64(fig_pos), fig_to_base64(fig_neg)

# ✅ Bar chart of top N words in a sentiment category
def generate_common_words_bar(df, sentiment_type="Positive", top_n=10):
    text = ' '.join(df[df['Sentiment'] == sentiment_type]['Cleaned'])
    words = text.split()
    word_freq = Counter(words)
    common_words = word_freq.most_common(top_n)

    words = [w for w, _ in common_words]
    counts = [c for _, c in common_words]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(words, counts, color='blue')
    ax.set_title(f"Top {top_n} Words in {sentiment_type} Comments")
    plt.xticks(rotation=45)
    
    return fig_to_base64(fig)