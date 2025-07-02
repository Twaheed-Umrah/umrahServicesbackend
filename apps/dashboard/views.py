from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from calendar import month_name
import calendar

from apps.bookings.models import Booking, QuickBooking
from apps.enquiries.models import ContactUs
from apps.enquiries.models import APIKey
from django.db.models.functions import Extract, TruncMonth, TruncYear, TruncDate


def get_user_specific_queryset(user, model_class):
    """
    Get queryset filtered by user role and permissions
    """
    if user.role == 'superadmin':
        # SuperAdmin can see all data
        return model_class.objects.all()
    else:
        # Other users can only see their own data
        return model_class.objects.filter(created_by=user)


def get_enquiry_queryset(user):
    """
    Get enquiry queryset based on user's API keys
    Only superadmin gets all enquiries, others get enquiries from their API keys
    """
    if user.role == 'superadmin':
        # SuperAdmin gets all enquiries
        return ContactUs.objects.all()
    else:
        # Other users get enquiries only from their API keys
        user_api_keys = APIKey.objects.filter(user=user, is_active=True)
        if user_api_keys.exists():
            # Get enquiries that came through this user's API keys
            # Assuming ContactUs has an api_key field or similar tracking
            return ContactUs.objects.filter(api_key__in=user_api_keys)
        else:
            # If user has no API keys, return empty queryset
            return ContactUs.objects.none()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for bookings, amounts, and enquiries
    Data filtered by user role and permissions
    """
    user = request.user
    now = timezone.now()
    today = now.date()
    current_month = now.month
    current_year = now.year
    
    # Get user-specific querysets
    booking_qs = get_user_specific_queryset(user, Booking)
    quick_booking_qs = get_user_specific_queryset(user, QuickBooking)
    enquiry_qs = get_enquiry_queryset(user)
    
    # Get total bookings (both regular and quick bookings)
    total_bookings = booking_qs.count()
    total_quick_bookings = quick_booking_qs.count()
    total_all_bookings = total_bookings + total_quick_bookings
    
    # Monthly bookings
    monthly_bookings = booking_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    monthly_quick_bookings = quick_booking_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    total_monthly_bookings = monthly_bookings + monthly_quick_bookings
    
    # Today's bookings
    today_bookings = booking_qs.filter(created_at__date=today).count()
    today_quick_bookings = quick_booking_qs.filter(created_at__date=today).count()
    total_today_bookings = today_bookings + today_quick_bookings
    
    # Amount calculations
    total_amount = booking_qs.aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    monthly_amount = booking_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    today_amount = booking_qs.filter(
        created_at__date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Add QuickBooking amounts
    total_quick_amount = quick_booking_qs.aggregate(
        total=Sum('budget')
    )['total'] or 0
    
    monthly_quick_amount = quick_booking_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(total=Sum('budget'))['total'] or 0
    
    today_quick_amount = quick_booking_qs.filter(
        created_at__date=today
    ).aggregate(total=Sum('budget'))['total'] or 0
    
    # Total amounts including quick bookings
    total_all_amount = total_amount + total_quick_amount
    total_monthly_amount = monthly_amount + monthly_quick_amount
    total_today_amount = today_amount + today_quick_amount
    
    # Enquiries (ContactUs) - based on user's API keys
    total_enquiries = enquiry_qs.count()
    monthly_enquiries = enquiry_qs.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    today_enquiries = enquiry_qs.filter(created_at__date=today).count()
    
    # Format amounts for display
    def format_amount(amount):
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.1f}Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.1f}L"
        elif amount >= 1000:  # 1 thousand
            return f"₹{amount/1000:.1f}K"
        else:
            return f"₹{amount}"
    
    return Response({
        'bookings': {
            'total': total_all_bookings,
            'monthly': total_monthly_bookings,
            'today': total_today_bookings
        },
        'amounts': {
            'total': format_amount(total_all_amount),
            'total_raw': total_all_amount,
            'monthly': format_amount(total_monthly_amount),
            'monthly_raw': total_monthly_amount,
            'today': format_amount(total_today_amount),
            'today_raw': total_today_amount
        },
        'enquiries': {
            'total': total_enquiries,
            'monthly': monthly_enquiries,
            'today': today_enquiries
        },
        'user_role': user.role  # Include user role for frontend logic
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_data(request):
    """
    Get chart data for different time periods and types
    Data filtered by user role and permissions
    """
    user = request.user
    period = request.GET.get('period', 'monthly')  # daily, monthly, yearly
    chart_type = request.GET.get('type', 'income')  # income, booking, enquiry
    
    now = timezone.now()
    current_year = now.year
    
    # Get user-specific querysets
    booking_qs = get_user_specific_queryset(user, Booking)
    quick_booking_qs = get_user_specific_queryset(user, QuickBooking)
    enquiry_qs = get_enquiry_queryset(user)
    
    if period == 'yearly':
        # Get data for last 5 years
        years = range(current_year - 4, current_year + 1)
        data = []
        
        for year in years:
            if chart_type == 'income':
                # Combine regular and quick booking amounts
                regular_amount = booking_qs.filter(
                    created_at__year=year
                ).aggregate(total=Sum('total_price'))['total'] or 0
                
                quick_amount = quick_booking_qs.filter(
                    created_at__year=year
                ).aggregate(total=Sum('budget'))['total'] or 0
                
                value = regular_amount + quick_amount
                
            elif chart_type == 'booking':
                regular_count = booking_qs.filter(created_at__year=year).count()
                quick_count = quick_booking_qs.filter(created_at__year=year).count()
                value = regular_count + quick_count
                
            else:  # enquiry
                value = enquiry_qs.filter(created_at__year=year).count()
            
            data.append({
                'name': str(year),
                'value': value
            })
    
    elif period == 'monthly':
        # Get data for current year, all 12 months
        data = []
        
        for month_num in range(1, 13):
            month_short = calendar.month_abbr[month_num]
            
            if chart_type == 'income':
                regular_amount = booking_qs.filter(
                    created_at__year=current_year,
                    created_at__month=month_num
                ).aggregate(total=Sum('total_price'))['total'] or 0
                
                quick_amount = quick_booking_qs.filter(
                    created_at__year=current_year,
                    created_at__month=month_num
                ).aggregate(total=Sum('budget'))['total'] or 0
                
                value = regular_amount + quick_amount
                
            elif chart_type == 'booking':
                regular_count = booking_qs.filter(
                    created_at__year=current_year,
                    created_at__month=month_num
                ).count()
                quick_count = quick_booking_qs.filter(
                    created_at__year=current_year,
                    created_at__month=month_num
                ).count()
                value = regular_count + quick_count
                
            else:  # enquiry
                value = enquiry_qs.filter(
                    created_at__year=current_year,
                    created_at__month=month_num
                ).count()
            
            data.append({
                'name': month_short,
                'value': value
            })
    
    else:  # daily - last 7 days
        data = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i in range(7):
            target_date = now.date() - timedelta(days=6-i)
            day_name = days[target_date.weekday()]
            
            if chart_type == 'income':
                regular_amount = booking_qs.filter(
                    created_at__date=target_date
                ).aggregate(total=Sum('total_price'))['total'] or 0
                
                quick_amount = quick_booking_qs.filter(
                    created_at__date=target_date
                ).aggregate(total=Sum('budget'))['total'] or 0
                
                value = regular_amount + quick_amount
                
            elif chart_type == 'booking':
                regular_count = booking_qs.filter(created_at__date=target_date).count()
                quick_count = quick_booking_qs.filter(created_at__date=target_date).count()
                value = regular_count + quick_count
                
            else:  # enquiry
                value = enquiry_qs.filter(created_at__date=target_date).count()
            
            data.append({
                'name': day_name,
                'value': value
            })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_revenue_chart(request):
    """
    Get monthly booking and revenue data for the current year
    Data filtered by user role and permissions
    """
    user = request.user
    current_year = timezone.now().year
    data = []
    
    # Get user-specific querysets
    booking_qs = get_user_specific_queryset(user, Booking)
    quick_booking_qs = get_user_specific_queryset(user, QuickBooking)
    
    for month_num in range(1, 13):
        month_short = calendar.month_abbr[month_num]
        
        # Count bookings
        regular_bookings = booking_qs.filter(
            created_at__year=current_year,
            created_at__month=month_num
        ).count()
        
        quick_bookings = quick_booking_qs.filter(
            created_at__year=current_year,
            created_at__month=month_num
        ).count()
        
        total_bookings = regular_bookings + quick_bookings
        
        # Calculate revenue
        regular_revenue = booking_qs.filter(
            created_at__year=current_year,
            created_at__month=month_num
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        quick_revenue = quick_booking_qs.filter(
            created_at__year=current_year,
            created_at__month=month_num
        ).aggregate(total=Sum('budget'))['total'] or 0
        
        total_revenue = regular_revenue + quick_revenue
        
        data.append({
            'name': month_short,
            'bookings': total_bookings,
            'revenue': int(total_revenue)
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def enquiry_distribution(request):
    """
    Get enquiry distribution by package type
    Data filtered by user's API keys (superadmin gets all)
    """
    user = request.user
    enquiry_qs = get_enquiry_queryset(user)
    
    # Get enquiry counts by package_type
    enquiry_data = enquiry_qs.exclude(
        package_type__isnull=True
    ).exclude(
        package_type__exact=''
    ).values('package_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Define colors for different package types
    colors = ['#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    
    data = []
    for i, item in enumerate(enquiry_data[:6]):  # Limit to top 6
        data.append({
            'name': item['package_type'].title() if item['package_type'] else 'Other',
            'value': item['count'],
            'color': colors[i % len(colors)]
        })
    
    # If no package_type data, return empty list
    if not data:
        data = []
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activities(request):
    """
    Get recent activities - latest bookings and enquiries
    Data filtered by user role and permissions
    """
    user = request.user
    
    # Get user-specific querysets
    booking_qs = get_user_specific_queryset(user, Booking)
    quick_booking_qs = get_user_specific_queryset(user, QuickBooking)
    enquiry_qs = get_enquiry_queryset(user)
    
    # Recent bookings
    recent_bookings = booking_qs.select_related('created_by').order_by('-created_at')[:5]
    recent_quick_bookings = quick_booking_qs.select_related('created_by').order_by('-created_at')[:5]
    recent_enquiries = enquiry_qs.order_by('-created_at')[:5]
    
    activities = []
    
    # Add recent bookings
    for booking in recent_bookings:
        activities.append({
            'type': 'booking',
            'title': f'New Booking: {booking.customer_name}',
            'description': f'Package: {booking.package_name}',
            'amount': f'₹{booking.total_price:,.0f}',
            'time': booking.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': booking.created_by.get_full_name() if booking.created_by else 'System'
        })
    
    # Add recent quick bookings
    for booking in recent_quick_bookings:
        activities.append({
            'type': 'quick_booking',
            'title': f'Quick Booking: {booking.customer_name}',
            'description': f'Destination: {booking.destination}',
            'amount': f'₹{booking.budget:,.0f}',
            'time': booking.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': booking.created_by.get_full_name() if booking.created_by else 'System'
        })
    
    # Add recent enquiries
    for enquiry in recent_enquiries:
        activities.append({
            'type': 'enquiry',
            'title': f'New Enquiry: {enquiry.name}',
            'description': f'Package: {enquiry.package_type or "General"}',
            'amount': None,
            'time': enquiry.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': 'Website'
        })
    
    # Sort by time and limit to 10
    activities.sort(key=lambda x: x['time'], reverse=True)
    
    return Response(activities[:10])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    Get comprehensive dashboard summary
    Data filtered by user role and permissions
    """
    try:
        # Get all data in one response
        stats_response = dashboard_stats(request)
        booking_revenue_response = booking_revenue_chart(request)
        enquiry_dist_response = enquiry_distribution(request)
        recent_activities_response = recent_activities(request)
        
        return Response({
            'stats': stats_response.data,
            'booking_revenue_chart': booking_revenue_response.data,
            'enquiry_distribution': enquiry_dist_response.data,
            'recent_activities': recent_activities_response.data,
            'last_updated': timezone.now().isoformat(),
            'user_role': request.user.role
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch dashboard data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )