from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .utils import get_comments, clean_comment, get_sentiment, extract_video_id, generate_common_words_bar, generate_wordclouds
from collections import Counter
import pandas as pd
from django.http import HttpResponse
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('register')
@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def analyze(request):
    if request.method == 'POST':
        url = request.POST.get('youtube_url')
        video_id = extract_video_id(url)
        comments, likes = get_comments(video_id)
        cleaned = [clean_comment(c) for c in comments]
        sentiments = [get_sentiment(c) for c in cleaned]
        df = pd.DataFrame({
            'Comment': comments,
            'Cleaned': cleaned,
            'Sentiment': sentiments,
            'Likes': likes
        })
        # Visuals
        wordcloud_pos, wordcloud_neg = generate_wordclouds(df)
        top_words_pos = generate_common_words_bar(df, "Positive")
        top_words_neg = generate_common_words_bar(df, "Negative")

        summary = df['Sentiment'].value_counts().to_dict()
        request.session['summary'] = summary
        request.session['df'] = df.to_dict(orient='records')   
        # 🔥 Generate Matplotlib pie chart
        fig, ax = plt.subplots()
        labels = summary.keys()
        sizes = summary.values()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

        # 🔥 Convert plot to image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()

        return render(request, 'results.html', {
            'summary': summary,
            'df': df.to_dict(orient='records'),
            'chart': graphic,
            'wordcloud_pos': wordcloud_pos,
            'wordcloud_neg': wordcloud_neg,
            'top_words_pos': top_words_pos,
            'top_words_neg': top_words_neg
            
        })
      
        return render(request, 'results.html', {'summary': summary, 'df': df})
    return redirect('home')

@login_required

def download_pdf(request):
    df_records = request.session.get('df')
    summary = request.session.get('summary')

    if df_records is None or summary is None:
        return HttpResponse("No data to generate PDF. Please analyze comments first.")

    df = pd.DataFrame(df_records)

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

    # ✅ Write PDF content to a bytes buffer
    pdf_bytes = pdf.output(dest='S').encode('latin-1')  # Convert to bytes
    buffer = io.BytesIO(pdf_bytes)
    

    # ✅ Send as downloadable file
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sentiment_report.pdf"'
    return response


# Create your views here.
