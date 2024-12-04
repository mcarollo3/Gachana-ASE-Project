import requests


def make_request(url, method="GET", data=None, headers=None, cert=None, timeout=(2, 5)):
    try:
        response = requests.request(
            method,
            url,
            json=data,
            headers=headers,
            cert=cert,
            verify=False,
            timeout=timeout,
        )
        response.raise_for_status()  # Solleva eccezioni solo per 4xx/5xx
    except requests.exceptions.HTTPError as e:
        # Restituisci comunque la risposta per catturare i dettagli
        return e.response
    except requests.exceptions.Timeout:
        raise Exception("Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")
    return response
