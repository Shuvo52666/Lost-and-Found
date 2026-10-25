
from io import BytesIO
import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommunityForm, JoinForm
from .models import Community, Membership


def accessible_communities(user):
    return Community.objects.filter(
        Q(admin=user) |
        Q(memberships__user=user)
    ).distinct()



@login_required
def community_list(request):
    # Communities where the current user is an admin
    owned = Community.objects.filter(
        admin=request.user
    ).order_by("name")

    # Communities where the user is a member,
    # excluding communities they manage
    joined = accessible_communities(
        request.user
    ).exclude(
        admin=request.user
    ).order_by("name")

    # One combined list:
    # Admin communities FIRST, joined communities SECOND
    from django.db.models import Case, When, Value, IntegerField

    communities = (
        accessible_communities(request.user)
        .annotate(
            priority=Case(
                When(
                    admin=request.user,
                    then=Value(0)
                ),
                default=Value(1),
                output_field=IntegerField()
            )
        )
        .order_by("priority", "name")
    )

    return render(
        request,
        "communities/list.html",
        {
            "communities": communities,
            "owned_communities": owned,
            "joined_communities": joined,
            "join_form": JoinForm(),
        }
    )

@login_required
def enter_community(request, pk):
    community = get_object_or_404(
        accessible_communities(request.user),
        pk=pk
    )

    request.session["last_community_id"] = community.pk

    return redirect("feed")


@login_required
def create(request):
    form = CommunityForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.admin = request.user
        obj.save()

        Membership.objects.get_or_create(
            user=request.user,
            community=obj,
            defaults={"role": "admin"}
        )

        request.session["last_community_id"] = obj.pk

        messages.success(
            request,
            "Community created successfully."
        )

        return redirect("feed")

    return render(request, "generic_form.html", {
        "form": form,
        "heading": "Create community",
        "submit_label": "Create",
    })


@login_required
def join(request):
    if request.method != "POST":
        return redirect("community_list")

    form = JoinForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data["code"].strip().upper()

        community = Community.objects.filter(
            join_code__iexact=code
        ).first()

        if community:
            _, created = Membership.objects.get_or_create(
                user=request.user,
                community=community
            )

            request.session[
                "last_community_id"
            ] = community.pk

            messages.success(
                request,
                "Joined community." if created
                else "You are already a member."
            )

            return redirect("feed")

    messages.error(request, "Invalid community ID.")
    return redirect("community_list")


@login_required
def detail(request, pk):
    community = get_object_or_404(
        accessible_communities(request.user),
        pk=pk
    )

    # Opening a community opens its individual feed.
    request.session[
        "last_community_id"
    ] = community.pk

    return redirect("feed")


@login_required
def qr(request, pk):
    community = get_object_or_404(
        accessible_communities(request.user),
        pk=pk
    )

    target = request.build_absolute_uri(
        reverse(
            "community_join_code",
            args=[community.join_code]
        )
    )

    image = qrcode.make(target)

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png"
    )


@login_required
def join_code(request, code):
    community = get_object_or_404(
        Community,
        join_code__iexact=code
    )

    if request.method == "POST":
        Membership.objects.get_or_create(
            user=request.user,
            community=community
        )

        request.session[
            "last_community_id"
        ] = community.pk

        messages.success(
            request,
            "Joined community."
        )

        return redirect("feed")

    return render(
        request,
        "communities/confirm_join.html",
        {"community": community}
    )
