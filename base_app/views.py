from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from club.models import Committee, Club
from accounts.models import User, FeeStructure, FeeName
from payment.models import CommitteeDonation, MembershipPayment
from django.db.models import Sum

def home(request):
    fee_totals = FeeStructure.objects.filter(is_active=True) \
        .values('fee_name__name') \
        .annotate(total_amount=Sum('amount')) \
        .order_by('fee_name__name')
    
    # Calculate grand total
    total_fees_collected = sum(item['total_amount'] for item in fee_totals)
    context = {
        'committee_count': Committee.objects.count(),  # Count of Committee objects
        'member_count': User.objects.filter(role=User.MEMBER).count(),  # Count of members
        'total_fees_collected': MembershipPayment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,  # Total amount from MembershipPayment
        'total_fees_collected': total_fees_collected,
        'fee_totals': fee_totals,

    }
    return render(request, 'base_app/home.html', context)

def post(request):
    posts = Post.objects.all()

    if request.method == "POST":
        post_id = request.POST.get('post_id')
        message = request.POST.get('message')
        comment_id = request.POST.get('comment_id')  # Check if editing a comment

        if post_id and message:
            post = get_object_or_404(Post, id=post_id)
            if request.user.is_authenticated:
                if comment_id:  # If editing an existing comment
                    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
                    comment.message = message
                    comment.save()
                else:  # New comment
                    Comment.objects.create(user=request.user, post=post, message=message)
                return redirect('home')

    context = {'posts': posts}
    return render(request, 'base_app/post.html', context)

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.title = request.POST['title']
        post.body = request.POST['body']
        post.save()
        return redirect('home')
    return render(request, 'base_app/edit_post.html', {'post': post})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    return redirect('home')

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    if request.method == 'POST':
        comment.message = request.POST['message']
        comment.save()
        return redirect('home')
    return render(request, 'base_app/edit_comment.html', {'comment': comment})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return redirect('home')

@login_required
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')

        # Create and save the new post
        post = Post.objects.create(user=request.user, title=title, body=body)
        return redirect('home')  # Redirect back to the home page

    return render(request, 'base_app/create_post.html')
