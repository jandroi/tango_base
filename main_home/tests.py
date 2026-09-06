from django.test import TestCase, Client
from django.urls import reverse
from main_users.models import MainUser

class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_returns_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_home/home.html')

    def test_what_we_do_returns_200(self):
        response = self.client.get(reverse('what_we_do'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_home/what_we_do.html')

    def test_how_it_works_returns_200(self):
        response = self.client.get(reverse('how_it_works'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_home/how_it_works.html')

    def test_about_returns_200(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_home/about.html')

    def test_contact_returns_200(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_home/contact.html')

    def test_public_pages_include_social_preview_metadata(self):
        preview_url = 'https://www.tangodatalabs.com/static/main_home/img/social_preview.jpg'

        for page_name in ('home', 'what_we_do', 'how_it_works', 'about', 'contact'):
            with self.subTest(page_name=page_name):
                response = self.client.get(reverse(page_name))
                self.assertContains(response, f'<meta property="og:image" content="{preview_url}">')
                self.assertContains(response, '<meta property="og:image:type" content="image/jpeg">')
                self.assertContains(response, '<meta property="og:image:width" content="1200">')
                self.assertContains(response, '<meta property="og:image:height" content="630">')

    def test_home_authenticated_nav_shows_main_not_dashboard(self):
        user = MainUser.objects.create_user(email='nav@example.com', password='TestPass123!')
        self.client.login(username='nav@example.com', password='TestPass123!')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Main')
        self.assertNotContains(response, 'Dashboard')

class DistributorViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('main_distributor')
        self.user = MainUser.objects.create_user(email='dist@example.com', password='TestPass123!')

    def test_main_distributor_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_main_distributor_returns_200_for_authenticated_user(self):
        self.client.login(username='dist@example.com', password='TestPass123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_main_distributor_uses_expected_template(self):
        self.client.login(username='dist@example.com', password='TestPass123!')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'main_home/distributor.html')

    def test_base_logo_authenticated_points_to_main_distributor(self):
        self.client.login(username='dist@example.com', password='TestPass123!')
        response = self.client.get(self.url)
        self.assertContains(response, reverse('main_distributor'))

    def test_dashboard_redirect_points_to_main(self):
        self.client.login(username='dist@example.com', password='TestPass123!')
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, self.url)

# ===========================================================================
# Navigation path integration tests (Section A)
# ===========================================================================

class NavigationPathTests(TestCase):
    """End-to-end navigation path: Login -> Main."""

    def setUp(self):
        self.client = Client()
        self.user = MainUser.objects.create_user(
            email='navpath@example.com',
            password='TestPass123!',
            is_staff=True,
        )

    def test_login_redirects_to_main(self):
        response = self.client.post(reverse('login'), {
            'username': 'navpath@example.com',
            'password': 'TestPass123!',
        })
        self.assertRedirects(response, '/main/', fetch_redirect_response=False)

