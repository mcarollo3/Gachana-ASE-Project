from locust import HttpUser, task, between
from collections import Counter
import json

class GachaPlayerLoadTest(HttpUser):
    wait_time = between(1, 3)  # Tempo di attesa casuale tra richieste
    host = "https://localhost:444"  # API Gateway Player
    base_path = "/player/gacha"  # Path base per le operazioni di gacha
    login_path = "/player/user/login"  # Path per il login

    # Contatore per tracciare la distribuzione delle rarità
    rarity_distribution = Counter()
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJyb2xlIjoiUGxheWVyIiwiZXhwIjoxNzMzNDE4MTAyfQ.sOZIo8Dbyx-a1nhgfeNegyJCp6vEB3mNRSbg1gYgdMA"
    

    def on_start(self):
        """Esegui il login per generare un token JWT valido."""
        self.username = "player"  # Cambia con un utente valido
        self.password = "prova"   # Cambia con una password valida
        self.login()

    #def login(self):
     #   """Effettua il login per ottenere un token JWT."""
      #  response = self.client.post(
       #     self.login_path,
        #    json={"username": self.username, "psw": self.password},
        #    verify=False
        #)
        #if response.status_code == 200:
        #    self.token = response.json().get("token")
        #    print(f"Login riuscito. Token ottenuto: {self.token}")
        #else:
        #    print(f"Errore durante il login: {response.status_code} - {response.text}")

    @task(1)
    def gacha_info(self):
        """Testa l'endpoint di informazioni del gacha."""   


    @task(3)
    def gacha_roll(self):
        """Testa l'endpoint di roll del gacha."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(f"{self.base_path}/roll", headers=headers, verify=False)

            if response.status_code == 200:
                # Estrai la rarità dalla risposta JSON
                rarity = response.json().get("rarity", "unknown")
                self.rarity_distribution[rarity] += 1
                print(f"Rarity: {rarity}")
            else:
                print(f"Gacha roll failed: {response.status_code} - {response.text}")

    @task(1)
    def gacha_inventory(self):
        """Testa l'endpoint per visualizzare l'inventario del giocatore."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(f"{self.base_path}/inventory", headers=headers, verify=False)

            if response.status_code == 200:
                print(f"Inventory: {response.json()}")
            else:
                print(f"Failed to retrieve inventory: {response.status_code} - {response.text}")

    def on_stop(self):
        """Mostra la distribuzione delle rarità al termine del test."""
        print("\nFinal Gacha Rarity Distribution:")
        print(json.dumps(self.rarity_distribution, indent=4))
