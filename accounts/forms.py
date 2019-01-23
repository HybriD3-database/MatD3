from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import UserProfile


class RegistrationForm(UserCreationForm):
    all_fields = ('username', 'first_name', 'last_name', 'email', 'password1',
                  'password2')
    email = forms.EmailField(max_length=200, help_text='Required',
                             required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        )

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class ChangePasswordForm(PasswordChangeForm):
    all_fields = ('old_password', 'new_password1', 'new_password2')

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class EditProfileForm(forms.ModelForm):
    all_fields = ('description', 'institution', 'website', 'phone', 'image')

    class Meta:
        model = UserProfile
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'
            if(fieldname == 'image'):
                self.fields[fieldname].widget.attrs['class'] = (
                    'form-control-file')


class EditUserForm(forms.ModelForm):
    all_fields = ('first_name', 'last_name', 'email')

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'
