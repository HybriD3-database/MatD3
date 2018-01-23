# -*- coding: utf-8 -*-


from django.shortcuts import render, redirect
from accounts.forms import (
RegistrationForm,
EditProfileForm,
EditUserForm,
ChangePasswordForm
)

from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.urls import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from .models import UserProfile
from django.core.mail import EmailMessage

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site

def home(request):
    return render(request, 'accounts/home.html')

def register(request):
    if request.method =='POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            form.save()
            user.save()
            current_site = get_current_site(request)
            message = render_to_string('accounts/activation_email.html', {
                'user':user,
                'domain':current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            print("message created")
            mail_subject = 'Activate your Hybrid3 database account.'
            from_email = 'Hybrid3 materials database <hybrid3project@duke.edu>'
            to_email = form.cleaned_data.get('email')
            print("user email gotten")
            email = EmailMessage(mail_subject, message, from_email, to=[to_email])
            email.send()
            print("email sent")
            text = 'Please confirm your email address to complete the registration'
        else:
            text = 'Registration failed. Please correct the errors and try again.'
        args = {
        'form': form,
        'text': text
        }
        return render(request, 'accounts/reg_form.html', args)
    else:
        form = RegistrationForm()

        args = {'form': form}
        return render(request, 'accounts/reg_form.html', args)

def activate(request, uidb64, token):
    template = 'accounts/activate.html'
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        text = "Thank you for your email confirmation. Now you can login to your account."
    else:
        text = "Activation link is invalid!"
    return render(request, template, {'text': text})

def view_profile(request, pk=None):
    if pk:
        user = User.objects.get(pk=pk)
    else:
        user = request.user
    args = {'user': user}
    return render(request, 'accounts/profile.html', args)

def edit_profile(request):
    template = 'accounts/edit_profile.html'
    user = request.user
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        user_form = EditUserForm(request.POST, instance=user)
        user_profile_form = EditProfileForm(request.POST, request.FILES, instance=user_profile)
        print(request.FILES)
        if user_form.is_valid() and user_profile_form.is_valid():
            user_form.save()
            user_profile_form.save()
            return redirect(reverse('accounts:view_profile'))
        else:
            args = {
                'user_form': user_form,
                'user_profile_form': user_profile_form,
                'text': 'Please fix the errors and try again.'
            }
            return render(request, template, args)
    else:
        user_form = EditUserForm(instance=user)
        user_profile_form = EditProfileForm(instance=user_profile)
        args = {
            'user_form': user_form,
            'user_profile_form': user_profile_form
        }
        return render(request, template, args)

def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(reverse('accounts:view_profile'))
        else:
            text = "An error occurred. Please try again later."
            form = ChangePasswordForm(user=request.user)
            args = {
                'form': form,
                'text': text
            }
            return render(request, 'accounts/change_password.html', args)

    else:
        form = ChangePasswordForm(user=request.user)
        args = {'form': form}
        return render(request, 'accounts/change_password.html', args)
