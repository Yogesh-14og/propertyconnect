from django.contrib import admin
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import PropertyPost, Favorite, PropertyRating, Contact, PropertyImage, Transaction, Message


@admin.register(PropertyPost)
class PropertyPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'price', 'location', 'status', 'created_at')
    list_filter = ('status', 'property_type')
    search_fields = ('title', 'location')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')


@admin.register(PropertyRating)
class PropertyRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'rating', 'created_at')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'property', 'created_at')
    search_fields = ('name', 'email', 'message')


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'created_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'buyer', 'seller', 'commission', 'is_paid', 'is_approved', 'created_at')
    list_filter = ('is_paid', 'is_approved', 'transaction_type')
    search_fields = ('property__title', 'buyer__username', 'seller__username')
    actions = ['mark_as_paid', 'approve_payment']  
    
    def mark_as_paid(self, request, queryset):
        for transaction in queryset:
            transaction.is_paid = True
            transaction.save()
        self.message_user(request, f'{queryset.count()} transactions marked as paid.')
    mark_as_paid.short_description = 'Mark selected as paid'
    
    def approve_payment(self, request, queryset):
        for transaction in queryset:
            if not transaction.is_paid:
                self.message_user(request, f'Transaction #{transaction.id} is not paid yet. Please mark as paid first.', level='ERROR')
                continue
            
            transaction.is_approved = True
            transaction.approved_by = request.user
            transaction.approved_at = timezone.now()
            transaction.save()
            
            property = transaction.property
            if transaction.transaction_type == 'sale':
                property.status = 'sold'
            else:
                property.status = 'rented'
            property.sold_date = timezone.now()
            property.save()
            
            send_mail(
                subject='Your deal is now complete!',
                message=f"""
Dear {transaction.buyer.username},

Congratulations! Your deal has been approved and completed!

Property: {transaction.property.title}
Type: {transaction.transaction_type}
Price: Rs.{transaction.price}
Commission: Rs.{transaction.commission} (Paid!!)

Thank you for using PropertyConnect!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[transaction.buyer.email],
                fail_silently=False,
            )
            
            send_mail(
                subject='Your property has been sold/rented!',
                message=f"""
Dear {transaction.seller.username},

Your property has been successfully {transaction.transaction_type}ed!

Property: {transaction.property.title}
Buyer: {transaction.buyer.username}
Price: Rs.{transaction.price}
Commission: Rs.{transaction.commission} (Paid!!)

Thank you for using PropertyConnect!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[transaction.seller.email],
                fail_silently=False,
            )
        
        self.message_user(request, f'{queryset.count()} transactions approved successfully.')
    
    approve_payment.short_description = 'Approve selected payments'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'subject', 'message')

