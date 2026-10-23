from io import BytesIO
import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import CommunityForm, JoinForm
from .models import Community, Membership

@login_required
def community_list(request):
    communities = Community.objects.filter(memberships__user=request.user).distinct()
    return render(request,'communities/list.html',{'communities':communities,'join_form':JoinForm()})

@login_required
def create(request):
    form = CommunityForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False)
        obj.admin=request.user
        obj.save()
        Membership.objects.create(user=request.user,community=obj,role='admin')
        messages.success(request,'Community created. Share its ID only with intended members.')
        return redirect('community_detail',pk=obj.pk)
    return render(request,'generic_form.html',{'form':form,'heading':'Create community','submit_label':'Create'})

@login_required
def join(request):
    if request.method!='POST': return redirect('community_list')
    form=JoinForm(request.POST)
    if form.is_valid():
        obj=Community.objects.filter(join_code=form.cleaned_data['code'].strip().upper()).first()
        if obj:
            _,created=Membership.objects.get_or_create(user=request.user,community=obj)
            messages.success(request,'Joined community.' if created else 'You are already a member.')
            return redirect('community_detail',pk=obj.pk)
    messages.error(request,'Invalid community ID.')
    return redirect('community_list')

@login_required
def detail(request,pk):
    obj=get_object_or_404(Community,pk=pk)
    if not Membership.objects.filter(user=request.user,community=obj).exists(): raise Http404()
    return render(request,'communities/detail.html',{'community':obj})

@login_required
def qr(request,pk):
    obj=get_object_or_404(Community,pk=pk)
    if not Membership.objects.filter(user=request.user,community=obj).exists(): raise Http404()
    target=request.build_absolute_uri(reverse('community_join_code',args=[obj.join_code]))
    im=qrcode.make(target)
    buf=BytesIO(); im.save(buf,format='PNG')
    return HttpResponse(buf.getvalue(),content_type='image/png')

@login_required
def join_code(request,code):
    obj=get_object_or_404(Community,join_code=code.upper())
    if request.method=='POST':
        Membership.objects.get_or_create(user=request.user,community=obj)
        messages.success(request,'Joined community.')
        return redirect('community_detail',pk=obj.pk)
    return render(request,'communities/confirm_join.html',{'community':obj})
