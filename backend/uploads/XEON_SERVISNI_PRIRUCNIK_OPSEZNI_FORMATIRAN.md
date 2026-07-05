OBJAŠNjENJE: ECC ispravlja grešku na DIMM_A1 (5 puta). Zameniti RAM.

# 10. NAJČEŠĆI PROBLEMI I REŠENJA (FAQ – 50+ PITANJA)

P1: Kolika je maksimalna temperatura za Xeon Scalable?
O1: Zavisi od generacije: 85°C (1., 2., 3. gen Cooper), 83°C (3. gen Ice Lake),
    82°C (4. gen Sapphire Rapids).

P2: Šta znači greška CPU_TEMP_ERR?
O2: Procesor je prekoračio maksimalnu temperaturu. Proverite hladnjak, pastu,
    ventilatore i protok vazduha.

P3: Da li mogu da koristim desktop pastu za Xeon?
O3: Da, ali preporučuju se kvalitetnije paste poput Arctic MX-4 ili Noctua NT-H1.

P4: Koliko često treba menjati termalnu pastu na Xeon-u?
O4: Svake 2-3 godine za standardnu pastu, 3-5 godina za kvalitetnu.

P5: Kako da proverim temperaturu CPU-a bez ulaska u OS?
```bash
O5: Preko IPMI (ipmitool), iDRAC, iLO, ili BIOS-a.
```

P6: Da li Xeon podržava overklokovanje?
O6: Ne, Xeon Scalable nije predviđen za overklokovanje. Zaključan je.

P7: Šta je Tcase?
O7: Temperatura na površini procesorskog paketa (IHS). Meri senzor na vrhu.

P8: Šta je Tjunction?
O8: Temperatura unutar jezgra procesora. Obično 10-15°C viša od Tcase.

P9: Kako da znam koji socket imam?
O9: Proverite model matične ploče. LGA3647 (1. i 2. gen), LGA4189 (3. gen),
    LGA4677 (4. gen).

P10: Da li je LGA3647 kompatibilan sa LGA4189?
O10: Ne, različiti socketi. Nisu mehanički kompatibilni.

P11: Koji hladnjak preporučujete za Xeon Platinum 8490H (350W)?
O11: Tečno hlađenje (DLC) ili Dynatron R33 (vazdušno, ali na granici).

P12: Šta je PROCHOT?
O12: Signal koji smanjuje frekvenciju procesora kada dostigne kritičnu temperaturu.

P13: Kako da onemogućim PROCHOT?
O13: Ne preporučuje se – može dovesti do oštećenja procesora.

P14: Da li garancija pokriva pregorevanje usled lošeg hlađenja?
O14: Ne, garancija ne pokriva termalne probleme izazvane lošim hlađenjem.

P15: Kako da prijavim RMA?
O15: Preko Intel podrške ili distributera. Potreban je serijski broj i račun.

P16: Koliko dugo traje RMA proces?
O16: Obično 5-10 radnih dana.

P17: Da li mogu da zamenim Xeon procesor bez skidanja matične ploče?
O17: Da, u većini servera (ručica za otpuštanje hladnjaka).

P18: Šta je VRM?
O18: Voltage Regulator Module – naponski regulator na matičnoj ploči.

P19: Kako da proverim da li je VRM pregrejan?
O19: Preko IPMI senzora (VRM Temp) ili termalnom kamerom.

P20: Da li Xeon podržava ECC RAM?
O20: Da, svi Xeon Scalable podržavaju ECC DDR4/DDR5 memoriju.

P21: Koja je maksimalna količina RAM-a po procesoru?
O21: 1. gen: 768GB, 2. gen: 1.5TB, 3. gen: 4TB, 4. gen: 4TB.

P22: Da li Xeon podržava PCIe 4.0?
O22: Da, od 3. generacije (Ice Lake) pa nadalje.

P23: Da li Xeon podržava PCIe 5.0?
O23: Da, od 4. generacije (Sapphire Rapids).

P24: Šta je CXL?
O24: Compute Express Link – protokol za povezivanje akceleratora i memorije.

P25: Kako da ažuriram mikrokod?
O25: Preko BIOS update-a ili preko Linux microcode_ctl paketa.

P26: Da li Xeon ima integrisanu grafiku?
O26: Većina modela NEMA. Samo neki F modeli imaju integrisanu grafiku.

P27: Kako da resetujem SEL?
```bash
O27: `ipmitool sel clear` (sa root privilegijama).
```

P28: Šta znači POST kod 0xE0?
O28: Termalna greška (CPU_TEMP_ERR).

P29: Kako da podesim brzinu ventilatora u IPMI?
```bash
O29: `ipmitool raw 0x30 0x45 0x01 0x01` (full speed) ili 0x00 (auto).
```

P30: Da li mogu da koristim Xeon u desktop matičnoj ploči?
O30: Ne, Xeon zahteva server matičnu ploču sa odgovarajućim socketom.

P31: Šta je TDP?
O31: Thermal Design Power – maksimalna količina toplote koju procesor emituje.

P32: Kako da izračunam potrebni TDP hladnjaka?
O32: Hladnjak mora imati TDP veći ili jednak procesoru (npr. 350W hladnjak za 350W CPU).

P33: Da li Xeon podržava AVX-512?
O33: Da, sve generacije podržavaju AVX-512 (sa različitim podskupovima).

P34: Šta je AMX?
O34: Advanced Matrix Extensions – instrukcije za mašinsko učenje (4. generacija).

P35: Kako da testiram stabilnost Xeon-a?
O35: Koristite Prime95, Intel Burn Test, ili Linpack.

P36: Koliko dugo treba da traje stres test?
O36: Minimum 1 sat, preporučuje se 24 sata za kritične sisteme.

P37: Šta je throttling?
O37: Smanjenje frekvencije procesora kako bi se smanjila temperatura.

P38: Da li throttling skraćuje vek procesora?
O38: Ne, ali čest throttling ukazuje na loše hlađenje – to skraćuje vek.

P39: Kako da proverim da li je procesor originalan?
O39: Proverite FPO broj na Intel-ovoj web stranici za verifikaciju.

P40: Šta je batch broj?
O40: Serijski broj procesora koji označava proizvodnu seriju (npr. L014A123).

P41: Da li mogu da vratim procesor ako nije kompatibilan?
O41: Zavisi od politike prodavca. Neki dozvoljavaju povrat u roku od 14 dana.

P42: Kako da očistim staru termalnu pastu?
O42: Koristite izopropil alkohol (90%+) i bezvojne maramice.

P43: Da li mogu da koristim aceteton za čišćenje paste?
O43: Ne – aceteton može oštetiti plastične delove procesora.

P44: Šta je IHS?
O44: Integrated Heat Spreader – metalni poklopac na vrhu procesora.

P45: Da li Xeon ima zaštitu od prenapona?
O45: Da, ali ne za ekstremne slučajeve (> 10% iznad specifikacije).

P46: Kako da proverim da li je procesor mrtav?
O46: Testirajte u drugom serveru. Ako ne radi – mrtav je.

P47: Da li se isplati kupiti polovni Xeon?
O47: Da, ali proverite garanciju i fizičko stanje (pinovi, IHS).

P48: Šta je ESD i zašto je opasan?
O48: Electrostatic Discharge – može trajno oštetiti procesor.

P49: Kako da zaštitim procesor od ESD?
O49: Koristite antistatički remen i radite na antistatičkoj podlozi.

P50: Gde da nađem zvanične specifikacije za moj model?
O50: Na Intel ARK sajtu: https://ark.intel.com

P51: Kako da ažuriram BIOS za novi Xeon?
O51: Preuzmite BIOS sa sajta proizvođača matične ploče i instalirajte preko USB-a.

P52: Da li Xeon podržava virtualizaciju?
O52: Da, svi Xeon Scalable podržavaju Intel VT-x i VT-d.

P53: Šta je Intel SGX?
O53: Software Guard Extensions – zaštita memorije od neovlašćenog pristupa.

P54: Šta je Intel TDX?
O54: Trust Domain Extensions – napredna virtualizacija sa zaštitom (4. gen).

P55: Kako da proverim da li je sistem stabilan nakon servisiranja?
O55: Pokrenite stres test od 1h i pratite temperature i greške u SEL-u.

# 11. ZAMENA PROCESORA – KORAK PO KORAK

## 11.1 Priprema

---

- Isključite server iz struje (videti sekciju 3.1).
- Nosite antistatički remen.
- Postavite server na ravnu površinu.
- Skinite bočni poklopac kućišta.
- Identifikujte procesor koji menjate (CPU1, CPU2, itd.).
- Pripremite novi procesor (još u antistatičkoj kesi).

## 11.2 Demontaža starog procesora

---

# 1. Odvojite kabl ventilatora sa matične ploče.
# 2. Odvrnite šrafove hladnjaka (krstasto, dijagonalno).
   - LGA3647: 4 šrafa (T20 Torx).
   - LGA4189: 4 šrafa (T20 Torx).
   - LGA4677: 4 šrafa (T30 Torx) – pažljivo, veći moment.
# 3. Pažljivo podignite hladnjak ravno nagore (bez uvrtanja).
# 4. Ako je hladnjak zalepio, lagano ga okrenite levo-desno (ne povlačite na silu).
# 5. Očistite staru termalnu pastu sa procesora i hladnjaka.
   - Koristite izopropil alkohol i bezvojne maramice.
   - NE KORISTITE vodu ili deterdžent.
# 6. Otpustite metalnu ručicu na socket-u.
# 7. Pažljivo podignite poklopac socket-a.
# 8. Uhvatite procesor za ivice i podignite ga ravno nagore.
# 9. Stavite stari procesor u antistatičku kesu.

## 11.3 Montaža novog procesora

---

# 1. Izvadite novi procesor iz antistatičke kese (držite za ivice).
# 2. Proverite orijentaciju (trougao na procesoru i socket-u moraju da se poklapaju).
# 3. Pažljivo spustite procesor u socket – BEZ pritiska! Treba da "padne" na svoje mesto.
# 4. Spustite poklopac socket-a i pritisnite ručicu do kraja.
# 5. Nanesite termalnu pastu (veličina zrna graška – 0.5–1g).
# 6. Postavite hladnjak na procesor.
# 7. Zategnite šrafove KRSTASTO (naizmenično) sa momentom od:
   - 0.5 Nm za LGA3647
   - 0.6 Nm za LGA4189
   - 0.8 Nm za LGA4677
# 8. Priključite kabl ventilatora na matičnu ploču.
# 9. Proverite da li je sve čvrsto (hladnjak ne sme da se pomera).

## 11.4 Testiranje nakon montaže

---

# 1. Priključite napajanje i uključite server.
# 2. Uđite u BIOS (F2, Del) i proverite:
   - Da li je procesor detektovan (model, frekvencija).
   - Temperatura CPU-a u BIOS-u (treba da bude 30–45°C u idle-u).
# 3. Pokrenite OS i instalirajte potrebne drajvere (ako je noviji procesor).
# 4. Pokrenite stres test (npr. Prime95) u trajanju od 1h.
# 5. Pratite temperature (ne sme preći Tcase max).
# 6. Proverite SEL da nema grešaka.
# 7. Ako je sve prošlo dobro – servisiranje je uspešno.

# 12. DODATNE PREPORUKE

## 12.1 Ažuriranje BIOS/UEFI

---

Pre instalacije novijeg Xeon procesora, OBAVEZNO ažurirajte BIOS na najnoviju
verziju. Stari BIOS možda ne podržava novije mikro kodove.

KAKO:
# 1. Preuzmite BIOS sa sajta proizvođača matične ploče.
# 2. Kopirajte na FAT32 USB fleš disk.
# 3. Uđite u BIOS i izaberite "BIOS Update" ili "Flash".
# 4. Pratite uputstva na ekranu.
# 5. NEMOJTE isključivati server tokom update-a (može trajati 5-10 minuta).

## 12.2 Stress testiranje

---

Preporučeni alati za stres test:
- Prime95 (Windows/Linux) – najpoznatiji, opterećuje sve jezgra.
- Intel Burn Test (Windows) – brz, agresivan test.
- Linpack (Linux) – koristi se u HPC okruženjima.
- CPU-Z (Windows) – ima ugrađen stres test.

TRAJANJE:
- Minimalno: 1 sat.
- Preporučeno: 24 sata za kritične sisteme.
- Za data center: 72 sata sa različitim opterećenjima.

## 12.3 Praćenje performansi

---

Koristite sledeće alate za praćenje performansi:
- htop / top (Linux) – opterećenje CPU-a.
- iostat (Linux) – I/O performanse.
- vmstat (Linux) – memorija i procesi.
- Performance Monitor (Windows) – sve metrike.
- Intel VTune – napredni profiler.
- Intel Advisor – optimizacija koda.

## 12.4 Prevencija problema

---

- Redovno čistite prašinu (svakih 6 meseci).
- Redovno proveravajte SEL (svake nedelje).
- Zamenite termalnu pastu na svake 3 godine.
- Ažurirajte BIOS na svake 2 godine.
- Pratite temperature u realnom vremenu (preko IPMI ili SNMP).
- Instalirajte UPS (neprekidno napajanje) za stabilan napon.
- Osigurajte dovoljan protok vazduha u server sobi.
- Postavite upozorenja (alerts) za temperaturu, napon i ventilatore.

# 13. DODATAK A – TABELE SA PINOVIMA SOCKETA

LGA3647 (1. i 2. generacija):
- Ukupno pinova: 3647
- Broj pinova za napajanje: ~400
- Broj pinova za podatke: ~1200
- Ostatak: GND (uzemljenje)
- Raspored: 4x4 matrica podržava 4 procesora

LGA4189 (3. generacija):
- Ukupno pinova: 4189
- Broj pinova za napajanje: ~450
- Broj pinova za podatke: ~1400
- Ostatak: GND
- Raspored: 4x4 matrica, podržava do 8 procesora (Cooper Lake)

LGA4677 (4. generacija):
- Ukupno pinova: 4677
- Broj pinova za napajanje: ~500
- Broj pinova za podatke: ~1600
- Ostatak: GND
- Raspored: 4x4 matrica, podržava CXL i PCIe 5.0

# 14. DODATAK B – SPISAK KOMANDI ZA LINUX

# 1. Čitanje temperature CPU-a:
```bash
   `cat /sys/class/thermal/thermal_zone*/temp
```

# 2. Čitanje frekvencije CPU-a:
```bash
   `cat /proc/cpuinfo | grep "MHz"
```

# 3. Čitanje informacija o CPU-u:
```bash
   `lscpu
```

# 4. Čitanje SEL (IPMI):
```bash
   `ipmitool sel list
```

# 5. Brisanje SEL:
```bash
   `ipmitool sel clear
```

# 6. Podešavanje brzine ventilatora (full speed):
```bash
   `ipmitool raw 0x30 0x45 0x01 0x01
```

# 7. Čitanje napona CPU-a:
```bash
   `ipmitool sensor get "CPU1 Vcore"
```

# 8. Gašenje servera:
```bash
   `shutdown -h now
```

# 9. Restart servera:
```bash
   `reboot
```

# 10. Praćenje logova u realnom vremenu:
```bash
    `tail -f /var/log/syslog
```

# 11. Provera opterećenja CPU-a:
```bash
    `top
```

# 12. Provera opterećenja CPU-a (detaljnije):
```bash
    `htop
```

# 13. Provera I/O performansi:
```bash
    `iostat -x 1
```

# 14. Provera memorije:
```bash
    `free -h
```

# 15. Provera diskova:
```bash
    `df -h
```

# 15. DODATAK C – SPISAK ALATA I NJIHOVA NAMENA

ALATI ZA MONITORING:
# 1. IPMI – upravljanje serverom nezavisno od OS-a
# 2. iDRAC – Dell-ov remote management
# 3. iLO – HPE-ov remote management
# 4. SNMP – mrežni monitoring (Zabbix, Nagios, PRTG)
# 5. Intel DCM – data center monitoring
# 6. HWMonitor – Windows temperatura i napon
# 7. Open Hardware Monitor – open source monitoring
# 8. lm-sensors – Linux senzori (sensors komanda)

ALATI ZA STRES TEST:
# 1. Prime95 – CPU stres test
# 2. Intel Burn Test – agresivni stres test
# 3. Linpack – HPC stres test
# 4. CPU-Z – stres test i informacije
# 5. Geekbench – benchmark

ALATI ZA ČIŠĆENJE:
# 1. Izopropil alkohol (90%+) – čišćenje paste
# 2. Bezvojne maramice – bez ostataka
# 3. Kompresovani vazduh – čišćenje prašine
# 4. Antistatička četka – nežno čišćenje pinova
# 5. Usisivač sa ESD zaštitom – za prašinu (oprezno)

ALATI ZA MONTAŽU:
# 1. PH2 križni odvijač
# 2. T20 Torx odvijač
# 3. T30 Torx odvijač
# 4. Moment ključ (0.5–1.5 Nm)
# 5. Plastična lopatica za pastu
# 6. Antistatički remen za ručni zglob
# 7. Antistatička podloga
# 8. Fles lampa

# 16. ZAVRŠNE NAPOMENE I LITERATURA

Ovaj priručnik je sačinjen na osnovu zvaničnih Intel specifikacija, iskustava
servisera i preporuka proizvođača matičnih ploča. Svi podaci su tačni na dan
04.07.2026. godine.

PREPORUČENA LITERATURA:
# 1. Intel Xeon Scalable Processor Datasheet – Volume 1 (Intel Corporation)
# 2. Intel Xeon Scalable Processor Datasheet – Volume 2 (Intel Corporation)
# 3. Intel 64 and IA-32 Architectures Software Developer's Manual (Intel)
# 4. Intel IPMI 2.0 Specification (Intel)
# 5. Server System Reference Guide (SuperMicro, Dell, HPE)

VAŽNO: Uvek pratite zvanične upute proizvođača vašeg servera. Ovaj priručnik
služi kao opšti vodič i ne zamenjuje specifične upute za vaš model.

ZA DODATNA PITANJA:
- Intel podrška: https://www.intel.com/support
- Forum: https://community.intel.com
- Reddit: r/homelab, r/sysadmin


---

KRAJ DOKUMENTA

---
