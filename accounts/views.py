# This file is covered by the BSD license. See LICENSE in the root directory.
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode

from .forms import ChangePasswordForm
from .forms import EditProfileForm
from .forms import EditUserForm
from .forms import RegistrationForm
from .tokens import account_activation_token
from mainproject.settings import MATD3_NAME
from mainproject.settings import MATD3_URL


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            user.email_user(
                f'Activate Your {MATD3_NAME} Account',
                render_to_string('accounts/activation_email.html', {
                    'user': user,
                    'domain': get_current_site(request),
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
            )
            messages.success(
                request, 'Confirmation email has been sent. Check your email.')
            form = RegistrationForm()
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def activate(request, uid, token):
    try:
        pk = urlsafe_base64_decode(uid)
        user = User.objects.get(pk=pk)
        if not account_activation_token.check_token(user, token):
            raise User.DoesNotExist
        user.is_active = True
        user.save()
        login(request, user)
        Group.objects.get(name='users').user_set.add(user)
        # Notify all superusers of the new user
        email_addresses = list(User.objects.filter(
            is_superuser=True).values_list('email', flat=True))
        send_mail(f'{MATD3_URL}: new user created', '', 'matd3info',
                  email_addresses,
                  fail_silently=False,
                  html_message=(f'The account of "{user.username}" is '
                                'waiting to be elevated to staff status.'))
        messages.success(request, 'Account confirmed.')
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Activation link is invalid!')
    return redirect(reverse('accounts:profile'))


@login_required
def profile(request):
    user = request.user
    user_profile = user.userprofile
    if request.method == 'GET':
        user_form = EditUserForm(instance=request.user)
        user_profile_form = EditProfileForm(instance=user_profile)
        return render(request, 'accounts/profile.html', {
            'user_form': user_form,
            'user_profile_form': user_profile_form
        })
    elif request.method == 'POST':
        user_form = EditUserForm(request.POST, instance=request.user)
        user_profile_form = EditProfileForm(request.POST,
                                            instance=user_profile)
        if user_form.is_valid() and user_profile_form.is_valid():
            user_form.save()
            user_profile_form.save()
            messages.success(request, 'Profile information updated')
        else:
            messages.error(request, 'Could not update profile information')
        return redirect(reverse('accounts:profile'))


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Password successfully changed')
            return redirect(reverse('accounts:profile'))
        else:
            messages.error(request,
                           'Incorrect password or new passwords not matching')
    form = ChangePasswordForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
