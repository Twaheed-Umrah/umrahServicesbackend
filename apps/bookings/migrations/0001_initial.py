# Generated by Django 5.2.3 on 2025-06-22 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking_number', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('mobile_no', models.CharField(max_length=15)),
                ('passport_no', models.CharField(blank=True, max_length=20, null=True)),
                ('place_of_issue', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.TextField()),
                ('travel_date', models.DateField()),
                ('departure_city', models.CharField(max_length=100)),
                ('package_name', models.CharField(max_length=255)),
                ('package_days', models.PositiveIntegerField()),
                ('sharing', models.CharField(choices=[('single', 'Single'), ('double', 'Double'), ('triple', 'Triple'), ('quad', 'Quad')], max_length=20)),
                ('room_sharing', models.CharField(choices=[('single', 'Single'), ('double', 'Double'), ('triple', 'Triple'), ('quad', 'Quad')], max_length=20)),
                ('flight', models.BooleanField(default=False)),
                ('special_request', models.TextField(blank=True, null=True)),
                ('adult_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_adults', models.PositiveIntegerField()),
                ('total_adult_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('child_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_children', models.PositiveIntegerField(default=0)),
                ('total_child_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('infant_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_infants', models.PositiveIntegerField(default=0)),
                ('total_infant_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('advance_payment', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payable_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_type', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'), ('net_banking', 'Net Banking'), ('cheque', 'Cheque')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('remarks', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BookingTraveler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('age', models.PositiveIntegerField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=10)),
                ('traveler_type', models.CharField(choices=[('adult', 'Adult'), ('child', 'Child'), ('infant', 'Infant')], max_length=10)),
                ('passport_number', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuickBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking_number', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('mobile', models.CharField(max_length=15)),
                ('travel_date', models.DateField()),
                ('destination', models.CharField(max_length=255)),
                ('number_of_travelers', models.PositiveIntegerField()),
                ('budget', models.DecimalField(decimal_places=2, max_digits=10)),
                ('preferred_payment', models.CharField(choices=[('full_advance', 'Full Payment in Advance'), ('partial_advance', 'Partial Payment in Advance'), ('pay_later', 'Pay Later')], max_length=20)),
                ('is_converted_to_full_booking', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
