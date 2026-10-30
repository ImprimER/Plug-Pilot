# Mises à jour de PlugPilot

## Dans l'application

Réglages → Mises à jour recherche la dernière version stable publiée.
Si une version plus récente existe, PlugPilot propose un lien vers les notes de version et le bouton
**Mettre à jour**. Le téléchargement se déroule en arrière-plan avec une barre
de progression et peut être annulé. La taille et l'empreinte SHA-256 fournies par
GitHub sont vérifiées avant de proposer **Installer et redémarrer**.
La mise à jour s’installe sans les pages de l’assistant, avec une fenêtre de progression, puis PlugPilot redémarre. Les choix de raccourcis et de démarrage existants sont conservés. La première installation reste interactive.
Les réglages et identifiants restent dans le profil utilisateur et le gestionnaire Windows.

La recherche est déclenchée à la demande. Rien n'est installé automatiquement.
Dans une session de développement, l'installateur peut être téléchargé et son chemin
affiché, mais il n'est pas exécuté : les sources restent indépendantes de l'exe installé.
L'exe 1.0 actuel devra être mis à niveau manuellement une première fois pour recevoir
ce système.

## Distribution

- Sources et installateurs publics : https://github.com/ImprimER/Plug-Pilot
- Aucun identifiant GitHub n'est embarqué ni demandé aux utilisateurs.
- Les brouillons et préversions ne sont pas proposés.
- Sans version publiée, la fenêtre signale qu'aucune version stable n'est disponible.

## Préparer une version stable

1. Tester les sources dans PlugPilot_V2_Work avec lancer_dev.bat.
2. Après validation, définir APP_VERSION dans services/version.py, par exemple
   1.1.0. Chaque nouvelle version stable doit avoir un numéro supérieur.
3. Lancer construire_installateur.bat. Inno Setup 6 doit être installé.
   Le script refuse les versions .dev0 et reconstruit systématiquement l'exe.
   Il produit installer/PlugPilot-Setup-1.1.0.exe et son fichier .exe.sha256.
4. Tester l'installation et la mise à niveau depuis la version précédente.
5. Enregistrer le code dans le dépôt Plug-Pilot. Dans ce même dépôt public,
   créer une Release avec le tag exact v1.1.0, les changements et les deux fichiers.
   Vérifier que GitHub indique une empreinte SHA-256 pour l'asset exe avant publication.
   Seuls l'installateur construit, son empreinte et les notes doivent être publiés,
   jamais les configurations locales, sauvegardes, logs ou environnements Python.
6. Après publication, vérifier la détection et le téléchargement depuis une version antérieure.
7. Reprendre le développement avec le prochain numéro se terminant par .dev0.

Ne pas modifier AppId ni le mode d'installation de PlugPilot.iss entre deux versions.
L'empreinte contrôle l'intégrité du fichier téléchargé ; elle ne remplace pas une
signature Authenticode. Windows peut encore afficher un avertissement pour un
installateur non signé.

La version 1.1.2 apporte le lancement simplifié. La mise à niveau depuis une version antérieure peut donc encore afficher l’ancien assistant une dernière fois. Les mises à jour lancées depuis 1.1.2 utiliseront le parcours simplifié.
