"""
Universal Multi-Tenant Scoping and Filtering Engine for Masar Umrah CRM
-----------------------------------------------------------------------
Principles:
1. SuperAdmin is the Platform Owner:
   - Full global visibility across all tenants.
   - Dynamic cross-tenant filtering by `tenant_id`, `start_date`, `end_date`, `date`, `category`, and `status`.
   - SuperAdmin does not own personal leads, personal bookings, or operational quotas.
2. Tenants (franchisesadmin) are Feature / Business Owners:
   - Strict data isolation: One tenant can NEVER see or mutate another tenant's data.
   - Telecallers, operations staff, and accountants are scoped to their parent Tenant agency.
"""

from datetime import datetime, time
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime


def get_param(request, key, default=None):
    """
    Safely retrieves a query parameter from either a DRF Request (query_params)
    or a standard Django WSGIRequest (GET).
    """
    if hasattr(request, 'query_params'):
        val = request.query_params.get(key)
        if val is not None:
            return val
    if hasattr(request, 'GET'):
        val = request.GET.get(key)
        if val is not None:
            return val
    return default


def get_user_tenant(user):
    """
    Returns the Tenant (Franchise Admin) for the given user:
    - If user is franchisesadmin, returns the user themselves.
    - If user is agency staff (caller, operations, accountant) with a parent, returns user.created_by.
    - If user is superadmin, returns None (platform owner).
    """
    if not user or not user.is_authenticated:
        return None
    if getattr(user, 'role', '') in ['franchisesadmin', 'franchiseadmin']:
        return user
    if getattr(user, 'created_by', None):
        parent = user.created_by
        if getattr(parent, 'role', '') in ['franchisesadmin', 'franchiseadmin']:
            return parent
    return None


def apply_date_filters(queryset, request, date_field='created_at'):
    """
    Applies start_date, end_date, single date, or month/year filters to a queryset.
    Supports formats: YYYY-MM-DD
    """
    if not date_field or not hasattr(queryset.model, date_field):
        return queryset

    start_date_str = get_param(request, 'start_date') or get_param(request, 'from_date') or get_param(request, 'date_from')
    end_date_str = get_param(request, 'end_date') or get_param(request, 'to_date') or get_param(request, 'date_to')
    single_date_str = get_param(request, 'date') or get_param(request, 'exact_date')
    month_str = get_param(request, 'month')
    year_str = get_param(request, 'year')

    # Date Range: start_date to end_date
    if start_date_str and end_date_str:
        parsed_start = parse_date(str(start_date_str))
        parsed_end = parse_date(str(end_date_str))
        if parsed_start and parsed_end:
            start_dt = timezone.make_aware(datetime.combine(parsed_start, time.min))
            end_dt = timezone.make_aware(datetime.combine(parsed_end, time.max))
            queryset = queryset.filter(**{f"{date_field}__range": (start_dt, end_dt)})
        return queryset

    if start_date_str and not end_date_str:
        parsed_start = parse_date(str(start_date_str))
        if parsed_start:
            start_dt = timezone.make_aware(datetime.combine(parsed_start, time.min))
            queryset = queryset.filter(**{f"{date_field}__gte": start_dt})

    if end_date_str and not start_date_str:
        parsed_end = parse_date(str(end_date_str))
        if parsed_end:
            end_dt = timezone.make_aware(datetime.combine(parsed_end, time.max))
            queryset = queryset.filter(**{f"{date_field}__lte": end_dt})

    # Single Date filter
    if single_date_str:
        parsed_date = parse_date(str(single_date_str))
        if parsed_date:
            queryset = queryset.filter(**{f"{date_field}__date": parsed_date})

    # Month & Year filter
    if month_str and str(month_str).isdigit():
        queryset = queryset.filter(**{f"{date_field}__month": int(month_str)})
    if year_str and str(year_str).isdigit():
        queryset = queryset.filter(**{f"{date_field}__year": int(year_str)})

    return queryset


def apply_category_filters(queryset, request, category_field='category'):
    """
    Applies category / type filter to the queryset if query parameters are provided.
    """
    if not category_field:
        return queryset

    category_val = (
        get_param(request, 'category') or
        get_param(request, 'package_type') or
        get_param(request, 'template_type') or
        get_param(request, 'visa_type') or
        get_param(request, 'journey_type')
    )

    if category_val and str(category_val).lower() != 'all':
        if hasattr(queryset.model, category_field):
            queryset = queryset.filter(**{category_field: category_val})

    return queryset


def apply_status_filter(queryset, request, status_field='status'):
    """
    Applies status filter to the queryset.
    """
    if not status_field or not hasattr(queryset.model, status_field):
        return queryset

    status_val = get_param(request, 'status')
    if status_val and str(status_val).lower() != 'all':
        queryset = queryset.filter(**{status_field: status_val})

    return queryset


def get_tenant_scoped_queryset(
    request,
    queryset,
    user_field='created_by',
    secondary_user_field=None,
    date_field='created_at',
    category_field=None,
    status_field='status'
):
    """
    Comprehensive multi-tenant scoping and filtering helper:
    
    1. SuperAdmin:
       - Sees all platform records by default.
       - Can filter by ?tenant_id=<id> or ?tenant=<id>
       - Can filter by date range, single date, category, status.
       
    2. Tenant Admin (franchisesadmin):
       - Strictly limited to records created by themselves or their staff.
       - One tenant CANNOT view records belonging to any other tenant.
       
    3. Agency Staff (sells_caller, operations, accountant):
       - Tied to their parent tenant agency head (user.created_by) or themselves.
       
    4. Date & Category Filtering:
       - Seamlessly applied to all roles.
    """
    user = request.user
    if not user.is_authenticated:
        return queryset.none()

    # --- Role-Based Tenant Scoping ---
    if user.role == 'superadmin':
        tenant_id = get_param(request, 'tenant_id') or get_param(request, 'tenant')
        if tenant_id and str(tenant_id).lower() != 'all':
            try:
                t_id = int(tenant_id)
                q_expr = Q(**{f"{user_field}_id": t_id}) | Q(**{f"{user_field}__created_by_id": t_id})
                if secondary_user_field:
                    q_expr |= Q(**{f"{secondary_user_field}_id": t_id}) | Q(**{f"{secondary_user_field}__created_by_id": t_id})
                queryset = queryset.filter(q_expr)
            except (ValueError, TypeError):
                pass
    elif user.role in ['franchisesadmin', 'franchiseadmin']:
        q_expr = Q(**{user_field: user}) | Q(**{f"{user_field}__created_by": user})
        if secondary_user_field:
            q_expr |= Q(**{secondary_user_field: user}) | Q(**{f"{secondary_user_field}__created_by": user})
        queryset = queryset.filter(q_expr)
    elif user.role == 'sells_caller':
        agency_head = user.created_by or user
        q_expr = Q(**{user_field: user}) | Q(**{user_field: agency_head})
        if secondary_user_field:
            q_expr |= Q(**{secondary_user_field: user}) | Q(**{secondary_user_field: agency_head})
        queryset = queryset.filter(q_expr)
    elif user.role in ['accountant', 'operations']:
        agency_head = user.created_by or user
        q_expr = Q(**{user_field: user}) | Q(**{user_field: agency_head})
        if secondary_user_field:
            q_expr |= Q(**{secondary_user_field: user}) | Q(**{secondary_user_field: agency_head})
        queryset = queryset.filter(q_expr)
    else:
        queryset = queryset.filter(**{user_field: user})

    # --- Date Filtering ---
    queryset = apply_date_filters(queryset, request, date_field=date_field)

    # --- Category Filtering ---
    queryset = apply_category_filters(queryset, request, category_field=category_field)

    # --- Status Filtering ---
    queryset = apply_status_filter(queryset, request, status_field=status_field)

    return queryset
