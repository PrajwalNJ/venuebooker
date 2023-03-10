"""
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')

    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [    
    path('', views.index, name="index"),
    path('login/', views.login, name = "login"),
    path('home/', views.home, name="home"),
    path('staff/', views.staff_main, name="staff"),
    path('staffBooking/', views.staff_booking, name="staff_booking"),
    path('hod/', views.hod_main, name="hod"),
    path('hodAddStaff/', views.hod_addStaff, name="hod_addStaff"),
    path('hodViewStaff/', views.hod_viewStaff, name="hod_viewStaff"),
    path('HoDBooking/', views.hod_booking, name="hod_booking"),
    path('HoDRequests/', views.hod_requests, name="hod_requests"),
    path('manager/', views.admin_main, name="manager"),
    path('AdminBooking/', views.admin_booking, name="admin_booking"),
    path('adminRequests/', views.admin_requests, name="admin_requests"),
    path('adminAddHoD/', views.admin_addHoD, name="admin_addHoD"),
    path('adminViewHoD/', views.admin_viewHoD, name="admin_viewHoD"),
    path('adminAddSem/', views.admin_addSem, name="admin_addSem"),
    path('adminUpdateSem/', views.admin_updateSem, name="admin_updateSem"),
    path('adminStatusSem/', views.admin_statusSem, name="admin_statusSem"),
    path('viewBookings/', views.view_bookings, name="view_bookings"),
    path('seminarhall/<int:id>/', views.seminar, name="seminarhall"),
    path('eventView/<int:id>/<str:returnMessage>', views.event_view, name="event_view"),
    # path('eventRequest/<int:request_id>/<str:action>/',views.event_request,name = 'event_request'),
    path('eventRequest/<int:id>/',views.event_request,name = 'event_request'),
    path('logout/', views.logout_view, name="logout"),
]
