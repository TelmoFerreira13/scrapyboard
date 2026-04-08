# Scrapyboard (Django)

Objectif: **scraper une page web**, **stocker** les items en base (SQLite), puis **afficher** les données via une page Django.

## 1) Installation

Dans le dossier du projet:

```bash
python3 -m venv .venv
source .venv/bin/activate

# Si ton pip a des soucis SSL, tu peux (temporairement) utiliser:
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org django requests beautifulsoup4

pip install -r requirements.txt
python manage.py migrate
```

## 2) Lancer le serveur

```bash
source .venv/bin/activate
python manage.py runserver
```

Puis ouvre `http://127.0.0.1:8000/` (liste des items).

## 3) Scraper une page (commande Django)

La commande s’appelle `scrape`:

```bash
source .venv/bin/activate
python manage.py scrape --url "https://exemple.com/page"
```

Par défaut, elle récupère les liens (`a[href]`). Pour un site réel, tu vas souvent préciser des sélecteurs CSS:

```bash
python manage.py scrape \
  --url "https://exemple.com/page" \
  --item-selector ".product-card" \
  --title-selector ".title" \
  --link-selector "a" \
  --price-selector ".price" \
  --limit 50
```

Notes:
- `--item-selector`: le “bloc” qui représente un item (carte produit, annonce, etc.)
- `--title-selector`: où trouver le titre, à l’intérieur de chaque item
- `--link-selector`: où trouver le lien, à l’intérieur de chaque item
- `--price-selector`: optionnel (texte du prix)
- `--limit`: limite le nombre d’insert/update

Les données vont dans la table `scraper_listing` (modèle `scraper.models.Listing`).

## 3bis) Scraper GOL (home, pagination Previous 10 games)

Le bouton "Previous 10 games" appelle une API JSON:
- `POST https://gol.gg/esports/ajax.home.php`
- payload: `start=0`, puis `start=10`, `start=20`, etc.

La commande correspondante:

```bash
source .venv/bin/activate
python manage.py scrape_gol_home
```

Options utiles:

```bash
python manage.py scrape_gol_home --start 0 --step 10 --max-pages 200 --sleep 0.2
```

Les données vont dans `scraper_golgame` (modèle `scraper.models.GolGame`).
La page d'affichage est `http://127.0.0.1:8000/gol/`.

## 4) Admin Django (optionnel)

```bash
source .venv/bin/activate
python manage.py createsuperuser
python manage.py runserver
```

Puis `http://127.0.0.1:8000/admin/`.

