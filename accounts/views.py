
from django.shortcuts import render, redirect


from django.contrib.auth import get_user_model, authenticate, login, logout

from django.contrib.auth.decorators import login_required
from django.contrib import messages

User = get_user_model()

def register_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not email or not username or not password:
            return render(request, 'register.html', {
                'error': 'All fields are required! Please fill out every box.'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {
                'error': 'A user account with this email address already exists!'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'This username is already taken. Please choose a different one!'
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect('login')

    return render(request, 'register.html')

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            return render(request, 'login.html', {
                'error': 'Both email and password are required to sign in!'
            })

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid email address or password. Please try again!'
            })

    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    
    return redirect('login')


@login_required
def become_seller(request):
    if request.method != 'POST':
        messages.error(request, 'Use the Become seller button to upgrade your account.')
        return redirect('dashboard')

    user = request.user
    if user.is_seller:
        messages.info(request, 'You are already a seller.')
        return redirect('dashboard')
    user.is_seller = True
    user.save()
    messages.success(request, 'You are now a seller — you can add products.')
    return redirect('dashboard')
