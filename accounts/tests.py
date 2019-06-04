# This file is covered by the BSD license. See LICENSE in the root directory.
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

User = get_user_model()
USERNAME = 'testuser'
PASSWORD = '28&}>z1-%ZY|0ATwGU+7I!F7pJ:+(E'
FIRSTNAME = 'first'
LASTNAME = 'last'
EMAIL = 'mail@example.com'
DESCRIPTION = 'description'
INSTITUTION = 'institution'
WEBSITE = 'http://example.com'


class UserCreationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create(
            username='superuser', email=EMAIL, is_superuser=True)
        Group.objects.create(name='users')

    def test_success(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': USERNAME,
            'email': EMAIL,
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertFalse(User.objects.last().is_active)
        self.assertContains(response, 'Confirmation email has been sent.')
        for line in mail.outbox[0].body.splitlines():
            line_stripped = line.lstrip()
            if line_stripped.startswith('http'):
                activation_url = line_stripped
                break
        response = self.client.get(activation_url, follow=True)
        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertContains(response, 'Account confirmed.')
        self.assertTrue(User.objects.last().is_active)
        self.assertFalse(User.objects.last().is_staff)
        self.assertEqual(len(mail.outbox), 2)

    def test_no_email_or_username(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': USERNAME, 'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertContains(response, 'This field is required')
        response = self.client.post(reverse('accounts:register'), {
            'email': EMAIL, 'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertContains(response, 'This field is required')
        self.assertEqual(User.objects.count(), 1)

    def test_incorrect_activation(self):
        uid = 'MMM'
        token = '00a-'+20*'0'
        response = self.client.get(
            reverse('accounts:activate', kwargs={'uid': uid, 'token': token}),
            follow=True)
        self.assertContains(response, 'Activation link is invalid!')

    def test_user_profile(self):
        user = User.objects.create(username=USERNAME, email=EMAIL)
        user.set_password(PASSWORD)
        user.save()
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.client.force_login(user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': FIRSTNAME,
            'last_name': LASTNAME,
            'email': EMAIL,
            'description': DESCRIPTION,
            'institution': INSTITUTION,
            'website': WEBSITE,
        }, follow=True)
        user = User.objects.last()
        self.assertEqual(user.first_name, FIRSTNAME)
        self.assertEqual(user.last_name, LASTNAME)
        self.assertEqual(user.userprofile.description, DESCRIPTION)
        self.assertEqual(user.userprofile.institution, INSTITUTION)
        self.assertEqual(user.userprofile.website, WEBSITE)

    def test_change_password(self):
        response = self.client.post(reverse('accounts:change_password'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        user = User.objects.first()
        user.set_password(PASSWORD)
        user.save()
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:change_password'),
                                    {'old_password': PASSWORD})
        self.assertContains(response,
                            'Incorrect password or new passwords not matching')
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': PASSWORD,
            'new_password1': PASSWORD,
            'new_password2': PASSWORD,
        }, follow=True)
        self.assertNotContains(
            response, 'Incorrect password or new passwords not matching')
        self.assertContains(response, 'Password successfully changed')


class TemplateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create(
            username='superuser', email=EMAIL, is_superuser=True)
        cls.user = User.objects.create(
            username=USERNAME, is_active=True)

    def test_buttons(self):
        response = self.client.get('')
        self.assertContains(response, 'Register')
        self.client.force_login(self.user)
        response = self.client.get('')
        self.assertContains(response, 'Profile')
        self.assertNotContains(response, 'Add Data')
        self.user.is_staff = True
        self.user.save()
        response = self.client.get('')
        self.assertContains(response, 'Add Data')


class AnonymousUserTestCase(TestCase):
    def test_load_pages(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
