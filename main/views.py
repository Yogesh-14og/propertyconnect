from decimal import Decimal
from datetime import datetime
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg
from .models import PropertyPost, Favorite, PropertyRating, Contact, PropertyImage, Transaction, Message


def home(request):
    featured = PropertyPost.objects.filter(is_featured=True, status='available')[:6]
    latest = PropertyPost.objects.filter(status='available').order_by('-created_at')[:8]
    sell = PropertyPost.objects.filter(property_type='sell', status='available')[:4]
    rent = PropertyPost.objects.filter(property_type='rent', status='available')[:4]
    
    context = {
        'featured': featured,
        'latest': latest,
        'sell': sell,
        'rent': rent,
    }
    return render(request, 'main/home.html', context)


def property_detail(request, pk):
    post = get_object_or_404(PropertyPost, pk=pk)
    post.views += 1
    post.save()
    
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, property=post).exists()
    
    avg_rating = PropertyRating.objects.filter(property=post).aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'post': post,
        'is_favorited': is_favorited,
        'avg_rating': avg_rating,
    }
    return render(request, 'main/detail.html', context)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back {username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('home')


def post_property(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        bedrooms = request.POST.get('bedrooms')
        area = request.POST.get('area')
        
        if bedrooms == '':
            bedrooms = 0
        else:
            bedrooms = int(bedrooms)
        
        if area == '':
            area = 0
        else:
            area = int(area)
        
        post = PropertyPost.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            location=request.POST.get('location'),
            property_type=request.POST.get('property_type'),
            bedrooms=bedrooms,
            area=area,
            phone=request.POST.get('phone'),
            image=request.FILES.get('image'),
        )
        
        images = request.FILES.getlist('images')
        for img in images:
            PropertyImage.objects.create(property=post, image=img)
        
        messages.success(request, 'Property posted successfully!')
        return redirect('home')
    
    return render(request, 'main/post_property.html')


def toggle_favorite(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    post = get_object_or_404(PropertyPost, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, property=post)
    
    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from favorites'})
    return JsonResponse({'status': 'added', 'message': 'Added to favorites'})


def rate_property(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    if request.method == 'POST':
        post = get_object_or_404(PropertyPost, pk=pk)
        rating = int(request.POST.get('rating'))
        
        PropertyRating.objects.update_or_create(
            user=request.user,
            property=post,
            defaults={'rating': rating}
        )
        
        avg_rating = PropertyRating.objects.filter(property=post).aggregate(Avg('rating'))['rating__avg'] or 0
        
        return JsonResponse({
            'status': 'success',
            'avg_rating': round(avg_rating, 1)
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_posts = PropertyPost.objects.filter(user=request.user)
    favorites = Favorite.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)
    
    context = {
        'user_posts': user_posts,
        'favorites': favorites,
        'transactions': transactions,
    }
    return render(request, 'main/dashboard.html', context)


def contact_owner(request, pk):
    property = get_object_or_404(PropertyPost, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        Contact.objects.create(
            property=property,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        messages.success(request, 'Your message sent successfully!')
        return redirect('property_detail', pk=pk)
    
    return render(request, 'main/contact.html', {'property': property})


def search(request):
    query = request.GET.get('q', '')
    
    if query:
        results = PropertyPost.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(location__icontains=query) |
            models.Q(description__icontains=query),
            status='available'
        ).distinct()
    else:
        results = PropertyPost.objects.none()
    
    context = {
        'query': query,
        'results': results,
        'count': results.count(),
    }
    return render(request, 'main/search_results.html', context)


def about(request):
    return render(request, 'main/about.html')


def contact_page(request):
    return render(request, 'main/contact_page.html')


def privacy(request):
    return render(request, 'main/privacy.html')


def send_message(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    property = get_object_or_404(PropertyPost, pk=pk)
    
    if request.user == property.user:
        messages.error(request, 'You cannot send message to yourself!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        Message.objects.create(
            sender=request.user,
            receiver=property.user,
            property=property,
            subject=subject,
            message=message_text
        )
        
        messages.success(request, 'Message sent successfully!')
        return redirect('property_detail', pk=pk)
    
    return render(request, 'main/send_message.html', {'property': property})


def inbox(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    received = Message.objects.filter(receiver=request.user).order_by('-created_at')
    sent = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    unread = received.filter(is_read=False)
    for msg in unread:
        msg.is_read = True
        msg.save()
    
    context = {
        'received': received,
        'sent': sent,
        'unread_count': unread.count(),
    }
    return render(request, 'main/inbox.html', context)


def message_detail(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    message = get_object_or_404(Message, pk=pk)
    
    if request.user != message.sender and request.user != message.receiver:
        messages.error(request, 'You are not authorized.')
        return redirect('inbox')
    
    if not message.is_read and request.user == message.receiver:
        message.is_read = True
        message.save()
    
    context = {
        'message': message,
    }
    return render(request, 'main/message_detail.html', context)


def reply_message(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    original_message = get_object_or_404(Message, pk=pk)
    
    if request.user != original_message.receiver:
        messages.error(request, 'You are not authorized to reply to this message.')
        return redirect('inbox')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        reply = Message.objects.create(
            sender=request.user,
            receiver=original_message.sender,
            property=original_message.property,
            subject=f"Re: {subject}",
            message=message_text
        )
        
        messages.success(request, 'Reply sent successfully!')
        return redirect('message_detail', pk=reply.id)
    
    context = {
        'original_message': original_message,
        'receiver': original_message.sender,
    }
    return render(request, 'main/reply_message.html', context)


def complete_deal(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    property = get_object_or_404(PropertyPost, pk=pk)
    
    if property.user == request.user:
        messages.error(request, 'You cannot buy your own property!')
        return redirect('property_detail', pk=pk)
    
    if property.status != 'available':
        messages.error(request, 'This property is no longer available.')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        price = request.POST.get('price')
        transaction_type = request.POST.get('transaction_type')
        
        if not price or float(price) <= 0:
            messages.error(request, 'Please enter a valid price.')
            return redirect('complete_deal', pk=pk)
        
        payment_confirmed = request.POST.get('paymentConfirm')
        
        if not payment_confirmed:
            messages.error(request, 'Please confirm that you have paid the commission.')
            return redirect('complete_deal', pk=pk)
        
        commission = float(price) * 0.01
        
        transaction = Transaction.objects.create(
            property=property,
            buyer=request.user,
            seller=property.user,
            transaction_type=transaction_type,
            price=price,
            commission=commission,
            is_paid=True,
            is_approved=False
        )
        
        if transaction_type == 'sale':
            property.status = 'sold'
        else:
            property.status = 'rented'
        property.sold_date = datetime.now()
        property.save()
        
        # Email to buyer
        try:
            send_mail(
                subject='Deal Confirmed - PropertyConnect',
                message=f"""
Dear {request.user.username},

Congratulations! Your deal has been confirmed.

Property: {property.title}
Price: Rs.{price}
Commission: Rs.{commission} (1%)

Thank you for using PropertyConnect!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        # Email to seller
        try:
            send_mail(
                subject='Your property has been {transaction_type}ed!',
                message=f"""
Dear {property.user.username},

Your property "{property.title}" has been {transaction_type}ed!

Buyer: {request.user.username}
Price: Rs.{price}
Commission: Rs.{commission}

Thank you for using PropertyConnect!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[property.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        # Email to admin
        try:
            send_mail(
                subject='New Transaction Pending Approval',
                message=f"""
Transaction ID: #{transaction.id}
Property: {property.title}
Buyer: {request.user.username}
Seller: {property.user.username}
Price: Rs.{price}
Commission: Rs.{commission}

Please login to admin panel to approve.
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        messages.success(request, f'Deal completed! Commission: Rs.{commission:.2f}. Waiting for admin approval.')
        return redirect('dashboard')
    
    return render(request, 'main/complete_deal.html', {'property': property})


def transaction_detail(request, transaction_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.user != transaction.buyer and request.user != transaction.seller:
        messages.error(request, 'You are not authorized.')
        return redirect('dashboard')
    
    context = {
        'transaction': transaction,
    }
    return render(request, 'main/transaction_detail.html', context)
