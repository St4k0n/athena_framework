import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import requests

# Fonctions utilisées dans les exemples
def process_item(item):
    time.sleep(0.2)  # Simule un traitement
    return f"Résultat de {item}"

def download_file(file_size):
    chunk_size = 1024
    for _ in tqdm(range(0, file_size, chunk_size), desc="Téléchargement", unit="ko"):
        time.sleep(0.1)

def process_data(index):
    time.sleep(0.5)  # Simule une tâche lente
    return f"Tâche {index} terminée"

class MyIterator:
    def __init__(self, n):
        self.n = n
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.n:
            time.sleep(0.1)
            self.current += 1
            return self.current
        else:
            raise StopIteration

# Menu des exemples
def main():
    print("Choisissez un exemple à exécuter :")
    print("1 - Barre simple")
    print("2 - Barre avec une liste")
    print("3 - Barre avec une fonction")
    print("4 - Téléchargement simulé")
    print("5 - Multithreading avec barre")
    print("6 - Barre pour fichiers")
    print("7 - Barre personnalisée")
    print("8 - Barre pour téléchargements (requests)")
    print("9 - Barres multiples")
    print("10 - Progression avec pandas")
    print("11 - Itérateur personnalisé")

    choix = int(input("Entrez le numéro de l'exemple : "))

    if choix == 1:
        for i in tqdm(range(100), desc="Traitement en cours"):
            time.sleep(0.1)

    elif choix == 2:
        data = ["tâche 1", "tâche 2", "tâche 3", "tâche 4"]
        for item in tqdm(data, desc="Chargement des tâches"):
            print(f"Traitement de {item}")
            time.sleep(0.5)

    elif choix == 3:
        data = ["a", "b", "c", "d"]
        results = [process_item(item) for item in tqdm(data, desc="Traitement des données")]
        print(results)

    elif choix == 4:
        download_file(10 * 1024)  # Simule un fichier de 10 Mo

    elif choix == 5:
        data = range(20)
        with ThreadPoolExecutor() as executor:
            results = list(tqdm(executor.map(process_data, data), total=len(data), desc="Multithreading"))
        print(results)

    elif choix == 6:
        print("Cet exemple nécessite des fichiers source et destination (à personnaliser).")
        # Exemple à adapter si besoin :
        # source_file = "source.txt"
        # destination_file = "destination.txt"

    elif choix == 7:
        for i in tqdm(range(100), desc="Travail", ncols=80, ascii=" >=", colour="cyan"):
            time.sleep(0.1)

    elif choix == 8:
        url = "https://example.com/largefile.zip"
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open("largefile.zip", "wb") as file, tqdm(
            desc="Téléchargement",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                bar.update(len(data))

    elif choix == 9:
        tasks = ["tâche 1", "tâche 2", "tâche 3"]
        progress_bars = [tqdm(total=100, desc=task) for task in tasks]

        for _ in range(100):
            for bar in progress_bars:
                bar.update(1)
                time.sleep(0.01)

        for bar in progress_bars:
            bar.close()

    elif choix == 10:
        tqdm.pandas(desc="Traitement du DataFrame")
        df = pd.DataFrame({'col1': range(100)})
        df['col2'] = df['col1'].progress_apply(lambda x: x ** 2)
        print(df)

    elif choix == 11:
        for value in tqdm(MyIterator(50), desc="Itérateur personnalisé"):
            pass

    else:
        print("Numéro invalide. Réessayez.")

if __name__ == "__main__":
    main()
