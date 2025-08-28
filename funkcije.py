import pandas as pd
from bs4 import BeautifulSoup
import requests

def pridobi_delnice(link):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(link, headers= headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    tabela = soup.find("table")
    if not tabela:
        print("Tabela ni najdena")
        return []
    vrstice = tabela.find_all("tr")
    
    delnice = []
    videne_delnice = set()
    for vrstica in vrstice[1:]:
        if len(delnice) >= 20 :
            break
        komponente = vrstica.find_all("td")
        if len(komponente) >= 7:
            simbol = komponente[1].text.strip()
            ime = komponente[2].text.strip()
            if ime in videne_delnice:
                continue
            videne_delnice.add(ime)
            cena = komponente[4].text.strip().replace(",", "")
            volumen = komponente[3].text.strip()
            dnevna_sprem = komponente[5].text.strip()
            dobiček = komponente[6].text.strip()
            pripona = komponente[1].find("a", href = True)
            if pripona and pripona.has_attr('href'):
                link_del = "https://stockanalysis.com" + pripona["href"]
            else:
                link_del = ""  # Varnostna možnost
            delnice.append([ime, simbol, cena, dnevna_sprem,dobiček, volumen, link_del])

    df =pd.DataFrame(delnice, columns=["Ime", "Simbol","Trenutna_cena", "Dnevna_sprem.", 
                                       "Dobiček", "Volumen_delnice", "Link_za_več"])
    df["Trenutna_cena"] = pd.to_numeric(df["Trenutna_cena"], errors= "coerce")
    return df

def pridobivanje_dod_info(link):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(link, headers = headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    tabele = soup.find_all("table")
    kljuci = ["PE Ratio", "Dividend", "Volume", "52-Week Range", "Beta", "Earnings Date"] #Mislim lahko dodaš še kaj, jaz hočem samo to
    podatki = {}

    for tabela in tabele:
        vrstice = tabela.find_all("tr")
        for vrstica in vrstice:
            stolpci = vrstica.find_all("td")
            if len(stolpci) == 2:
                ime = stolpci[0].text.strip()
                vred = stolpci[1].text.strip()
                if ime in kljuci:
                    podatki[ime] = vred

    for k in kljuci:
        if k not in podatki:
            podatki[k] = "Ne najdemo"
    return podatki






