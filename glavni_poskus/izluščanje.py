from bs4 import BeautifulSoup
import requests
import pandas as pd
import funkcije
import time

def prid_podatkov_analysis():
    url = "https://stockanalysis.com/list/exchanges/"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    
    tabela = soup.find("table")  
    vrstice = tabela.find_all("tr")
    baza = "https://stockanalysis.com"
    podatki = []
    videne_drzave = set()
    for vrstica in vrstice[2:]: # Ni mi bilo všeč, da so tuje delnice zastopale ZDA, torej 2:
        komponenti = vrstica.find_all("td")
        if len(komponenti) >=5 :
            drzava = komponenti[1].text.strip()
            if drzava in videne_drzave:
                continue
            videne_drzave.add(drzava)

            ime= komponenti[0].text.strip()
            borza = komponenti[2].text.strip()
            valuta = komponenti[3].text.strip()
            št_delnic = komponenti[4].text.strip()

            pripona = vrstica.find("a", href = True)
            link = baza + pripona["href"]
            podatki.append([ime, drzava, borza, valuta, št_delnic, link])
    
    df = pd.DataFrame(podatki, columns=["Ime","Drzava", "Borza", "Valuta", "st_delnic", "Link_iz_stock_analysis"])
    return df

def prid_podatkov_tradecon():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get("https://tradingeconomics.com/stocks", headers = headers)
    soup = BeautifulSoup(r.content, "html.parser")
    baza = "https://tradingeconomics.com"
    tabele = soup.find_all("table")
    rez = []
    videne_drzave = set()

    for tabela in tabele:
        vrstice = tabela.find_all("tr")
        if len(vrstice) <= 1:
            continue
        for vrstica in vrstice[1:]:
            komponente = vrstica.find_all("td")

            if len(komponente) < 6:
                    continue
            predpona = komponente[1].find("a", href = True)
            drzava = predpona["href"].split("/")[1]
            drzava = drzava.replace("-", " ").title()
            if drzava in videne_drzave:
                continue
            videne_drzave.add(drzava)
            
            link = baza + predpona["href"]
            cena = komponente[2].text.strip().replace(",", "")
            Mesecna = komponente[-5].text.strip()
            Letna = komponente[-4].text.strip()
            datum_td = vrstica.find("td", id = "date")
            datum = datum_td.text.strip() if datum_td else ""
            rez.append([link, drzava, cena, Mesecna, Letna, datum])

    df = pd.DataFrame(rez, columns=["Link_iz_econ", "Drzava", "Cena", "Mesečna sprem.", "Letna sprem.", "Čas prid. podatkov"])
    df["Cena"] = pd.to_numeric(df["Cena"], errors= "coerce")
    return df


def združitev_obeh():
    df_sa = prid_podatkov_analysis()
    df_tr = prid_podatkov_tradecon()
    df_zdruzen = pd.merge(df_sa, df_tr, on='Drzava', how='inner')
    
    željeni_stolpci = [
        'Ime', 'Drzava', 'Borza', 'Valuta', 'Cena', 
        'Mesečna sprem.', 'Letna sprem.', 'st_delnic', 'Čas prid. podatkov',
        'Link_iz_stock_analysis', 'Link_iz_econ'
    ]
    
    obstoječi_stolpci = [col for col in željeni_stolpci if col in df_zdruzen.columns]
    ostali = [col for col in df_zdruzen.columns if col not in obstoječi_stolpci]
    
    koncni = obstoječi_stolpci + ostali
    return df_zdruzen[koncni]

def pridobi_delnice_iz_indeksov():
    df_indeksi = združitev_obeh()
    vse_delnice = []
    for i, (_, row) in enumerate(df_indeksi.iterrows(), 1):
        drzava = row['Drzava']
        link = row['Link_iz_stock_analysis']
  
        df_delnice_indeksa = funkcije.pridobi_delnice(link)
        if not df_delnice_indeksa.empty:
            df_delnice_indeksa['Drzava'] = drzava
            df_delnice_indeksa['Link_indeksa'] = link
            vse_delnice.append(df_delnice_indeksa)

    if vse_delnice:
        df_vse_delnice = pd.concat(vse_delnice, ignore_index=True)

        stolpci = ['Drzava', 'Ime', 'Simbol', 'Trenutna_cena', 'Dnevna_sprem.', 'Dobiček', 
                   'Volumen_delnice', 'Link_za_več', ]
        
        # Ohranimo samo stolpce, ki obstajajo
        obstojeci_stolpci = [col for col in stolpci if col in df_vse_delnice.columns]
        df_vse_delnice = df_vse_delnice[obstojeci_stolpci]
   
    return df_vse_delnice
   
    
def pridobi_delnice_iz_indeksov_z_dodatki(Drzava = None):
    df = združitev_obeh()
    if Drzava :
        if type(Drzava) == str:
            Drzave = [Drzava]
        df = df[df["Drzava"].isin(Drzave)]
    if df.empty:
        print("Nobenega indeksa za navedeno državo")
        return pd.DataFrame()
    
    vse_delnice = []
    for i, (_, vrstica) in enumerate(df.iterrows(), 1):
        drzava = vrstica["Drzava"]
        link = vrstica["Link_iz_stock_analysis"]
        df_delnice = funkcije.pridobi_delnice(link)
        dod_podatki = []
        
        if not df_delnice.empty :
            dod_podatki = []
            for _, df_vrstica in df_delnice.iterrows():
                link_del = df_vrstica["Link_za_več"]
                dod_info = funkcije.pridobivanje_dod_info(link_del)
                dod_podatki.append(dod_info)
                time.sleep(0.5)

        df_dodatno = pd.DataFrame(dod_podatki)
        df_delnice_z_dodatni = pd.concat([df_delnice, df_dodatno], axis= 1)
        df_delnice_z_dodatni["Drzava"] = drzava
        vse_delnice.append(df_delnice_z_dodatni)
        time.sleep(0.5)

    df_vse_delnice = pd.concat(vse_delnice, ignore_index=True)
    stolpci = ["Ime", "Simbol", "Drzava", "Ime_indeksa", "Trenutna_cena", 
               "Dnevna_sprem.", "Dobiček", "Volumen_delnice",
               "PE Ratio", "Dividend", "Volume", "52-Week Range", "Beta", "Earnings Date",
               "Link_za_več"]
    obstojeci_stolpci = [col for col in stolpci if col in df_vse_delnice.columns]
    return df_vse_delnice[obstojeci_stolpci]

    








