from locust import HttpUser, task, between
from collections import Counter
import json

#il numero corrisponde alla priorita del task
#genera prima il token poi salva e procedi con locust -f locustfile.py

class GachaPlayerLoadTest(HttpUser):
    wait_time = between(2, 10)  # Tempo di attesa casuale tra richieste
    host = "https://localhost:444"  # API Gateway Player
    base_path = "/player/gacha"  # Path base per le operazioni di gacha

    # 
    #utilizzando un Counter per tracciare la distribuzione delle rarità dei gacha roll.
    rarity_distribution = Counter()
    token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJyb2xlIjoiUGxheWVyIiwiZXhwIjoxNzMzNDM3ODUxfQ.TRHQrVmwaeMjDQ3LuN7Isno7IYjlIQgYl13bUDmOh_8"


    #metodo gacha roll
    @task(3) 
    def gacha_roll(self):
        """Testa l'endpoint di roll del gacha."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(f"{self.base_path}/roll", headers=headers, verify=False)

            if response.status_code == 200:
                gacha_info=response.json().get("gacha_info")
                # Estrai la rarità dalla risposta JSON
                rarity = gacha_info.get("rarity")
                self.rarity_distribution[rarity] += 1
                print(f"Rarity: {rarity}")
            else:
                print(f"Gacha roll failed: {response.status_code} - {response.text}")

    
    #Metodo get_gacha_collection
    @task(2)
    def get_gacha_collection(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(f"{self.base_path}/collection", headers=headers, verify=False)
        if response.status_code == 200:
            print(f"Collezione recuperata: {response.json()}")
        else:
            print(f"Errore: {response.status_code} - {response.text}")

    #get_available_gachas
    @task(1)
    def get_available_gachas(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(f"{self.base_path}/collection/available", headers=headers, verify=False)
        if response.status_code == 200:
            print(f"Gacha disponibili: {response.json()}")
        else:
            print(f"Errore: {response.status_code} - {response.text}")

    @task(1)
    def get_user_gacha(self):
        """Testa l'endpoint per ottenere un singolo gacha casuale dalla collezione."""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(f"{self.base_path}/collection/available/1", headers=headers, verify=False)
        if response.status_code == 200:
            gacha_info = response.json()
            print(f"Gacha Info - Name: {gacha_info['name']}, Description: {gacha_info['description']}, Rarity: {gacha_info['rarity']}")
        else:
            print(f"Errore nel recuperare il gacha: {response.status_code} - {response.text}")