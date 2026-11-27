# Transferer la memoire de Mistybot

Double-cliquer sur **transfer-railway-memory.bat**, sans administrateur.
Garder les fichiers `.bat`, `.ps1` et `railway-memory-transfer.py` ensemble.
Python est utilise sur Railway ; il n'est pas necessaire de l'installer sur le PC pour le transfert.

## Recuperer et transferer la memoire actuelle

1. Choisir **1**, se connecter au compte SOURCE et selectionner son projet et son service.
2. Attendre **SAUVEGARDE VALIDE**. Le fichier est conserve sur le Bureau dans `Mistybot Railway Backups`.
3. Accepter l'installation, puis se connecter au compte CIBLE et selectionner son service.
4. Sur Railway, preparer la cible : volume monte sur `/app/data`, commande de demarrage `sleep infinity`, puis deployer et attendre **Online**.
5. Taper **RESTAURER**. L'envoi, la sauvegarde de l'ancienne memoire cible et la verification se font automatiquement.
6. Apres **TRANSFERT VERIFIE**, arreter l'ancien bot, remettre `python main.py` sur le nouveau et redeployer.

Aucune commande a coller dans un terminal SSH. Aucune cle SSH a chercher : le script cree et enregistre une cle dediee a chaque compte, puis la reutilise.
La copie contient la memoire au moment de l'extraction ; les changements ulterieurs sur la source n'y figurent pas.

## Reprendre apres un echec

Relancer le `.bat`, choisir **2**, puis selectionner la sauvegarde souhaitee.
Les fichiers identiques ne sont presentes qu'une fois. Cette option ne cree plus de copies supplementaires.

Si le bot cible est actif, le script refuse la restauration et permet de reessayer apres la mise en pause.
Si la connexion s'interrompt pendant l'envoi, garder la cible avec `sleep infinity` et reprendre avec **2** : une memoire deja copiee a l'identique est reconnue automatiquement.
Les erreurs de connexion sont limitees dans le temps ; un service arrete, supprime ou inaccessible ne peut pas etre extrait.

## Fichiers conserves

- Sur le PC : sauvegarde `memory-source-*.json` et confirmation `transfer-verified-*.json`.
- Sur la cible : ancienne memoire `memory-before-transfer-*.json` si elle existait et etait differente.
- Dans le dossier Windows `.ssh` : cle privee dediee, a conserver confidentielle.

Le script ne transfere pas les variables Railway ni le code du bot. Il ne change pas automatiquement la commande de demarrage et n'arrete pas de service.
Les fonctions SSH utilisees sont documentees dans [la CLI Railway](https://docs.railway.com/cli/ssh).

## Verification locale du script

Les tests utilisent uniquement des fichiers temporaires, jamais un compte Railway :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test-transfer-railway-memory.ps1
python.exe -B -m unittest -v test_railway_memory_transfer
```

Sous Windows, les tests Python simulent uniquement le verrou Linux et la synchronisation du repertoire. La lecture, la sauvegarde et le remplacement des fichiers sont reels dans des dossiers temporaires.
