import time
import subprocess
import requests
from playwright.sync_api import sync_playwright


def start_server():
    # start uvicorn in background
    p = subprocess.Popen(['uvicorn', 'src.app:app', '--host', '127.0.0.1', '--port', '8000'])
    time.sleep(2)
    return p


def stop_server(p):
    p.terminate()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()


def test_ui_homepage_and_buttons():
    p = start_server()
    try:
        # ensure server up
        r = requests.get('http://127.0.0.1:8000/')
        assert r.status_code == 200

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto('http://127.0.0.1:8000/')
            # click forecast
            page.click('#btnForecast')
            page.wait_for_selector('#forecastArea')
            assert 'no data' not in page.inner_text('#forecastArea').lower()
            # click anomalies
            page.click('#btnAnomalies')
            page.wait_for_selector('#anomalyArea')
            # click recommend
            page.click('#btnRecommend')
            page.wait_for_selector('#recommendArea')
            browser.close()
    finally:
        stop_server(p)
