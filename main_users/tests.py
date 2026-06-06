from django.test import TestCase, Client
from django.urls import reverse
from main_users.models import MainUser


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_register_page_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_users/register.html')

    def test_register_valid_user(self):
        data = {
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(MainUser.objects.filter(email='newuser@example.com').exists())

    def test_register_password_mismatch(self):
        data = {
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'WrongPass456!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MainUser.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        MainUser.objects.create_user(email='existing@example.com', password='TestPass123!')
        data = {
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MainUser.objects.filter(email='existing@example.com').count(), 1)


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = MainUser.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
        )

    def test_login_page_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_users/login.html')

    def test_login_valid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_success_redirects_to_main(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        self.assertRedirects(response, '/main/', fetch_redirect_response=False)

    def test_guarded_page_redirects_to_login_then_back(self):
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)
        self.assertIn('next=/main/', response.url)

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = MainUser.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
        )
        self.client.login(username='testuser@example.com', password='TestPass123!')

    def test_logout_redirects(self):
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = MainUser.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
        )
        self.profile_url = reverse('profile')

    def test_profile_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_profile_page_authenticated(self):
        self.client.login(username='testuser@example.com', password='TestPass123!')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_users/profile.html')

    def test_profile_update(self):
        self.client.login(username='testuser@example.com', password='TestPass123!')
        response = self.client.post(self.profile_url, {
            'email': 'testuser@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
            'country': 'Mexico',
            'language': 'Spanish',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.country, 'Mexico')
