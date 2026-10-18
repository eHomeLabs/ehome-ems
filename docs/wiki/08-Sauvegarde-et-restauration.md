# 08 — Sauvegarder et reproduire l’installation

[Accueil](Home.md) · [Précédent](07-Validation.md) · [Suite : dépannage](09-Depannage.md)

## Dès l’installation du RPi

Conserver hors du RPi :

- la référence de l’image Raspberry Pi OS et sa date ;
- les références du RPi, du HAT et du SSD ;
- les versions OS, noyau, EEPROM, Docker et Compose ;
- une copie de la configuration de démarrage et le contenu de la configuration EEPROM ;
- le commit du projet utilisé ;
- le journal d’installation, les choix réseau et les résultats des contrôles.

Les informations privées restent dans une sauvegarde locale protégée. Les mots de passe et clés privées restent dans le gestionnaire de secrets habituel.

**RPi / terminal**, créer un relevé local dans un dossier privé :

```bash
umask 077
record_dir="$HOME/ehome-install-$(date +%Y%m%d-%H%M%S)"
mkdir "$record_dir"
cat /etc/os-release > "$record_dir/os-release.txt"
uname -a > "$record_dir/kernel.txt"
rpi-eeprom-config > "$record_dir/eeprom-config.txt"
sudo rpi-eeprom-update > "$record_dir/eeprom-version.txt"
cp /boot/firmware/config.txt "$record_dir/config.txt"
cp /boot/firmware/cmdline.txt "$record_dir/cmdline.txt"
sudo docker version > "$record_dir/docker.txt"
sudo docker compose version > "$record_dir/compose.txt"
printf 'Dossier créé : %s\n' "$record_dir"
```

Transférer ce dossier vers le PC ou une sauvegarde dédiée, par exemple avec un client SFTP via SSH. Ce relevé **n’est ni une image du SSD ni une sauvegarde de l’application**.

## Quand l’EMS sera déployé

Documenter avant la première sauvegarde :

| À sauvegarder | À préciser avec l’implémentation |
| --- | --- |
| Version logicielle | Commit, version des images et éventuelles migrations |
| Configuration | Fichier Compose réel et configuration sans secrets |
| Secrets | Copie séparée protégée, procédure de renouvellement |
| SQLite | Chemin et méthode de copie cohérente |
| Volumes | Liste, chemins et propriétaires |
| Historique | Politique de rétention et taille attendue |

Ne pas copier uniquement le fichier principal d’une base SQLite en cours d’écriture : les écritures peuvent aussi se trouver dans les fichiers WAL. Utiliser une sauvegarde cohérente fournie par l’application ou arrêter proprement les services concernés avant de copier l’ensemble requis. La procédure exacte sera ajoutée avec le stockage réel. [Référence SQLite : sauvegarde cohérente](https://www.sqlite.org/backup.html).

Une copie sur le même NVMe ne protège pas contre sa panne. Garder au moins une copie sur un autre support et vérifier qu’elle est lisible.

## Reconstruction sur un SSD de remplacement

1. Reprendre les [phases d’installation](03-Installation-RPi5-NVMe.md) sur le nouveau disque.
2. Refaire les contrôles ARM64, NVMe, réseau et Docker.
3. Récupérer la version de code et les images identifiées dans le journal.
4. Restaurer les données et permissions selon la procédure de cette version.
5. Remettre les secrets par le canal local prévu.
6. Démarrer en simulation ou avec les sources désactivées.
7. Vérifier l’historique puis reconnecter les sources en lecture seule.
8. Refaire la [validation](07-Validation.md) et noter la restauration.

Ne pas écraser l’unique sauvegarde pour faire un essai. Tester sur une copie. Restaurer une ancienne version applicative avec une base déjà migrée exige une vérification de compatibilité.

## À chaque mise à jour future

Noter l’ancienne version, sauvegarder, lire les migrations, appliquer la nouvelle version puis contrôler les flux et les historiques. En cas d’échec, revenir à une paire cohérente **logiciel + données**, pas seulement à une ancienne image.

La fréquence des sauvegardes et leur durée de conservation restent à choisir selon la quantité d’historique que l’on accepte de perdre.
