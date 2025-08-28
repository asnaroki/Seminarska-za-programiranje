import izluščanje

df = izluščanje.združitev_obeh()
df.to_csv("Svetovni_indeksi.csv", index = False, encoding= "utf-8")
df1 = izluščanje.pridobi_delnice_iz_indeksov()
df1.to_csv("Delnice.csv", index= False , encoding= "utf-8") 
df2 = izluščanje.pridobi_delnice_iz_indeksov_z_dodatki("Slovenia")
df2.to_csv("Slov_delnice.csv", index= False, encoding= "utf-8")