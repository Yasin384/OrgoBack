import requests

BASE_URL = "https://orgoback-production.up.railway.app/api"

def login(username, password):
    """
    Logs in and retrieves the authentication token.
    """
    url = f"{BASE_URL}/login/"
    data = {"username": username, "password": password}

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        token = response.json().get("token")
        if token:
            print(f"Login successful. Token: {token}")
            return token
        else:
            print("Login failed: No token returned.")
    except requests.RequestException as e:
        print(f"Login failed: {e}")
    return None

def get_schedules(token):
    """
    Fetches the schedules using the provided authentication token.
    """
    url = f"{BASE_URL}/schedules/"
    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            print("No schedules available.")
        else:
            print(f"Schedules fetched successfully: {results}")
        return results
    except requests.RequestException as e:
        print(f"Failed to fetch schedules: {e}")
    return None

if __name__ == "__main__":
    # Credentials
    username = "yasin"
    password = "yasinatay"

    # Login and fetch token
    token = login(username, password)

    # Fetch schedules if login was successful
    if token:
        schedules = get_schedules(token)
        if schedules:
            print("\n--- Schedules ---")
            for schedule in schedules:
                print(f"Subject: {schedule['subject']['name']}, Teacher: {schedule['teacher']['username']}, "
                      f"Class: {schedule['class_obj']['name']}, Time: {schedule['start_time']} - {schedule['end_time']}")
