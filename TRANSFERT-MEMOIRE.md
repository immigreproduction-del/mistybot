# Transfert de la memoire Mistybot

Double-cliquer sur `transfer-railway-memory.bat`, sans droits administrateur.
Garder le fichier `.ps1` a cote. Railway CLI et OpenSSH doivent etre installes.

## Choisir une source

- Choix 1 : connexion a l'ancien compte, selection du service, telechargement SFTP.
  En cas d'echec, le script propose une extraction SSH guidee.
- Choix 2 : selection d'une sauvegarde locale. Aucun acces a l'ancien compte requis.

Les fichiers sont conserves dans `Mistybot Railway Backups` sur le Bureau Windows.
Un echec ne demande jamais de supprimer une sauvegarde ni de recommencer la recuperation.
Le transfert porte uniquement sur `memory.json`, y compris sa memoire permanente.
Les variables Railway et autres fichiers du volume ne sont pas transferes.

## Restaurer

Le service cible doit etre deploye, ONLINE, avec son volume monte sur `/app/data`.
Le programme du bot doit etre arrete : utiliser temporairement `sleep infinity` comme
commande de demarrage. Si Railway endort le service, le reveiller avant la session SSH.
Le script ne contourne pas les restrictions du compte ou du plan Railway.

Confirmer le compte et le service cibles, puis saisir `RESTAURER`.
Indiquer une cle SSH privee deja associee au compte, ou appuyer sur Entree pour creer
une cle unique. Aucune ancienne cle n'est remplacee. Accepter son enregistrement Railway.

Les commandes sont preparees dans le presse-papiers. Dans SSH, coller puis appuyer
sur Entree. Copier le resultat contenant `MISTY_TRANSFER_OK:...`, puis taper `exit`.
Le script verifie ce resultat : la commande affichee seule ne compte pas comme succes.

L'installation refuse un processus `main.py` actif, decompresse dans un dossier
temporaire du volume, verifie l'empreinte SHA256, sauvegarde l'ancienne cible, puis
remplace `memory.json` par renommage sur le meme volume. Le controle de processus
cible le lancement habituel de Mistybot (`main.py`); il ne remplace pas la mise en
maintenance si vous avez personnalise la commande de lancement.

Apres confirmation, arreter l'ancien bot, retirer la commande temporaire de la cible
et redeployer le nouveau bot. Conserver les sauvegardes et tester une information
permanente connue. Les souvenirs temporaires peuvent expirer independamment du transfert.

## Limites et verification

SSH reste guide : connexion, collage et copie du resultat sont necessaires. Un resultat
manquant est annonce comme non confirme, jamais comme une reussite. Ne pas publier les
sorties contenant la memoire. Le collage de secours est limite a 200 000 caracteres
compresses pour eviter les gros collages peu fiables.

Tests locaux sans connexion Railway :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test-transfer-railway-memory.ps1
```
