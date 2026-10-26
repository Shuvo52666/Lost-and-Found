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
from django.db.models import Q
from communities.models import Community, Membership

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render



from notifications.models import Notification





def get_selected_community(request):
    """
    Find the user's last selected accessible community.
    Return None if no valid community is selected.
    """
    community_id = request.session.get(
        "last_community_id"
    )

    if not community_id:
        return None

    community = Community.objects.filter(
        Q(created_by=request.user) |
        Q(membership__user=request.user),
        pk=community_id
    ).distinct().first()

    if community is None:
        request.session.pop(
            "last_community_id", None
        )

    return community


def accessible_post(user,pk):
    return get_object_or_404(Post.objects.filter(community__memberships__user=user).distinct(),pk=pk)


@login_required
def feed(request):
    community_id = request.session.get(
        "last_community_id"
    )

    if not community_id:
        return redirect("community_list")

    # Allow only communities the user owns or joined.
    community = Community.objects.filter(
        Q(admin=request.user) |
        Q(memberships__user=request.user),
        pk=community_id
    ).distinct().first()

    if community is None:
        request.session.pop(
            "last_community_id", None
        )
        return redirect("community_list")

    posts = (
        Post.objects
        .filter(community=community)
        .select_related("community", "user")
        .prefetch_related("comments__user")
        .order_by("-created_at")
    )

    selected_type = request.GET.get("type", "")
    search_query = request.GET.get(
        "q", ""
    ).strip()

    if selected_type in ("lost", "found"):
        posts = posts.filter(type=selected_type)
    else:
        selected_type = ""

    if search_query:
        posts = posts.filter(
            Q(caption__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    member_count = Membership.objects.filter(
        community=community
    ).count()

    if not Membership.objects.filter(
        community=community,
        user=community.admin
    ).exists():
        member_count += 1


    return render(request, "newsfeed/feed.html", {
        "posts": posts,
        "selected_community": community,
        "member_count": member_count,
        "is_community_owner": (
            community.admin_id == request.user.id
        ),
        "selected_type": selected_type,
        "search_query": search_query,
    })



@login_required
def create(request):

    # Get the currently entered community
    community_id = request.session.get("last_community_id")

    # Find the community from the user's allowed communities
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        user=request.user
    )

    allowed_communities = form.fields["community"].queryset

    community = allowed_communities.filter(
        pk=community_id
    ).first() if community_id else None

    # User must enter an accessible community first
    if community is None:
        messages.error(
            request,
            "Please enter a community before creating a post."
        )
        return redirect("community_list")

    # Force the selected community on the server
    # This prevents changing it through a modified POST request
    form.fields["community"].queryset = allowed_communities.filter(
        pk=community.pk
    )

    form.fields["community"].initial = community.pk

    form.fields["community"].disabled = True

    max_questions = 5

    if request.method == "POST":

        questions = []

        for i in range(1, max_questions + 1):

            question = request.POST.get(
                f"question_{i}", ""
            ).strip()

            if question:
                questions.append(question)

        if any(len(q) > 300 for q in questions):
            form.add_error(
                None,
                "Each verification question must be "
                "300 characters or fewer."
            )

        if form.is_valid():

            with transaction.atomic():

                post = form.save(commit=False)
                post.user = request.user

                # Always save in the entered community
                post.community = community

                post.save()

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
            "community": community,
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


# ==========================================
# REPORT A POST
# ==========================================


@login_required
def report_post(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(
            "community",
            "community__admin"
        ),
        pk=post_id
    )

    # The post author cannot report their own post.
    if post.user_id == request.user.id:
        messages.error(
            request,
            "You cannot report your own post."
        )
        return redirect("post_detail", pk=post.pk)

    # Prevent the same user from reporting twice.
    if Report.objects.filter(
        user=request.user,
        post=post
    ).exists():
        messages.warning(
            request,
            "You have already reported this post."
        )
        return redirect("post_detail", pk=post.pk)

    if request.method == "POST":
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            report.post = post
            report.user = request.user

            # Save report only if it does not already exist.
            # get_or_create also handles concurrent submissions.
            saved_report, created = Report.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={
                    "reason": report.reason,
                    "description": report.description
                }
            )

            if not created:
                messages.warning(
                    request,
                    "You have already reported this post."
                )
                return redirect("post_detail", pk=post.pk)

            # Notify only the community admin.
            # Use the existing notification service for Socket.IO.
            notify(
                post.community.admin,
                (
                    f"REPORT: {request.user.username} "
                    f"reported the post '{post.caption}'."
                ),
                post=post
            )

            messages.success(
                request,
                "Your report has been submitted."
            )

            return redirect(
                "post_detail",
                pk=post.pk
            )

    else:
        form = ReportForm()

    return render(
        request,
        "newsfeed/report_post.html",
        {
            "post": post,
            "form": form
        }
    )



# ==========================================
# COMMUNITY ADMIN: MANAGE POSTS
# ==========================================

@login_required
def manage_community_posts(request, community_id):

    community = get_object_or_404(
        Community,
        pk=community_id,
        admin=request.user
    )

    posts = (
        Post.objects
        .filter(community=community)
        .select_related("user")
        .order_by("-created_at")
    )

    # Reports belonging to posts in this community
    reports = (
        Report.objects
        .filter(post__community=community)
        .select_related("post")
    )

    # Count reports for each post
    report_counts = {}

    for report in reports:
        report_counts[report.post_id] = (
            report_counts.get(report.post_id, 0) + 1
        )

    for post in posts:
        post.report_count = report_counts.get(
            post.pk,
            0
        )

    return render(
        request,
        "newsfeed/manage_posts.html",
        {
            "community": community,
            "posts": posts
        }
    )


# ==========================================
# COMMUNITY ADMIN: REVIEW A POST
# ==========================================

@login_required
def moderate_post(request, post_id):

    post = get_object_or_404(
        Post.objects.select_related(
            "user",
            "community"
        ),
        pk=post_id,
        community__admin=request.user
    )

    reports = (
        Report.objects
        .filter(post=post)
        .order_by("-pk")
    )

    return render(
        request,
        "newsfeed/moderate_post.html",
        {
            "post": post,
            "reports": reports
        }
    )


# ==========================================
# COMMUNITY ADMIN: REMOVE A POST
# ==========================================

@login_required
@require_POST
def admin_delete_post(request, post_id):

    post = get_object_or_404(
        Post.objects.select_related("community"),
        pk=post_id,
        community__admin=request.user
    )

    community_id = post.community_id

    post.delete()

    messages.success(
        request,
        "The post has been removed."
    )

    return redirect(
        "manage_community_posts",
        community_id=community_id
    )
