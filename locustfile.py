from locust import HttpUser, task, between
import random
import string

class UserServiceLoadTest(HttpUser):
    wait_time = between(1, 3)  # Attesa tra richieste
    host = "https://localhost:443"  # API Gateway Admin
    base_path = "/admin/user"  # Path base configurato in Nginx per user_service

    def on_start(self):
        """Simula l'inizializzazione dell'utente: registrazione e login."""
        self.username = self.random_string(8)
        self.password = "Str0ngP@ssw0rd!"  # Password forte predefinita
        self.token = None
        if not self.signup():
            print("Registrazione fallita. Interrompo il test.")
            return
        if not self.login():
            print("Login fallito. Interrompo il test.")
            return

    @staticmethod
    def random_string(length):
        """Genera una stringa casuale."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def signup(self):
        """Esegue la registrazione di un nuovo utente."""
        response = self.client.post(f"{self.base_path}/signup", json={
            "username": self.username,
            "psw": self.password
        }, verify=False)
        print(f"Signup Response: {response.status_code} - {response.text}")
        return response.status_code == 201

    def login(self):
        """Esegue il login e salva il token JWT."""
        response = self.client.post(f"{self.base_path}/login", json={
            "username": self.username,
            "psw": self.password
        }, verify=False)
        print(f"Login Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            self.token = response.json().get("token")
            return True
        return False

    @task(1)
    def test_get_users(self):
        """Testa l'endpoint per ottenere tutti gli utenti (solo admin)."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(f"{self.base_path}/list", headers=headers, verify=False)
            print(f"GET /list Response: {response.status_code} - {response.text}")

    @task(2)
    def test_logout(self):
        """Testa il logout dell'utente."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(f"{self.base_path}/logout", headers=headers, verify=False)
            print(f"POST /logout Response: {response.status_code} - {response.text}")
