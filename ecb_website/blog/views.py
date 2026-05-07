import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .ai import generate_article_draft
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


@login_required
@require_POST
def article_ai_generate(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = request.POST

    prompt = (payload.get('prompt') or '').strip()
    if len(prompt) < 8:
        return JsonResponse({'error': 'Add a little more detail for the draft.'}, status=400)

    draft, error = generate_article_draft(prompt=prompt, user_id=request.user.pk)
    if error:
        return JsonResponse({'error': error}, status=503)

    return JsonResponse({'draft': draft})
