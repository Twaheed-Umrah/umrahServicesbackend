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
from apps.crm.models import Lead
from apps.enquiries.models import ContactUs
from apps.enquiries.models import APIKey
from django.db.models.functions import Extract, TruncMonth, TruncYear, TruncDate


def get_user_specific_queryset(user, model_class, request=None):
    """
    Get queryset filtered by user role, tenant selection, and date filters
    """
    if user.role == 'superadmin':
        qs = model_class.objects.all()
        if request:
            tenant_id = request.GET.get('tenant_id') or getattr(request, 'query_params', {}).get('tenant_id')
            if tenant_id and str(tenant_id).lower() != 'all':
                qs = qs.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id))
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs
    elif user.role in ['accountant', 'operations', 'sells_caller']:
        if user.created_by:
            qs = model_class.objects.filter(Q(created_by=user.created_by) | Q(created_by=user))
        else:
            qs = model_class.objects.filter(created_by=user)
        if request:
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs
    else:
        # Franchise Admin (Tenant)
        qs = model_class.objects.filter(Q(created_by=user) | Q(created_by__created_by=user))
        if request:
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs


def get_enquiry_queryset(user, request=None):
    """
    Get enquiry queryset based on user's API keys and tenancy
    """
    if user.role == 'superadmin':
        qs = ContactUs.objects.all()
        if request:
            tenant_id = request.GET.get('tenant_id') or getattr(request, 'query_params', {}).get('tenant_id')
            if tenant_id and str(tenant_id).lower() != 'all':
                qs = qs.filter(Q(submitted_by_user_id=tenant_id) | Q(api_key__user_id=tenant_id))
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs
    elif user.role in ['accountant', 'operations', 'sells_caller']:
        if user.created_by:
            user_api_keys = APIKey.objects.filter(user=user.created_by, is_active=True)
            qs = ContactUs.objects.filter(Q(api_key__in=user_api_keys) | Q(submitted_by_user=user.created_by))
        else:
            qs = ContactUs.objects.filter(submitted_by_user=user)
        if request:
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs
    else:
        user_api_keys = APIKey.objects.filter(user=user, is_active=True)
        qs = ContactUs.objects.filter(Q(api_key__in=user_api_keys) | Q(submitted_by_user=user))
        if request:
            from apps.common.tenancy import apply_date_filters
            qs = apply_date_filters(qs, request, date_field='created_at')
        return qs


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
    Data filtered by user's API keys (superadmin gets all, accountant gets parent's)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def executive_dashboard_overview(request):
    """
    Unified endpoint for Executive Dashboard matching the reference UI:
    - User Profile & Greeting
    - 4 Top KPI Pods (Bookings, Accounts, Lead CRM, Staff Pipeline)
    - Monthly Booking Overview (Bookings + Passengers per month for requested year)
    - Lead Source Analysis (Percentages and counts for donut chart)
    - Recent Bookings (Top 5)
    - Recent Payments (Top 5)
    - Lead Status Distribution (Bar chart)
    """
    user = request.user
    now = timezone.now()
    today = now.date()

    # Determine requested year
    try:
        selected_year = int(request.GET.get('year', now.year))
    except (ValueError, TypeError):
        selected_year = now.year

    current_month = now.month
    prev_month = 12 if current_month == 1 else current_month - 1
    prev_month_year = now.year - 1 if current_month == 1 else now.year

    # Querysets filtered by role / tenant
    booking_qs = Booking.objects.all()
    quick_booking_qs = QuickBooking.objects.all()
    lead_qs = Lead.objects.all()
    contact_qs = ContactUs.objects.all()

    if user.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id', None)
        if tenant_id and tenant_id != 'all':
            booking_qs = booking_qs.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id))
            quick_booking_qs = quick_booking_qs.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id))
            lead_qs = lead_qs.filter(Q(user_id=tenant_id) | Q(assigned_caller__created_by_id=tenant_id))
            contact_qs = contact_qs.filter(Q(submitted_by_user_id=tenant_id) | Q(api_key__user_id=tenant_id))
    elif user.role in ['accountant', 'operations', 'sells_caller']:
        if user.created_by:
            booking_qs = booking_qs.filter(Q(created_by=user.created_by) | Q(created_by=user) | Q(created_by__created_by=user.created_by))
            quick_booking_qs = quick_booking_qs.filter(Q(created_by=user.created_by) | Q(created_by=user))
            lead_qs = lead_qs.filter(Q(user=user.created_by) | Q(assigned_caller=user) | Q(assigned_caller__created_by=user.created_by))
            contact_qs = contact_qs.filter(Q(submitted_by_user=user.created_by) | Q(api_key__user=user.created_by))
        else:
            booking_qs = booking_qs.filter(created_by=user)
            quick_booking_qs = quick_booking_qs.filter(created_by=user)
            lead_qs = lead_qs.filter(Q(user=user) | Q(assigned_caller=user))
            contact_qs = contact_qs.filter(submitted_by_user=user)
    else:
        # Franchise Admin / Tenant
        booking_qs = booking_qs.filter(Q(created_by=user) | Q(created_by__created_by=user))
        quick_booking_qs = quick_booking_qs.filter(Q(created_by=user) | Q(created_by__created_by=user))
        lead_qs = lead_qs.filter(Q(user=user) | Q(assigned_caller__created_by=user))
        contact_qs = contact_qs.filter(Q(submitted_by_user=user) | Q(api_key__user=user))

    from apps.common.tenancy import apply_date_filters
    booking_qs = apply_date_filters(booking_qs, request, date_field='created_at')
    quick_booking_qs = apply_date_filters(quick_booking_qs, request, date_field='created_at')
    lead_qs = apply_date_filters(lead_qs, request, date_field='created_at')
    contact_qs = apply_date_filters(contact_qs, request, date_field='created_at')

    # 1. User Info & Greeting
    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0] if user.email else user.username
    greeting_name = full_name.title()

    role_map = {
        'superadmin': 'Super Admin',
        'franchisesadmin': 'Tenant Admin',
        'sells_caller': 'Sales & Telecaller',
        'operations': 'Operations Coordinator',
        'accountant': 'Accountant'
    }
    role_display = role_map.get(user.role, 'Travel Agent')

    # 2. Top Pod 1: Booking Dashboard
    total_bookings = booking_qs.count() + quick_booking_qs.count()
    this_month_reg = booking_qs.filter(created_at__year=now.year, created_at__month=current_month).count()
    this_month_quick = quick_booking_qs.filter(created_at__year=now.year, created_at__month=current_month).count()
    this_month_bookings = this_month_reg + this_month_quick

    last_month_reg = booking_qs.filter(created_at__year=prev_month_year, created_at__month=prev_month).count()
    last_month_quick = quick_booking_qs.filter(created_at__year=prev_month_year, created_at__month=prev_month).count()
    last_month_bookings = last_month_reg + last_month_quick

    if last_month_bookings > 0:
        booking_growth_pct = round(((this_month_bookings - last_month_bookings) / last_month_bookings) * 100)
    elif this_month_bookings > 0:
        booking_growth_pct = 100
    else:
        booking_growth_pct = 0

    # 3. Top Pod 2: Account Dashboard
    amounts = booking_qs.aggregate(
        total=Sum('total_price'),
        advance=Sum('advance_payment'),
        balance=Sum('balance')
    )
    quick_budget = quick_booking_qs.aggregate(total=Sum('budget'))['total'] or 0

    total_amount = float((amounts['total'] or 0) + quick_budget)
    advance_payment = float(amounts['advance'] or 0)
    remaining_amount = float(amounts['balance'] or 0)

    # 4. Top Pod 3: Lead CRM Dashboard
    total_crm_leads = lead_qs.count()
    total_enquiries = contact_qs.count()
    total_leads = total_crm_leads + total_enquiries

    today_leads = lead_qs.filter(created_at__date=today).count() + contact_qs.filter(created_at__date=today).count()
    this_month_leads = lead_qs.filter(created_at__year=now.year, created_at__month=current_month).count() + contact_qs.filter(created_at__year=now.year, created_at__month=current_month).count()
    last_month_leads = lead_qs.filter(created_at__year=prev_month_year, created_at__month=prev_month).count() + contact_qs.filter(created_at__year=prev_month_year, created_at__month=prev_month).count()

    if last_month_leads > 0:
        lead_growth_pct = round(((this_month_leads - last_month_leads) / last_month_leads) * 100)
    elif this_month_leads > 0:
        lead_growth_pct = 100
    else:
        lead_growth_pct = 0

    # 5. Top Pod 4: Staff / Pipeline Dashboard
    hot_leads = lead_qs.filter(status__in=['NEW', 'INTERESTED']).count() + contact_qs.filter(is_processed=False).count()
    warm_leads = lead_qs.filter(status__in=['CONTACTED', 'FOLLOW_UP', 'CALLBACK']).count()
    cold_leads = lead_qs.filter(status__in=['BUSY', 'RNR', 'SWITCH_OFF', 'NOT_INTERESTED']).count()
    closed_leads = lead_qs.filter(status__in=['CLOSED', 'CONVERTED']).count()

    # 6. Monthly Booking Overview (Bookings + Passengers per month for requested year)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_booking_overview = []
    for m in range(1, 13):
        m_reg_qs = booking_qs.filter(created_at__year=selected_year, created_at__month=m)
        m_quick_qs = quick_booking_qs.filter(created_at__year=selected_year, created_at__month=m)
        b_count = m_reg_qs.count() + m_quick_qs.count()
        
        pax_agg = m_reg_qs.aggregate(
            adults=Sum('total_adults'),
            children=Sum('total_children'),
            infants=Sum('total_infants')
        )
        passengers = (pax_agg['adults'] or 0) + (pax_agg['children'] or 0) + (pax_agg['infants'] or 0)
        passengers += m_quick_qs.count()

        monthly_booking_overview.append({
            'month': month_names[m - 1],
            'month_num': m,
            'bookings': b_count,
            'passengers': passengers
        })

    # 7. Lead Source Analysis (Donut Chart & List)
    source_counts = {
        'Website Search': contact_qs.count() + lead_qs.filter(source__iexact='Website').count(),
        'Meta Ads': lead_qs.filter(source__iexact='Meta Ads').count(),
        'Google Ads': lead_qs.filter(source__iexact='Google Ads').count(),
        'Walk-in / Referral': lead_qs.filter(source__in=['Walk-in', 'Referral']).count(),
        'Other': lead_qs.filter(source__in=['Other', 'Excel Upload']).count(),
    }
    source_total = sum(source_counts.values())
    lead_source_analysis = []
    source_palette = {
        'Website Search': '#0f172a',
        'Meta Ads': '#059669',
        'Google Ads': '#334155',
        'Walk-in / Referral': '#0d9488',
        'Other': '#94a3b8'
    }
    for s_name, s_cnt in source_counts.items():
        pct = round((s_cnt / source_total) * 100) if source_total > 0 else 0
        lead_source_analysis.append({
            'source': s_name,
            'count': s_cnt,
            'percentage': pct,
            'color': source_palette.get(s_name, '#64748b')
        })

    # 8. Recent Bookings (Top 5)
    recent_bookings = []
    for b in booking_qs.order_by('-created_at')[:5]:
        pax = (b.total_adults or 0) + (b.total_children or 0) + (b.total_infants or 0) or 1
        name = f"{b.first_name} {b.last_name}".strip() or b.booking_number
        recent_bookings.append({
            'id': b.id,
            'booking_number': b.booking_number,
            'date': b.created_at.strftime('%d %b'),
            'client_name': name,
            'package': b.package_name or "-",
            'pax': pax,
            'amount': float(b.total_price or 0),
            'status': (b.status or 'confirmed').capitalize()
        })

    # 9. Recent Payments (Top 5)
    recent_payments = []
    for b in booking_qs.order_by('-updated_at')[:5]:
        tot = float(b.total_price or 0)
        adv = float(b.advance_payment or 0)
        bal = float(b.balance or 0)
        
        if bal == 0 and tot > 0:
            p_type = 'Full Payment'
            p_status = 'Received'
            amt = tot
        elif adv > 0:
            p_type = 'Advance'
            p_status = 'Received'
            amt = adv
        else:
            p_type = 'Part Payment'
            p_status = 'Pending'
            amt = tot

        name = f"{b.first_name} {b.last_name}".strip() or b.booking_number
        recent_payments.append({
            'id': b.id,
            'booking_number': b.booking_number,
            'date': b.created_at.strftime('%d %b'),
            'client_name': name,
            'amount': amt,
            'type': p_type,
            'status': p_status
        })

    # 10. Lead Status Distribution for Staff (Bar Chart)
    lead_status_distribution = [
        {'status': 'Hot', 'count': hot_leads, 'color': '#e11d48'},
        {'status': 'Warm', 'count': warm_leads, 'color': '#d97706'},
        {'status': 'Cold', 'count': cold_leads, 'color': '#64748b'},
        {'status': 'Closed', 'count': closed_leads, 'color': '#059669'},
    ]

    return Response({
        'user_info': {
            'name': greeting_name,
            'role': role_display,
            'email': user.email,
            'current_date': now.strftime('%A, %d %b %Y')
        },
        'booking_dashboard': {
            'total_bookings': total_bookings,
            'this_month': this_month_bookings,
            'growth_pct': booking_growth_pct,
            'growth_label': 'vs last month'
        },
        'account_dashboard': {
            'total_amount': total_amount,
            'advance_payment': advance_payment,
            'remaining_amount': remaining_amount
        },
        'lead_crm_dashboard': {
            'today_leads': today_leads,
            'this_month': this_month_leads,
            'total_leads': total_leads,
            'growth_pct': lead_growth_pct,
            'growth_label': 'vs last month'
        },
        'staff_dashboard': {
            'hot_leads': hot_leads,
            'warm_leads': warm_leads,
            'cold_leads': cold_leads,
            'closed_leads': closed_leads
        },
        'monthly_booking_overview': monthly_booking_overview,
        'selected_year': selected_year,
        'lead_source_analysis': {
            'total_leads': source_total,
            'sources': lead_source_analysis
        },
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
        'lead_status_distribution': lead_status_distribution
    })
