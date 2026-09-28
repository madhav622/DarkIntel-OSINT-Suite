import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_onion_page(target_url):
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url

    # socks5h is mandatory for Tor remote DNS resolution
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'
    }

    # Attempt 1: Tor Route with Retry
    for attempt in range(2):
        try:
            response = requests.get(
                target_url,
                headers=headers,
                proxies=proxies,
                timeout=25,
                verify=False
            )
            if response.status_code == 200:
                return response.text
        except Exception:
            time.sleep(2)

    # Attempt 2: Clearweb Direct Fallback (For HTTP/HTTPS links)
    try:
        response = requests.get(
            target_url,
            headers=headers,
            timeout=15,
            verify=False
        )
        if response.status_code == 200:
            return response.text
    except Exception:
        pass

    return None
