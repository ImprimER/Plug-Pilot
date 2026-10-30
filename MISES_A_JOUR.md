# Versions et mises à jour

## Utiliser une nouvelle version

Dans Réglages, le numéro de version et le bouton **Mises à jour** donnent accès
aux versions publiées sur GitHub. Le dépôt étant privé, le navigateur doit être
connecté à un compte autorisé. Ce bouton ouvre la liste des versions ; il ne
compare pas automatiquement les versions et ne télécharge rien en arrière-plan.
Si aucune version n'est publiée, aucun installateur n'est encore disponible.

Télécharger l'installateur voulu, quitter PlugPilot par son menu près de l'horloge,
puis lancer cet installateur. Ne pas désinstaller l'ancienne version au préalable.
L'identifiant Inno Setup reste identique. La configuration dans le profil utilisateur
et les identifiants du gestionnaire Windows ne font pas partie de l'installation.

La version exe 1.0 déjà installée recevra ce bouton lors de sa première mise à jour,
qui devra être téléchargée depuis GitHub directement.

## Préparer une version stable

1. Modifier et tester les sources dans PlugPilot_V2_Work avec lancer_dev.bat.
2. Après validation, changer APP_VERSION dans services/version.py, par exemple
   de 1.1.0.dev0 à 1.1.0. Chaque nouvelle version stable doit avoir un numéro supérieur.
3. Lancer `construire_installateur.bat`, qui prépare les dépendances puis lance
   `construire_version_stable.py`. Inno Setup 6 doit être installé.
   Le script refuse les versions de développement
   et reconstruit systématiquement l'exécutable avant l'installateur.
4. Tester l'installateur et la mise à jour depuis la version précédente.
5. Enregistrer les sources sur GitHub, créer une Release avec le tag correspondant
   (ex. v1.1.0), joindre installer/PlugPilot-Setup-1.1.0.exe et décrire les changements.
6. Reprendre les développements avec le prochain numéro se terminant par .dev0.

Ne jamais modifier AppId dans PlugPilot.iss entre deux versions.
Les versions de développement ne sont pas distribuées comme versions stables.
