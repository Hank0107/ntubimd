from django import forms
from .models import Article, Comment

from django import forms

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']
        labels = {
            'title': '文章標題',
            'content': '文章內容',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入您想討論的標題'}),
            'content': forms.Textarea(attrs={'class': 'form-control textarea', 'placeholder': '請輸入您的內文'}),
        }

    

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

