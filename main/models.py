from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class PropertyPost(models.Model):
    PROPERTY_TYPES = [
        ('sell', 'For Sale'),
        ('rent', 'For Rent'),
        ('buy', 'Looking to Buy'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=200)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='sell')
    bedrooms = models.IntegerField(default=0)
    area = models.IntegerField(default=0, help_text="Area in sq. ft.")
    image = models.ImageField(upload_to='properties/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    sold_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.location}"


class PropertyImage(models.Model):
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.property.title}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'property']


class PropertyRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'property']


class Contact(models.Model):
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.property.title}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.subject[:30]}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]
    
    property = models.ForeignKey(PropertyPost, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_transactions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.commission = Decimal(str(self.price)) * Decimal('0.01')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.property.title} - Rs.{self.commission}"