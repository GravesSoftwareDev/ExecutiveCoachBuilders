from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.text import slugify

from .forms import ArticleForm
from .models import Article
from account.decorators import portal_section_required


@portal_section_required('can_edit_blog')
def article_list(request):
    articles = Article.objects.all().order_by('-publish')
    return render(request, 'blog/article_list.html', {'articles': articles})


@portal_section_required('can_edit_blog')
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            if not article.slug:
                article.slug = slugify(article.title)
            article.save()
            form.save_m2m()
            messages.success(request, 'Article saved.')
            return redirect('blog:article_list')
    else:
        form = ArticleForm()
    return render(request, 'blog/article_form.html', {'form': form, 'action': 'New Article'})


@portal_section_required('can_edit_blog')
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            if not article.slug:
                article.slug = slugify(article.title)
            article.save()
            form.save_m2m()
            messages.success(request, 'Article updated.')
            return redirect('blog:article_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'blog/article_form.html', {
        'form': form,
        'article': article,
        'action': f'Edit: {article.title}',
    })


@portal_section_required('can_edit_blog')
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('blog:article_list')
    return render(request, 'blog/article_confirm_delete.html', {'article': article})
