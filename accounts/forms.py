import uuid
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UsernameField, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class SignUpWithEmailForm(forms.ModelForm):

    email = forms.EmailField(
        label=_('Email'),
        required=True,
        max_length=63,
        widget=forms.EmailInput(
            attrs={
                'placeholder': _('Email'),
            },
        ),
        help_text=_('Email cannot be changed after setting.')
    )

    field_order = ['username', 'email', 'first_name', 'last_name']

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        help_texts = {
            'username': '',
        }

    def __init__(self, email_endswith_strings=[], email_cant_endswith_strings=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_endswith_strings = email_endswith_strings
        self.email_cant_endswith_strings = email_cant_endswith_strings

    def clean_email(self):
        email = self.cleaned_data['email']
        email_endswith_valid_string = False if self.email_endswith_strings else True
        for email_endswith_string in self.email_endswith_strings:
            if email.endswith(email_endswith_string):
                email_endswith_valid_string = True
                break
        if not email_endswith_valid_string:
            self.add_error(
                'email',
                ValidationError(
                    _('The Email address must end with %(join_email_endswith_strings)s.'),
                    params={'join_email_endswith_strings': ', '.join(self.email_endswith_strings)},
                    code='invalid'
                )
            )
        email_endswith_invalid_string = False
        for email_cant_endswith_string in self.email_cant_endswith_strings:
            if email.endswith(email_cant_endswith_string):
                email_endswith_invalid_string = True
                break
        if email_endswith_invalid_string:
            self.add_error(
                'email',
                ValidationError(
                    _('The Email address must not end with %(join_email_cant_endswith_strings)s.'),
                    params={'join_email_cant_endswith_strings': ', '.join(self.email_cant_endswith_strings)},
                    code='invalid'
                )
            )
        if User.objects.filter(email=email).exists():
            self.add_error(
                'email',
                ValidationError(
                    _('A user with this Email already exists.'),
                    code='invalid'
                )
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        random_uuid_password = uuid.uuid4()
        user.set_password(random_uuid_password)
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        subject = '[Chief Firewall Admin] You have created an account.'
        message = (
            f'Hi {username},\n'
            '\n'
            'You have created a new account on Chief Firewall Admin.\n'
            'You could login and change it on Chief Firewall Admin later.\n'
            '\n'
            f'Your account: {username}\n'
            f'Your password: {random_uuid_password}\n'
            '\n'
            'Sincerely,\n'
            'Chief Firewall Admin\n'
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Extend AuthenticationForm and disable the autofocus on field username.
    """
    username = UsernameField(widget=forms.TextInput())


class ProfileForm(forms.ModelForm):

    email = forms.EmailField(
        label=_('Email'),
        required=False,
        max_length=63,
        widget=forms.EmailInput(
            attrs={
                'placeholder': _('Email'),
            }
        ),
        help_text=_('Email cannot be changed after setting.'),
    )

    phone_number = forms.CharField(
        label=_('Phone number'),
        max_length=32,
        required=False,
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.email:
            self.fields['email'].disabled = True
        self.fields['phone_number'].initial = self.instance.profile.phone_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.profile.phone_number = self.cleaned_data['phone_number']
        if commit:
            instance.save()
        return instance


class EmailValidationOnForgotPasswordForm(PasswordResetForm):

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            self.add_error(
                'email',
                ValidationError(
                    _('No user registering with this Email.'),
                    code='invalid'
                )
            )
        return email