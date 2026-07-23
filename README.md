# LabQR – OneNote odkazy přes GitHub Pages

## Nastavení

1. Vytvoř na GitHubu veřejný repozitář `LabQR`.
2. Nahraj do něj `index.html`, `pages.json`, `create_qr.py`,
   `requirements.txt` a složku `QR`.
3. V GitHubu otevři **Settings → Pages**.
4. V části **Build and deployment** zvol:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/(root)**
5. Ulož nastavení.
6. V `create_qr.py` změň:
   - `GITHUB_USER = "TVUJ_GITHUB_LOGIN"`
   - případně `REPOSITORY = "LabQR"`

## Instalace na Windows

V PowerShellu ve složce projektu:

```powershell
py -m pip install -r requirements.txt
```

## Přidání odkazu

```powershell
py create_qr.py AFM-001 "CELÝ_ONENOTE_ODKAZ"
```

Skript:
- doplní nebo vytvoří položku v `pages.json`,
- vytvoří `QR\AFM-001.png`,
- vypíše výslednou krátkou adresu.

Přepsání existujícího ID:

```powershell
py create_qr.py AFM-001 "NOVÝ_ONENOTE_ODKAZ" --overwrite
```

## Nahrání změn přes Git

```powershell
git add pages.json QR
git commit -m "Add AFM-001"
git push
```

Případně lze soubory nahrát ručně přes webové rozhraní GitHubu.

## Test

Otevři:

```text
https://TVUJ_GITHUB_LOGIN.github.io/LabQR/?id=AFM-001
```

## Pozor na soukromí

Obsah veřejného `pages.json` může kdokoliv přečíst. Neukládej do něj citlivé
informace ani neveřejné odkazy, jejichž samotné zveřejnění představuje riziko.
Přístup k cílové stránce OneNote se stále řídí sdílecím oprávněním daného odkazu.
