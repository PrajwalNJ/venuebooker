from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.urls import reverse
from .models import users
from .models import seminarHall
from .models import event
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.core.files.storage import default_storage
from datetime import datetime
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount


## Not a View
def getProfilePic(request):
    user = request.user
    social_account = SocialAccount.objects.get(user=user.id, provider='google')
    profile_picture_url = social_account.extra_data['picture']
    return profile_picture_url


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)

    context['happy_clients'] = event.objects.values('user_id').distinct().count()
    today = timezone.localdate()
    context['day'] = datetime.today().strftime('%A')[:3]
    context['today_events'] = event.objects.filter(date=today).count()
    context['count_seminarHalls'] = seminarHall.objects.count()
    context['users'] = users.objects.count()
    context['total_events'] =event.objects.count()

    context['halls'] = seminarHall.objects.filter(status = "Active")
    context['all_halls'] = seminarHall.objects.all()
    print(context['halls'])
    if request.method == "POST":
        context['submitted'] = True
        data = request.POST
        print(data)
        date1 = data['event_date']
        start_time = data['event_start']+':00'
        end_time = data['event_end']+':00'
        capacity = data['event_no_ppl']
        seminar = event.objects.all()
        clashes = []
        if(end_time<start_time):
            context['returnMessage'] = "Improper timings"
        else:
            for i in seminar:
                if(str(i.date) == str(date1) and ((str(i.start_time) <= str(end_time) and str(i.end_time)>=str(end_time)) or (str(i.start_time)<=str(start_time) and str(i.end_time)>=str(start_time)) or (str(i.start_time) <= str(end_time) and str(i.start_time)>=str(start_time)))):
                    clashes.append((i.location_id).id)
            all_seminar = seminarHall.objects.all()
            available = []
            for i in all_seminar:
                # print(i.capacity, int(str(capacity)), i.capacity > int(str(capacity)))
                if(i.id not in clashes and i.capacity > int(str(capacity))):
                    available.append(i)
            context['availableHalls'] = available

            if not available:
                context['returnMessage'] = "No Seminar Halls are available for the entered requirement."

            context['availability'] = True

    return render(request, 'index.html',context)

@login_required
def home(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
    try:
        person = users.objects.get(email=request.user.email)
        context['returnMessage'] = "Login Successful!!"
        if(person.designation == "Admin"):
            request.session['role'] = "Admin"
            return render(request, "admin_main.html", context)
        elif(person.designation == "HoD"):
            request.session['role'] = "HoD"
            return render(request, "hod_main.html", context)
        elif(person.designation == "Staff"):
            request.session['role'] = "Staff"
            return render(request, "staff_main.html", context)
    except:
        returnMessage= "Please Login only as Staff, HoD or Admin with RVCE mail id only."
        context = {}
        context['happy_clients'] = event.objects.values('user_id').distinct().count()
        today = timezone.localdate()
        context['day'] = datetime.today().strftime('%A')[:3]
        context['today_events'] = event.objects.filter(date=today).count()
        context['count_seminarHalls'] = seminarHall.objects.count()
        context['users'] = users.objects.count()
        context['halls'] = seminarHall.objects.all()
        context['returnMessage'] = returnMessage
        logout(request)
        return render(request, "index.html", context)



def logout_view(request):
    try:
        logout(request)
    except:
        return redirect("/")
    return redirect("/")

def login(request):
    return render(request, 'login_vb.html')


@login_required
def staff_main(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Staff"):
            return render(request,'staff_main.html', context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def staff_booking(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Staff"):

            context['halls'] = seminarHall.objects.filter(status = "Active")
            context['HoD'] = users.objects.filter(designation = "HoD")
            if request.method == "POST":
                print(request.POST)
                data = request.POST
                obj =users.objects.get(email = request.user.email)
                user_id = obj
                name = data['event_name']
                date1 = data['event_date']
                start_time = data['event_start']+':00'
                end_time = data['event_end']+':00'
                status_HoD = "pending"
                status_Admin = "pending"
                audience = data['event_no_ppl']
                agenda = data['event_agenda']
                same_seminar = event.objects.filter(location_id = data['sem_hall_chosen'])
                clashes = []
                for i in same_seminar:
                    if(str(i.date) == str(date1) and ((str(i.start_time) <= str(end_time) and str(i.end_time)>=str(end_time)) or (str(i.start_time)<=str(start_time) and str(i.end_time)>=str(start_time))or (str(i.start_time) <= str(end_time) and str(i.start_time)>=str(start_time)))):
                        clashes.append(i)
                obj =users.objects.get(id = data['req_hod'])
                hod_id = obj
                obj =seminarHall.objects.get(id = data['sem_hall_chosen'])
                location_id = obj
                if((obj.capacity)>int(str(audience))):
                    if(end_time>start_time):
                        if(not clashes):
                            try:
                                obj = event(user_id = user_id, name = name,agenda = agenda, status_HoD = status_HoD, status_Admin = status_Admin, date = date1, start_time = start_time, end_time = end_time, audience = audience,location_id = location_id,hod_id= hod_id)
                                obj.save()
                                context['returnMessage'] = "Request successfully made"
                                email = user_id.email
                                try:
                                    user = User.objects.get(email=email)
                                    first_name = user.first_name
                                except User.DoesNotExist:
                                    first_name = email.split('@')[0]
                                response = send_mail("[VenueBooker] Event Has been requested by " + first_name,"Hello HoD "+hod_id.code+ "! \nNew booking requests have been raised on VenueBooker, that are waiting for your verification. \n\nPlease login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify them. \n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[hod_id.email],fail_silently=False)
                                response1 = send_mail("[VenueBooker] You have raised a booking request!", "Hello "+first_name+"!\nWe received a booking request from your end. The same has been forworded to the requested personnel for approval.\n\nThe request raised is for - \""+name+"\" with, \nBooking ID: RV"+str(user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Pending \n\nPlease use these for further communications. Meanwhile, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and track your event approval status.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[user_id.email],fail_silently=False)
                            except:
                                    context['returnMessage'] = "Request cannot be made"
                        else:
                            context['returnMessage'] = "Your event is clashing with another request please try a different date"
                    else:
                        context['returnMessage'] = "Inappropriate timing"
                else:
                    context['returnMessage'] = "Sorry the selected seminar hall cannot hold the audience"
            return render(request,"staff_booking.html", context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def hod_main(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "HoD"):
            return render(request,'hod_main.html', context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def hod_addStaff(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "HoD"):
            if request.method == 'POST':
                email = request.POST.get('staff_email')
                name = users.objects.get(email = request.user.email).department
                code = users.objects.get(email = request.user.email).code
                try:
                    obj = users(email = email,department = name, code = code,designation = "Staff")
                    obj.save()
                    context['returnMessage'] = "Staff successfully added"
                except:
                    context['returnMessage'] = "Staff could not be added"
            return render(request,'hod_addStaff.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def hod_viewStaff(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "HoD"):
            user = users.objects.filter(designation = "Staff")
            Staff = []
            for i in user:
                try:
                    user = User.objects.get(email=i.email)
                    first_name = user.first_name +' '+ user.last_name
                except User.DoesNotExist:
                    first_name = i.email.split('@')[0]
                Staff.append({'id':i.id,'name':first_name,'email':i.email})
            context['Staff'] = Staff
            return render(request,'hod_viewStaff.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def hod_booking(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "HoD"):
            context['halls'] = seminarHall.objects.filter(status = "Active")
            if request.method == "POST":
                print(request.POST)
                data = request.POST
                obj =users.objects.get(email = request.user.email)
                user_id = obj
                name = data['event_name']
                date1 = data['event_date']
                start_time = data['event_start']+':00'
                end_time = data['event_end']+':00'
                status_HoD = "approved"
                status_Admin = "pending"
                feedback_HoD = "N/A"
                audience = data['event_no_ppl']
                agenda = data['event_agenda']
                same_seminar = event.objects.filter(location_id = data['sem_hall_chosen'])
                admin_id = users.objects.get(designation = "Admin")
                clashes = []
                for i in same_seminar:
                    if(str(i.date) == str(date1) and ((str(i.start_time) <= str(end_time) and str(i.end_time)>=str(end_time))or (str(i.start_time)<=str(start_time) and str(i.end_time)>=str(start_time))or (str(i.start_time) <= str(end_time) and str(i.start_time)>=str(start_time)))):
                        clashes.append(i)
                hod_id = user_id
                obj =seminarHall.objects.get(id = data['sem_hall_chosen'])
                location_id = obj
                if((obj.capacity)>int(str(audience))):
                    if(end_time>start_time):
                        if(not clashes):
                            try:
                                obj = event(user_id = user_id, name = name,agenda = agenda, status_HoD = status_HoD, status_Admin = status_Admin, date = date1, start_time = start_time, end_time = end_time, audience = audience,location_id = location_id,hod_id= hod_id, feedback_HoD= feedback_HoD)
                                obj.save()
                                context['returnMessage'] = "Request successfully made"
                                email = user_id.email
                                try:
                                    user = User.objects.get(email=email)
                                    first_name = user.first_name
                                except User.DoesNotExist:
                                    first_name = email.split('@')[0]
                                # response = send_mail("Event Has been requested by " + first_name,"Hello Admin!\n there are requests waiting for you on the venue booker portal please login and look into it\n\n Thank you\nRegards\n","sameeksha.keshav@gmail.com",[admin_id.email],fail_silently=False)
                                response = send_mail("[VenueBooker] Event Has been requested by " + first_name, "Hello Admin! \nNew booking requests have been raised on VenueBooker, that are waiting for your verification. \n\nPlease login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify them. \n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[admin_id.email],fail_silently=False)
                                response1 = send_mail("[VenueBooker] You have raised a booking request!", "Hello "+first_name+"!\nWe received a booking request from your end. The same has been forworded to the Admin for approval.\n\nThe request raised is for - \""+name+"\" with, \nBooking ID: RV"+str(user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Pending \n\nPlease use these for further communications. Meanwhile, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and track your event approval status.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[user_id.email],fail_silently=False)
                            except:
                                    context['returnMessage'] = "Request could not be made"
                        else:
                            context['returnMessage'] = "Your event is clashing with another request please try a different date"
                    else:
                        context['returnMessage'] = "Inappropriate timing"
                else:
                    context['returnMessage'] = "Sorry the selected seminar hall cannot hold the audience"
            return render(request,"HoD_booking.html", context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def hod_requests(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "HoD"):
            hod_id = users.objects.get(email = request.user.email)
            requests = event.objects.filter(hod_id = hod_id)
            requests = requests.exclude(user_id = hod_id)
            all = []
            for i in requests:
                name = i.name
                organizer_email = i.user_id.email
                try:
                    user = User.objects.get(email=organizer_email)
                    first_name = user.first_name +' '+ user.last_name
                except User.DoesNotExist:
                    first_name = organizer_email.split('@')[0]
                HoD = "HoD - " + i.hod_id.code
                venue = i.location_id.name
                venueId = i.location_id.id
                Date = i.date
                StartTime = i.start_time
                EndTime = i.end_time
                Audience = i.audience
                today = timezone.localdate()
                status = "Pending"
                final = "Pending"
                if(i.status_HoD == "approved" and i.status_Admin == "approved"):
                    status = "Approved by Admin"
                    final = "Approved"
                elif(i.status_HoD == "approved" and i.status_Admin == "pending"):
                    status = "Approved by HoD"
                    final = "Pending"
                elif(i.status_HoD == "approved" and i.status_Admin == "rejected"):
                    status = "Rejected by Admin"
                    final = "Rejected"
                elif(i.status_HoD == "rejected"):
                    status = "Rejected by HoD"
                    final = "Rejected"
                elif(i.status_HoD == "pending"):
                    status = "Pending"
                    final = "Pending"
                if(i.date<today):
                    status = "Expired"
                    final = "Expired"
                id = "RV"+str(i.user_id.id)+"VB"+str(i.id)
                all.append({ 'name' : name, 'organizer_email': organizer_email,'first_name':first_name,'HoD':HoD,'venue':venue, 'venueId': venueId,
                            'Date' : Date, 'startTime':StartTime, 'endTime':EndTime,'audience':Audience,'status':status,'final':final,'id':id, 'eventId': i.id})

                all.reverse()
                context['requests'] = all

            return render(request,'HoD_requests.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_main(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            return render(request,'admin_main.html', context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_booking(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            context['halls'] = seminarHall.objects.filter(status = "Active")
            if request.method == "POST":
                print(request.POST)
                data = request.POST
                obj =users.objects.get(email = request.user.email)
                user_id = obj
                name = data['event_name']
                date1 = data['event_date']
                start_time = data['event_start']+':00'
                end_time = data['event_end']+':00'
                status_HoD = "approved"
                status_Admin = "approved"
                feedback_HoD = "N/A"
                feedback_Admin = "N/A"
                audience = data['event_no_ppl']
                agenda = data['event_agenda']
                same_seminar = event.objects.filter(location_id = data['sem_hall_chosen'])
                admin_id = users.objects.get(designation = "Admin")
                clashes = []
                for i in same_seminar:
                    if(str(i.date) == str(date1) and ((str(i.start_time) <= str(end_time) and str(i.end_time)>=str(end_time))or (str(i.start_time)<=str(start_time) and str(i.end_time)>=str(start_time))or (str(i.start_time) <= str(end_time) and str(i.start_time)>=str(start_time)))):
                        clashes.append(i)
                hod_id = user_id
                obj =seminarHall.objects.get(id = data['sem_hall_chosen'])
                location_id = obj
                if((obj.capacity)>int(str(audience))):
                    if(end_time>start_time):
                        if(not clashes):
                            try:
                                obj = event(user_id = user_id, name = name,agenda = agenda, status_HoD = status_HoD, status_Admin = status_Admin, date = date1, start_time = start_time, end_time = end_time, audience = audience,location_id = location_id,hod_id= hod_id, feedback_HoD=feedback_HoD,feedback_Admin=feedback_Admin)
                                obj.save()
                                context['returnMessage'] = "Request successfully made"
                                email = user_id.email
                                try:
                                    user = User.objects.get(email=email)
                                    first_name = user.first_name
                                except User.DoesNotExist:
                                    first_name = email.split('@')[0]
                                # response = send_mail("Event Has been requested by " + first_name,"Hello!!\n Your event with the following details has been approved.\n"+"Event name:"+obj.name+"\n"+"Date:"+obj.date+"\n"+"Start Time:"+obj.start_time+"\n"+"End Time:"+obj.end_time+"\n"+"location:"+location_id.name+"\n"+"Incharge Details:"+location_id.incharge+"\n"+"Please contact the incharge for further details and confirmation", "sameeksha.keshav@gmail.com", [admin_id.email], fail_silently=False)
                                # response = send_mail("[VenueBooker] Event Has been requested by " + first_name, "Hello Admin! \nNew booking requests have been raised on VenueBooker, that are waiting for your verification. \n\nPlease login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify them. \n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[admin_id.email],fail_silently=False)
                                response = send_mail("[VenueBooker] You have raised a booking request!", "Hello "+first_name+"!\nWe received a booking request from your end. The booking was successful and is approved.\n\nThe booking raised is for - \""+name+"\" with, \nBooking ID: RV"+str(user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Approved \n\nPlease use these for further communications. Meanwhile, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify the status of the booked event.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[user_id.email],fail_silently=False)
                            except:
                                    context['returnMessage'] = "Request could not be made"
                        else:
                            context['returnMessage'] = "Your event is clashing with another request please try a different date"
                    else:
                        context['returnMessage'] = "Inappropriate timing"
                else:
                    context['returnMessage'] = "Sorry the selected seminar hall cannot hold the audience"
            return render(request,"admin_booking.html", context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_requests(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            requests = event.objects.filter(status_HoD = "approved")
            requests = requests.exclude(user_id = person)
            all = []
            for i in requests:
                name = i.name
                organizer_email = i.user_id.email
                try:
                    user = User.objects.get(email=organizer_email)
                    first_name = user.first_name +' '+ user.last_name
                except User.DoesNotExist:
                    first_name = organizer_email.split('@')[0]
                HoD = "HoD - " + i.hod_id.code
                venue = i.location_id.name
                venueId = i.location_id.id
                Date = i.date
                StartTime = i.start_time
                EndTime = i.end_time
                today = timezone.localdate()
                Audience = i.audience
                status = "Pending"
                final = "Pending"
                if(i.status_Admin == "approved"):
                    status = "Approved by Admin"
                    final = "Approved"
                elif(i.status_Admin == "pending"):
                    status = "Approved by HoD"
                    final = "Pending"
                elif(i.status_Admin == "rejected"):
                    status = "Rejected by Admin"
                    final = "Rejected"

                if(i.date<today):
                    status = "Expired"
                    final = "Expired"
                id = "RV"+str(i.user_id.id)+"VB"+str(i.id)
                all.append({ 'name' : name, 'organizer_email': organizer_email,'first_name':first_name,'HoD':HoD,'venue':venue, 'venueId': venueId,
                            'Date' : Date, 'startTime':StartTime, 'endTime':EndTime,'audience':Audience,'status':status,'final':final,'id':id, 'eventId': i.id})

                all.reverse()
                context['requests'] = all

            return render(request,'admin_requests.html', context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_addHoD(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            if request.method == 'POST':
                email = request.POST.get('hod_email')
                department = request.POST.get('dept_name')
                code = request.POST.get('dept_code')
                try:
                    obj = users(email = email,department = department, code = code, designation = "HoD")
                    obj.save()
                    context['returnMessage'] = "HoD successfully added"
                except:
                    context['returnMessage'] = "HoD could not be added"
            return render(request,'admin_addHoD.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_viewHoD(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            context['HoD'] = users.objects.filter(designation = "HoD")
            return render(request,'admin_viewHoD.html', context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_addSem(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            if request.method == 'POST':
                capacity = request.POST.get('sem_capacity')
                name = request.POST.get('sem_name')
                incharge = request.POST.get('sem_incharge')
                image_file = request.FILES['sem_pic']
                try:
                    obj = seminarHall(capacity = capacity, name = name, incharge = incharge)
                    obj.save()
                    image_path = default_storage.save('venuebooker/app_shms/static/halls/' + str(obj.id)+'.jpg', image_file)
                    context['returnMessage'] = "Seminar Hall successfully added"
                except:
                    context['returnMessage'] = "Seminar Hall could not be added"
            return render(request,'admin_addSem.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_updateSem(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            context['halls'] = seminarHall.objects.all()
            if request.method == 'POST':
                capacity = request.POST.get('sem_capacity')
                name = request.POST.get('sem_hall_selected')
                incharge = request.POST.get('sem_incharge')
                image_file = request.FILES['sem_pic']
                try:
                    obj_to_del = seminarHall.objects.get(name = name)
                    obj_to_del.delete()

                    obj = seminarHall(capacity = capacity, name = name, incharge = incharge)
                    obj.capacity = capacity
                    obj.incharge = incharge
                    obj.save()
                    image_path = default_storage.save('venuebooker/app_shms/static/halls/' + str(obj.id)+'.jpg', image_file)
                    context['returnMessage'] = "Seminar Hall successfully updated"
                except:
                    context['returnMessage'] = "Seminar Hall could not be updated"
            return render(request,'admin_updateSem.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def admin_statusSem(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
        person = users.objects.get(email=request.user.email)
        if(person.designation == "Admin"):
            context['halls'] = seminarHall.objects.all()
            if request.method == 'POST':
                name = request.POST.get('sem_hall_selected')
                status = request.POST.get('sem_hall_status')
                try:
                    obj = seminarHall.objects.get(name = name)
                    obj.status = status
                    obj.save()
                    context['returnMessage'] = "Seminar Hall successfully updated"
                except:
                    context['returnMessage'] = "Seminar Hall could not be updated"
            return render(request,'admin_updateSem.html',context)

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def view_bookings(request):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)

        user_id = users.objects.get(email = request.user.email)
        requests = event.objects.filter(user_id = user_id)
        all = []
        for i in requests:
            name = i.name
            organizer_email = i.user_id.email

            person = users.objects.get(email=organizer_email)
            organizer_designation = person.designation

            try:
                user = User.objects.get(email = organizer_email)
                first_name = user.first_name +' '+ user.last_name
            except User.DoesNotExist:
                first_name = organizer_email.split('@')[0]

            if organizer_designation == "Admin":
                HoD = "N/A"
            else:
                HoD = "HoD - " + i.hod_id.code


            venue = i.location_id.name
            venueId = i.location_id.id
            Date = i.date
            today = timezone.localdate()
            StartTime = i.start_time
            EndTime = i.end_time
            Audience = i.audience
            status = "Pending"
            final = "Pending"
            if(i.status_HoD == "approved" and i.status_Admin == "approved"):
                status = "Approved by Admin"
                final = "Approved"
            elif(i.status_HoD == "approved" and i.status_Admin == "pending"):
                status = "Approved by HoD"
                final = "Pending"
            elif(i.status_HoD == "approved" and i.status_Admin == "rejected"):
                status = "Rejected by Admin"
                final = "Rejected"
            elif(i.status_HoD == "rejected"):
                status = "Rejected by HoD"
                final = "Rejected"
            elif(i.status_HoD == "pending"):
                status = "Pending"
                final = "Pending"
            if(i.date<today):
                status = "Expired"
                final = "Expired"
            id = "RV"+str(i.user_id.id)+"VB"+str(i.id)
            all.append({ 'name' : name, 'organizer_email': organizer_email,'first_name':first_name,'HoD':HoD,'venue':venue, 'venueId': venueId,
                        'Date' : Date, 'startTime':StartTime, 'endTime':EndTime,'audience':Audience,'status':status,'final':final,'id':id, 'eventId': i.id})

            all.reverse()
            context['requests'] = all

        person = users.objects.get(email=request.user.email)

        if(person.designation == "Admin"):
            return render(request,'adminViewBookings.html', context)
        elif(person.designation == "HoD"):
            return render(request,'hodViewBookings.html', context)
        elif(person.designation == "Staff"):
            return render(request,'staffViewBookings.html', context)

        # return render(request,'hodViewBookings.html', context) #################################### OYEEEEEEEEEE REMOVE THIS!!!!!!!!!

    return HttpResponse("Bad request\n Not authorized to view the page")

def seminar(request,id):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)
    try:
        obj = seminarHall.objects.get(id = id)
        context['obj'] = obj
    except:
        return HttpResponse("Bad request<br> Seminar Hall Does not exist")
    return render(request,'seminar.html', context)

@login_required
def event_view(request, id, returnMessage):
    context = {}
    if request.user.is_authenticated:
        context['profile_picture_url'] = getProfilePic(request)

        try:
            i = event.objects.get(id = id)
            name = i.name
            organizer_email = i.user_id.email

            organizer = users.objects.get(email=organizer_email)
            organizer_designation = organizer.designation

            person = users.objects.get(email=request.user.email)
            current_user_designation = person.designation
            current_user_email = request.user.email

            if organizer_email == current_user_email or i.hod_id.email == current_user_email or (i.feedback_HoD and current_user_designation == "Admin"):
                try:
                    user = User.objects.get(email=organizer_email)
                    first_name = user.first_name +' '+ user.last_name
                except User.DoesNotExist:
                    first_name = organizer_email.split('@')[0]

                if organizer_designation == "Admin":
                    HoD = "N/A"
                else:
                    HoD = "HoD - " + i.hod_id.code

                venue = i.location_id.name
                venueId = i.location_id.id
                Date = i.date
                StartTime = i.start_time
                EndTime = i.end_time
                today = timezone.localdate()
                Audience = i.audience
                status = "Pending"
                final = "Pending"
                if(i.status_HoD == "approved" and i.status_Admin == "approved"):
                    status = "Approved by Admin"
                    final = "Approved"
                elif(i.status_HoD == "approved" and i.status_Admin == "pending"):
                    status = "Approved by HoD"
                    final = "Pending"
                elif(i.status_HoD == "approved" and i.status_Admin == "rejected"):
                    status = "Rejected by Admin"
                    final = "Rejected"
                elif(i.status_HoD == "rejected"):
                    status = "Rejected by HoD"
                    final = "Rejected"
                elif(i.status_HoD == "pending"):
                    status = "Pending"
                    final = "Pending"
                if(i.date<today):
                    status = "Expired"
                    final = "Expired"
                id = "RV"+str(i.user_id.id)+"VB"+str(i.id)

                Agenda = i.agenda
                HoD_feedback = i.feedback_HoD
                admin_feedback = i.feedback_Admin
                all = { 'name' : name, 'organizer_email': organizer_email,'first_name':first_name,'HoD':HoD,'venue':venue, 'venueId': venueId, 'eventId': i.id,
                            'Date' : Date, 'startTime':StartTime, 'endTime':EndTime,'audience':Audience,'status':status,'final':final,'id':id,'agenda':Agenda,'hod_feedback': HoD_feedback, 'admin_feedback': admin_feedback}

                if returnMessage != 'null':
                    context['returnMessage'] = returnMessage

                context.update(all)

                print(context)
                return render(request, 'event_view.html', context)

            else:
                return HttpResponse("Bad request\n Not authorized to view the page")

        except:
            return HttpResponse("Bad Request\n The event does not exist\n")

    return HttpResponse("Bad request\n Not authorized to view the page")

@login_required
def event_request(request, id):
    context = {}
    if request.user.is_authenticated:
        context['id'] = id
        if request.method == 'POST':
            email = request.user.email
            person = users.objects.get(email=email)
            feedback = request.POST.get('feedback')
            clicked_button = request.POST.get('action')
            print(clicked_button)

            admin_id = users.objects.get(designation = "Admin")

            if clicked_button == 'approve':
                if(person.designation == "HoD"):
                    try:
                        obj = event.objects.get(id = id)
                        obj.status_HoD = "approved"
                        obj.feedback_HoD = feedback
                        obj.save()
                        returnMessage = "Event Approved"

                        response = send_mail("[VenueBooker] Event Request has been raised", "Hello Admin! \nNew booking requests have been raised on VenueBooker, that are waiting for your verification. \n\nPlease login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify them. \n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[admin_id.email],fail_silently=False)
                        response = send_mail("[VenueBooker] Update on Request - RV"+str(obj.user_id.id)+"VB"+str(obj.id), "Hello!\nWe are pleased to inform you that your booking request is approved by the request personnel and is awaiting Admin approval.\n\nThe booking request was for - \""+obj.name+"\" with, \nBooking ID: RV"+str(obj.user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Pending\n\nPlease use these for further communications. Meanwhile, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify the status of the booked event.\n\nYou may also find some feedback/suggestions from the approving personnel.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[obj.user_id.email],fail_silently=False)
                    except:
                        returnMessage = "Event could not be approved"
                elif(person.designation == "Admin"):
                    try:
                        obj = event.objects.get(id = id)
                        obj.status_Admin = "approved"
                        obj.feedback_Admin = feedback
                        obj.save()
                        returnMessage = "Event Approved"

                        response = send_mail("[VenueBooker] Update on Request - RV"+str(obj.user_id.id)+"VB"+str(obj.id), "Hello!\nWe are pleased to inform you that your booking request is approved by the Admin and your requested seminar hall is allocated.\n\nThe booking request was for - \""+obj.name+"\" with, \nBooking ID: RV"+str(obj.user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Approved\n\nFor more details of the booking, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify the status and details of the booked event.\n\nYou may also find some feedback/suggestions from the Admin.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[obj.user_id.email],fail_silently=False)
                    except:
                        returnMessage = "Event could not be approved"
                else:
                    return HttpResponse("Bad Request")
            elif clicked_button == 'reject':
                if(person.designation == "HoD"):
                    try:
                        obj = event.objects.get(id = id)
                        obj.status_HoD = "rejected"
                        obj.feedback_HoD = feedback
                        obj.save()
                        returnMessage = "Event Rejected"

                        response = send_mail("[VenueBooker] Update on Request - RV"+str(obj.user_id.id)+"VB"+str(obj.id), "Hello!\nWe are sorry to inform you that your booking request is rejected by the request personnel.\n\nThe booking request was for - \""+obj.name+"\" with, \nBooking ID: RV"+str(obj.user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Rejected\n\nPlease use these for further communications. Meanwhile, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verify the status of the booked event.\n\nYou may also find some feedback/suggestions from the approving personnel.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[obj.user_id.email],fail_silently=False)
                    except:
                        returnMessage = "Event could not be Rejected"
                elif(person.designation == "Admin"):
                    try:
                        obj = event.objects.get(id = id)
                        obj.status_Admin = "rejected"
                        obj.feedback_Admin = feedback
                        obj.save()
                        returnMessage = "Event rejected"
                        print(obj.feedback_Admin)

                        response = send_mail("[VenueBooker] Update on Request - RV"+str(obj.user_id.id)+"VB"+str(obj.id), "Hello!\nWe are sorry to inform you that your booking request is rejected by the Admin.\n\nThe booking request was for - \""+obj.name+"\" with, \nBooking ID: RV"+str(obj.user_id.id)+"VB"+str(obj.id) +"\n\nCurrent Status: Rejected\n\nFor more details of the booking, you may login to VenueBooker (https://prajwalnj.pythonanywhere.com) using your RVCE Google Account and verifying the details under 'My Bookings' section.\n\nYou may also find some feedback/suggestions from the Admin.\n\nThank you\nRegards\nVenueBooker Team","sameeksha.keshav@gmail.com",[obj.user_id.email],fail_silently=False)
                    except:
                        returnMessage = "Event could not be rejected"
                else:
                    return HttpResponse("Bad Request")

        return redirect(reverse('event_view', args=[id, returnMessage]))

    return HttpResponse("Bad request\n Not authorized to view the page")