from django.urls import path
from .views import EnquiryCreateView, EnquiryListView

urlpatterns = [
    path('contact-us/', EnquiryCreateView.as_view(), name='create-enquiry'),
    path('enquiries/', EnquiryListView.as_view(), name='list-enquiries'),
]
