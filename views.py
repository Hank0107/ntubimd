from django.shortcuts import get_object_or_404, render ,redirect
from .models import Article, Comment
from .forms import ArticleForm, CommentForm 
from django.contrib.auth.models import User
from django.core.paginator import Paginator

def article_list(request):
    articles = Article.objects.all()
    paginator = Paginator(articles, 1)  

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    comment_count = []
    for article in page_obj:
        count = Comment.objects.filter(article=article).count()
        comment_count.append(
            count
        )
    return render(request, 'article_board/article_list.html', {'page_obj': page_obj, 'comment_count': comment_count[0]})


def article_detail(request, article_id):
    print("Article ID:", article_id)  
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return render(request, 'article_board/article_not_found.html')
    return render(request, 'article_board/article_detail.html', {'article': article})

def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if request.user.is_authenticated:
            new_article = form.save(commit=False)
            new_article.author = request.user
            new_article.save()
            return redirect('article_list')
        else:
            return redirect('login')
    else:
        form = ArticleForm()        
        return render(request, 'article_board/create_article.html', {'form': form})

def update_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid() and request.user == article.author:
            form.save()
            return redirect('user_articles')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'article_board/update_article.html', {'form': form, 'article': article})

def delete_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST' and request.user == article.author:
        article.delete()
        return redirect('user_articles')
    return render(request, 'article_board/delete_article.html', {'article': article})

def author_articles(request, author_id):
    article_author = get_object_or_404(User, pk=author_id)  
    articles = Article.objects.filter(author=article_author)  
    return render(request, 'article_board/authors_articles.html', {'articles': articles, 'author': article_author})

def user_articles(request):
    articles = Article.objects.filter(author=request.user)
    return render(request, 'article_board/manage_articles.html', {'articles': articles})

def add_comment(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # 检查用户是否已登录
            if request.user.is_authenticated:
                comment = form.save(commit=False)
                comment.article = article
                comment.author = request.user
                comment.save()
                return redirect('article_detail', article_id=article_id)
            else:
                return redirect('login')  
    else:
        form = CommentForm()
    return render(request, 'article_board/article_detail.html', {'form': form, 'article': article})

# 創建模型
generation_config = {
    "temperature": 0.4,
    "top_p": 0.85,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

with open('training_data.json', 'r', encoding='utf-8') as f:
    history_data = json.load(f)


chat_session = model.start_chat(history=history_data)

@xframe_options_sameorigin
def ai_chat(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
        
        response = chat_session.send_message(user_message)
        ai_response = response.text
        ai_response_filtered = ai_response.replace('*', '')

        return JsonResponse({'response': ai_response_filtered})
    
    return render(request, 'article_board/chat.html')

