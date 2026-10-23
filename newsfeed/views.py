from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from communities.models import Membership
from notifications.services import notify
from .models import Post,Comment,Report
from .forms import PostForm,CommentForm,ReportForm
from django.urls import reverse
from django.db import transaction
from verification.models import VerificationQuestion

def accessible_post(user,pk):
    return get_object_or_404(Post.objects.filter(community__memberships__user=user).distinct(),pk=pk)
@login_required
def feed(request):
    posts = (
        Post.objects
        .filter(community__memberships__user=request.user)
        .select_related('community', 'user')
        .prefetch_related('comments__user')
        .distinct()
    )

    kind = request.GET.get('type')

    if kind in ('lost', 'found'):
        posts = posts.filter(type=kind)

    q = request.GET.get('q', '').strip()

    if q:
        posts = posts.filter(
            Q(caption__icontains=q) |
            Q(description__icontains=q)
        )

    return render(request, 'newsfeed/feed.html', {
        'posts': posts,
        'selected_type': kind,
        'search_query': q,
    })

@login_required
def create(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        user=request.user
    )

    max_questions = 5

    if request.method == "POST":

        questions = []

        for i in range(1, max_questions + 1):
            question = request.POST.get(
                f"question_{i}", ""
            ).strip()

            if question:
                questions.append(question)

        # Check for overly long questions
        if any(len(q) > 300 for q in questions):
            form.add_error(
                None,
                "Each verification question must be "
                "300 characters or fewer."
            )

        if form.is_valid():

            with transaction.atomic():

                # Step 1: Save post details
                post = form.save(commit=False)
                post.user = request.user
                post.save()

                # Step 2: Save optional questions
                for question in questions:
                    VerificationQuestion.objects.create(
                        post=post,
                        question=question
                    )

            messages.success(
                request,
                "Your post has been published successfully!"
            )

            return redirect(
                "post_detail",
                pk=post.pk
            )

    saved_questions = []

    for i in range(1, max_questions + 1):
        saved_questions.append({
            "number": i,
            "value": (
                request.POST.get(f"question_{i}", "")
                if request.method == "POST"
                else ""
            )
        })

    return render(
        request,
        "newsfeed/create.html",
        {
            "form": form,
            "questions": saved_questions,
            "max_questions": max_questions,
        }
    )
@login_required
def detail(request,pk):
    post=accessible_post(request.user,pk)
    return render(request,'newsfeed/detail.html',{'post':post,'comments':post.comments.select_related('user'),'comment_form':CommentForm()})
@login_required
@login_required
@require_POST
def comment(request, pk):
    post = accessible_post(request.user, pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        obj = form.save(commit=False)
        obj.post = post
        obj.user = request.user
        obj.save()

        if post.user_id != request.user.id:
            notify(
                post.user,
                f'{request.user.username} commented on your post.',
                post
            )
    else:
        messages.error(request, 'Please enter a valid comment.')

    if request.POST.get('from_feed') == '1':
        return redirect(reverse('feed') + f'#post-{pk}')

    return redirect('post_detail', pk=pk)
@login_required
def report(request,pk):
    post=accessible_post(request.user,pk)
    if post.user_id==request.user.id: raise Http404()
    form=ReportForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False);obj.user=request.user;obj.post=post
        if Report.objects.filter(user=request.user,post=post).exists():
            messages.warning(request,'You already reported this post.')
        else:
            obj.save();messages.success(request,'Report submitted to moderators.')
        return redirect('post_detail',pk=pk)
    return render(request,'generic_form.html',{'form':form,'heading':'Report post','submit_label':'Submit report'})
@login_required
@require_POST
def status(request,pk):
    post=accessible_post(request.user,pk)
    if post.user_id!=request.user.id: raise Http404()
    choice=request.POST.get('status')
    if choice in ['open','returned','closed']:
        post.status=choice;post.save(update_fields=['status']);messages.success(request,'Status updated.')
    return redirect('post_detail',pk=pk)
