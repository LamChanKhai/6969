import zipfile
import io
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from gateway.utils import check_file, transport_file, health_check

User = get_user_model()


def create_valid_zip(extensions=None):
    """Create a valid ZIP in memory with given file extensions."""
    if extensions is None:
        extensions = [".txt", ".png"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for ext in extensions:
            zf.writestr(f"file{ext}", f"sample content for {ext}")
    buf.seek(0)
    return buf


class CheckFileTestCase(TestCase):
    """Tests for the check_file utility function."""

    def test_valid_zip_with_allowed_extensions(self):
        buf = create_valid_zip([".txt", ".png", ".jpg"])
        self.assertTrue(check_file(buf))

    def test_valid_zip_with_single_allowed_extension(self):
        buf = create_valid_zip([".docx"])
        self.assertTrue(check_file(buf))

    def test_invalid_zip_with_disallowed_extension(self):
        buf = create_valid_zip([".txt", ".exe"])
        self.assertFalse(check_file(buf))

    def test_non_zip_file_returns_false(self):
        buf = io.BytesIO(b"this is not a zip file")
        self.assertFalse(check_file(buf))

    def test_empty_zip_returns_false(self):
        buf = io.BytesIO()
        self.assertFalse(check_file(buf))

    def test_all_allowed_extensions_pass(self):
        allowed = [".txt", ".docx", ".png", ".jpg", ".jpeg"]
        buf = create_valid_zip(allowed)
        self.assertTrue(check_file(buf))


class HealthCheckTestCase(TestCase):
    """Tests for the health_check utility function."""

    @patch("gateway.utils.requests.get")
    def test_health_check_returns_true_on_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        self.assertTrue(health_check("/health.php"))

    @patch("gateway.utils.requests.get")
    def test_health_check_returns_false_on_500(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        self.assertFalse(health_check("/health.php"))

    @patch("gateway.utils.requests.get")
    def test_health_check_returns_false_on_exception(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        self.assertFalse(health_check("/health.php"))


class TransportFileTestCase(TestCase):
    """Tests for the transport_file utility function."""

    @patch("gateway.utils.requests.post")
    def test_transport_returns_ok_on_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        buf = create_valid_zip([".txt"])
        result = transport_file("test-user-id", buf)
        self.assertEqual(result, "OK")

    @patch("gateway.utils.requests.post")
    def test_transport_returns_err_on_exception(self, mock_post):
        mock_post.side_effect = Exception("Timeout")
        buf = create_valid_zip([".txt"])
        result = transport_file("test-user-id", buf)
        self.assertEqual(result, "ERR")

    @patch("gateway.utils.requests.post")
    def test_transport_sends_correct_id(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        buf = create_valid_zip([".txt"])
        transport_file("abc-123-uuid", buf)
        call_kwargs = mock_post.call_args[1]
        files = call_kwargs["files"]
        file_keys = list(files.keys())
        self.assertIn("id", file_keys)

    @patch("gateway.utils.requests.post")
    def test_transport_sends_file(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        buf = create_valid_zip([".txt"])
        transport_file("abc-123-uuid", buf)
        call_kwargs = mock_post.call_args[1]
        files = call_kwargs["files"]
        self.assertIn("file", files)


class UserRegistrationAPITestCase(TestCase):
    """Tests for user registration endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_create_new_user(self):
        response = self.client.post(
            "/gateway/user/",
            data={
                "username": "newuser",
                "email": "newuser@test.local",
                "password": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "newuser")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_update_existing_user_returns_400_due_to_uniqueness_validator(self):
        User.objects.create_user(
            username="existing",
            email="existing@test.local",
            password="OldPass123!",
        )
        response = self.client.post(
            "/gateway/user/",
            data={
                "username": "existing",
                "email": "existing@test.local",
                "password": "NewPass456!",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_missing_password_fails(self):
        response = self.client.post(
            "/gateway/user/",
            data={"username": "nouser", "email": "nouser@test.local"},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_missing_username_fails(self):
        response = self.client.post(
            "/gateway/user/",
            data={"email": "nouser@test.local", "password": "Pass123!"},
        )
        self.assertEqual(response.status_code, 400)


class AuthTokenAPITestCase(TestCase):
    """Tests for JWT token endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tokenuser",
            email="tokenuser@test.local",
            password="TokenPass123!",
        )

    def test_obtain_token_success(self):
        response = self.client.post(
            "/auth/token/",
            data={"username": "tokenuser", "password": "TokenPass123!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_wrong_password(self):
        response = self.client.post(
            "/auth/token/",
            data={"username": "tokenuser", "password": "WrongPassword"},
        )
        self.assertEqual(response.status_code, 401)

    def test_obtain_token_nonexistent_user(self):
        response = self.client.post(
            "/auth/token/",
            data={"username": "ghost", "password": "Pass123!"},
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            "/auth/refresh-token/",
            data={"refresh": str(refresh)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)


class HealthEndpointAPITestCase(TestCase):
    """Tests for the health check endpoint."""

    def setUp(self):
        self.client = APIClient()

    @patch("gateway.utils.requests.get")
    def test_health_returns_ok_on_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code= 200)
        response = self.client.get("/gateway/health/?module=/health.php")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "OK")

    @patch("gateway.utils.requests.get")
    def test_health_returns_err_on_failure(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        response = self.client.get("/gateway/health/?module=/health.php")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ERR")

    def test_health_no_auth_required(self):
        response = self.client.get("/gateway/health/")
        self.assertEqual(response.status_code, 200)


class FileTransportAPITestCase(TestCase):
    """Tests for the file transport endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="transportuser",
            email="transport@test.local",
            password="TransportPass123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def _upload_file(self, extensions=None):
        buf = create_valid_zip(extensions)
        from django.core.files.uploadedfile import SimpleUploadedFile
        zip_file = SimpleUploadedFile("test.zip", buf.read(), content_type="application/zip")
        response = self.client.post(
            "/gateway/transport/",
            data={"file": zip_file},
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        return response

    @patch("gateway.utils.requests.post")
    def test_upload_valid_file_returns_ok(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        response = self._upload_file([".txt", ".png"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "OK")

    def test_upload_invalid_file_rejected(self):
        response = self._upload_file([".txt", ".exe"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Invalid file")

    def test_upload_requires_auth(self):
        buf = create_valid_zip([".txt"])
        from django.core.files.uploadedfile import SimpleUploadedFile
        zip_file = SimpleUploadedFile("test.zip", buf.read(), content_type="application/zip")
        response = self.client.post(
            "/gateway/transport/",
            data={"file": zip_file},
            format="multipart",
        )
        self.assertIn(response.status_code, [401, 403])


class UserFindAPITestCase(TestCase):
    """Tests for the user search endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="finduser",
            email="finduser@test.local",
            password="FindPass123!",
        )
        User.objects.create_user(
            username="other_user",
            email="other@test.local",
            password="OtherPass123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_find_by_username(self):
        response = self.client.post(
            "/gateway/user/find/?offset=0",
            data={"username": "finduser"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "finduser")

    def test_find_by_email(self):
        response = self.client.post(
            "/gateway/user/find/?offset=0",
            data={"email": "other@test.local"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_find_returns_empty_when_no_match(self):
        response = self.client.post(
            "/gateway/user/find/?offset=0",
            data={"username": "nonexistent"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_find_requires_auth(self):
        response = self.client.post(
            "/gateway/user/find/",
            data={"username": "finduser"},
            content_type="application/json",
        )
        self.assertIn(response.status_code, [401, 403])

    def test_find_pagination_offset(self):
        response = self.client.post(
            "/gateway/user/find/?offset=10",
            data={"username": ""},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_find_invalid_offset_defaults_to_zero(self):
        response = self.client.post(
            "/gateway/user/find/?offset=abc",
            data={"username": ""},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)
