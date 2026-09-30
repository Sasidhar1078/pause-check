import unittest

from app import inspect_url


class InspectUrlTests(unittest.TestCase):
    def test_https_address_has_no_basic_warning_signs(self):
        self.assertEqual(inspect_url("https://example.com")["warning_signs"], [])

    def test_http_address_is_flagged(self):
        warnings = inspect_url("http://example.com")["warning_signs"]
        self.assertTrue(any("HTTPS" in warning for warning in warnings))

    def test_shortened_address_is_flagged(self):
        warnings = inspect_url("bit.ly/check-this")["warning_signs"]
        self.assertTrue(any("shortened-link" in warning for warning in warnings))

    def test_credentials_in_address_are_flagged(self):
        warnings = inspect_url("https://user:password@example.com")["warning_signs"]
        self.assertTrue(any("sign-in details" in warning for warning in warnings))

    def test_encoded_lookalike_domain_is_flagged(self):
        warnings = inspect_url("https://аррӏе.com")["warning_signs"]
        self.assertTrue(any("encoded characters" in warning for warning in warnings))

    def test_non_web_protocol_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_url("javascript:alert(1)")

    def test_whitespace_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_url("not a website")


if __name__ == "__main__":
    unittest.main()
