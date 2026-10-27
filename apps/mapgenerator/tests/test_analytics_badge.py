import pytest
from apps.mapgenerator.app import app

# Simple Analytics free plan requires a visible badge on every page
PAGES = ["/", "/credits/", "/history/", "/dom5/arena-mapgen/", "/dom6/arena-mapgen/"]


@pytest.mark.parametrize("path", PAGES)
def test_simple_analytics_badge_is_rendered(path):
    request, response = app.test_client.get(path)
    assert response.status == 200
    assert response.text.count('id="sa-badge"') == 1
    assert "Privacy-friendly analytics by Simple Analytics" in response.text
    assert "https://www.simpleanalytics.com/" in response.text
