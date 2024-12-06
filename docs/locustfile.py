from locust import HttpUser, task, between
from collections import Counter
import json

class GachaPlayerLoadTest(HttpUser):
    wait_time = between(2, 10)  # Tempo di attesa casuale tra richieste
    host = "https://localhost:444"  # API Gateway Player
    base_path = "/player/gacha"  # Path base per le operazioni di gacha
    login_path = "/player/user/login"  # Endpoint di login per ottenere il token

    # Contatore per tracciare la distribuzione delle rarità
    rarity_distribution = Counter()
    token = None

    def on_start(self):
        """Effettua il login per ottenere un token JWT."""
        self.username = "player"  # Nome utente
        self.password = "prova"
        self.login()

    def login(self):
        """Effettua il login per ottenere un token JWT."""
        response = self.client.post(
            self.login_path,
            json={"username": self.username, "psw": self.password},
            verify=False
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
            print(f"Login riuscito. Token ottenuto: {self.token}")
        else:
            print(f"Errore durante il login: {response.status_code} - {response.text}")

    @task(3)
    def gacha_roll(self):
        """Testa l'endpoint di roll del gacha."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(f"{self.base_path}/roll", headers=headers, verify=False)

            if response.status_code == 200:
                gacha_info = response.json().get("gacha_info")
                # Estrai la rarità dalla risposta JSON
                rarity = gacha_info.get("rarity")
                self.rarity_distribution[rarity] += 1
                print(f"Rarity: {rarity}")
            else:
                print(f"Gacha roll failed: {response.status_code} - {response.text}")

    @task(2)
    def get_gacha_collection(self):
        """Testa l'endpoint per ottenere la collezione di gacha del giocatore."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(f"{self.base_path}/collection", headers=headers, verify=False)
            if response.status_code == 200:
                collection = response.json()
                for gacha in collection:
                    print(f"Gacha Collezione - Name: {gacha['name']}, Rarity: {gacha['rarity']}")
            else:
                print(f"Errore: {response.status_code} - {response.text}")

    @task(2)
    def get_available_gachas(self):
        """Testa l'endpoint per ottenere i gacha disponibili."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(f"{self.base_path}/collection/available", headers=headers, verify=False)
            if response.status_code == 200:
                available = response.json()
                for gacha in available:
                    print(f"Gacha Disponibili - Name: {gacha['name']}, Rarity: {gacha['rarity']}")
            else:
                print(f"Errore: {response.status_code} - {response.text}")

    @task(1)
    def get_user_gacha(self):
        """Testa l'endpoint per ottenere un singolo gacha casuale dalla collezione."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(f"{self.base_path}/collection/available/1", headers=headers, verify=False)
            if response.status_code == 200:
                gacha_info = response.json()
                print(f"Gacha Info - Name: {gacha_info['name']}, Description: {gacha_info['description']}, Rarity: {gacha_info['rarity']}")
            else:
                print(f"Errore nel recuperare il gacha: {response.status_code} - {response.text}")

    def on_stop(self):
        """Mostra la distribuzione delle rarità al termine del test."""
        print("\nDistribuzione Finale delle Rarità:")
        print(json.dumps(self.rarity_distribution, indent=4))
