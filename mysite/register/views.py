from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
    else:   #se get
        form = UserCreationForm()
    return render(request, 'register/register.html', {'form': form})

def profile(request):

    return render(request, 'register/profile.html')

def username_change(request):
    
    if request.method == 'POST':
        if len(request.POST.get('new_username'))<30:
            user = request.user
            user.username = request.POST.get('new_username')
            user.save()
            return redirect(profile)
    else:
        return render(request, 'register/username_change_form.html')

    return render(request, 'register/username_change_form.html')
