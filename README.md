# PlugPilot 1.0 — version finale

PlugPilot est une application Windows locale pour piloter des prises
TP-Link Kasa et Tapo.

## Fonctions

- démarrage rapide avec les prises mémorisées ;
- découverte automatique ou ajout guidé par adresse IP ;
- contrôle marche / arrêt ;
- renommage local persistant ;
- puissance instantanée et consommation du jour ;
- estimation du coût électrique ;
- recherche ;
- thème clair et sombre ;
- fonctionnement dans la zone de notification ;
- fréquence d'actualisation configurable ;
- actualisation ralentie lorsque la fenêtre est masquée ;
- instance unique pour éviter les doublons ;
- journal d'erreurs local ;
- identifiants protégés par le gestionnaire Windows.

## Pourquoi l'application est distribuée dans un dossier

La construction utilise le mode `onedir` de PyInstaller. Ce choix est
volontaire : le démarrage est plus rapide et évite l'extraction complète
de l'application à chaque lancement.

L'utilisateur final lance toujours un seul fichier :

`PlugPilot.exe`

Les autres fichiers du dossier sont les dépendances internes de l'application.

## Construire l'application

Double-clique sur :

`construire_exe.bat`

Résultat :

`dist\PlugPilot\PlugPilot.exe`

## Construire l'installateur

1. Installe Inno Setup 6.
2. Double-clique sur `construire_installateur.bat`.

Résultat :

`installer\PlugPilot-Setup.exe`

## P110 non détectée

Dans l'application Tapo, active la compatibilité avec les services tiers,
puis relance la recherche dans PlugPilot.

## Données locales

La configuration et le journal d'erreurs sont enregistrés dans :

`C:\Users\<utilisateur>\.tapo_pc_control`
