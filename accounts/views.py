# render: used to load and send HTML templates back to the browser.
# redirect: used to send the user to a different URL (like shifting pages).
from django.shortcuts import render, redirect

# the settings directory: "Which User blueprint is the active one right now?"
# This is safe and keeps our code completely modular.
from django.contrib.auth import get_user_model, authenticate, login, logout
# By placing this decorator directly above any view function, we instruct Django:
# "Ensure the visitor has an active stamped session pass. If they don't, lock the door,
# block the page, and kick them out straight to the login registration gate!"
from django.contrib.auth.decorators import login_required
from django.contrib import messages

User = get_user_model()

def register_user(request):
    # We check if the browser sent a POST request (meaning the user clicked "Submit" on the form).
    if request.method == 'POST':
        # We extract the email address directly from the form submission dictionary.
        # .strip() removes any accidental spaces the user might have typed at the start/end.
        email = request.POST.get('email', '').strip()
        # We extract the username nickname from the form submission.
        username = request.POST.get('username', '').strip()
        # We extract the password from the form submission.
        password = request.POST.get('password', '')

        # ---- VALIDATION 1: Ensure all fields are filled in ----
        # If any of the fields are completely empty, we reject the form.
        if not email or not username or not password:
            # We send them back to the form, displaying a clear validation error.
            return render(request, 'register.html', {
                'error': 'All fields are required! Please fill out every box.'
            })

        # ---- VALIDATION 2: Check if email is already registered ----
        # We ask our database if a user record with this exact email already exists.
        if User.objects.filter(email=email).exists():
            # We reload the registration page and inform the user that their email is already in use.
            return render(request, 'register.html', {
                'error': 'A user account with this email address already exists!'
            })

        # ---- VALIDATION 3: Check if username is already taken ----
        # We ask our database if a user record with this exact username nickname already exists.
        if User.objects.filter(username=username).exists():
            # We reload the page and tell them to pick a different nickname.
            return render(request, 'register.html', {
                'error': 'This username is already taken. Please choose a different one!'
            })

        # ---- STEP 4: Creating and saving the User securely ----
        # Why? Because 'create_user' automatically hashes the password!
        # safe. Even if someone steals the safe (database breach), they cannot read the password inside!
        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ---- STEP 5: Redirect to the login view ----
        # Now that the user is safely written in our database, we redirect them to the login page.
        # This will point to the URL mapped to the name 'login'.
        return redirect('login')

    # We simply render the empty HTML registration form.
    return render(request, 'register.html')

def login_user(request):
    # We check if the browser sent a POST request (meaning the user clicked "Sign In" on the form).
    if request.method == 'POST':
        # We extract the email address directly from the login form.
        # .strip() removes any accidental spaces the user might have typed at the start/end.
        email = request.POST.get('email', '').strip()
        # We extract the password directly from the login form.
        password = request.POST.get('password', '')

        # ---- VALIDATION 1: Ensure all fields are filled in ----
        if not email or not password:
            # We send them back to the login page, displaying a clear validation error.
            return render(request, 'login.html', {
                'error': 'Both email and password are required to sign in!'
            })

        # ---- STEP 2: Authenticate the user against the database ----
        # In our custom model, we configured 'email' as the main login identifier (USERNAME_FIELD).
        # However, Django's built-in 'authenticate' function always expects the login identifier
        # to be passed as the parameter named 'username'.
        # Therefore, we pass email under 'username=email' so the bouncer knows what to search for!
        user = authenticate(request, username=email, password=password)

        # ---- STEP 3: Check if authentication succeeded ----
        # If the email exists and the password hash matches, authenticate returns the User object.
        if user is not None:
            # ---- STEP 4: Start the session ----
            # This creates a secure, temporary session cookie in their browser.
            login(request, user)
            
            # ---- STEP 5: Redirect to the dashboard ----
            # Once authenticated and logged in, we send them to their dashboard home page.
            # (We will create and name this route 'dashboard' in Task 5).
            return redirect('dashboard')
        else:
            # We reload the login form with a clear error message.
            # whether it was the email or the password that was wrong!
            return render(request, 'login.html', {
                'error': 'Invalid email address or password. Please try again!'
            })

    return render(request, 'login.html')

def logout_user(request):
    # This automatically locates the active session cookie for this request,
    # completely deletes the session record from our database, and clears the cookie from the browser.
    logout(request)
    
    # After successfully destroying their session pass, we redirect the user to the login page.
    return redirect('login')


@login_required
def become_seller(request):
    if request.method != 'POST':
        messages.error(request, 'Use the Become seller button to upgrade your account.')
        return redirect('dashboard')

    # Allow a logged-in user to flag themselves as a seller.
    user = request.user
    if user.is_seller:
        messages.info(request, 'You are already a seller.')
        return redirect('dashboard')
    user.is_seller = True
    user.save()
    messages.success(request, 'You are now a seller — you can add products.')
    return redirect('dashboard')
