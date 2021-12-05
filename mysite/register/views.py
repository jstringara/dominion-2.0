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


