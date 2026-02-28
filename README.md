# 17TRACK Custom

Custom integration for Home Assistant based on the core `seventeentrack` component.

- Domain: `seventeentrack_custom`
- Type: sensor / cloud polling
- Installable via HACS as a custom repository (Integration).

## Visualiser et gérer les colis dans Home Assistant

Cette intégration expose :

- des capteurs de synthèse par statut (`in_transit`, `delivered`, etc.) ;
- des services pour interagir avec 17TRACK :
  - `seventeentrack_custom.get_packages`
  - `seventeentrack_custom.add_package`
  - `seventeentrack_custom.archive_package`

> Les colis sont stockés côté 17TRACK (cloud). Home Assistant interroge l'API et affiche le résultat.

### 1) Récupérer le `config_entry_id`

Le plus simple :

1. Aller dans **Outils de développement → Services**.
2. Choisir `seventeentrack_custom.get_packages`.
3. Dans `config_entry_id`, sélectionner l'entrée proposée dans la liste.

Tu peux aussi lire l'ID depuis **Paramètres → Appareils et services → 17TRACK Custom**.

### 2) Appels de services (exemples YAML)

#### Lister les colis

```yaml
service: seventeentrack_custom.get_packages
data:
  config_entry_id: "VOTRE_CONFIG_ENTRY_ID"
```

#### Ajouter un colis

```yaml
service: seventeentrack_custom.add_package
data:
  config_entry_id: "VOTRE_CONFIG_ENTRY_ID"
  package_tracking_number: "LB123456789FR"
  package_friendly_name: "Commande AliExpress"
```

#### Archiver un colis

```yaml
service: seventeentrack_custom.archive_package
data:
  config_entry_id: "VOTRE_CONFIG_ENTRY_ID"
  package_tracking_number: "LB123456789FR"
```

### 3) Créer un visuel rapide (Dashboard)

Exemple de cartes Lovelace en YAML :

```yaml
views:
  - title: Colis
    path: colis
    cards:
      - type: entities
        title: Résumé 17TRACK
        entities:
          - entity: sensor.17track_in_transit
          - entity: sensor.17track_delivered
          - entity: sensor.17track_alert

      - type: button
        name: Rafraîchir les colis
        icon: mdi:refresh
        tap_action:
          action: perform-action
          perform_action: seventeentrack_custom.get_packages
          data:
            config_entry_id: "VOTRE_CONFIG_ENTRY_ID"
```

> Les IDs exacts des entités peuvent varier. Utilise l'autocomplétion de l'éditeur Lovelace pour sélectionner les bons capteurs.

### 4) Option pratique : scripts

Tu peux créer 2 scripts Home Assistant (`script.yaml`) pour ne pas retaper les champs :

```yaml
refresh_17track:
  alias: 17TRACK - Rafraîchir
  sequence:
    - service: seventeentrack_custom.get_packages
      data:
        config_entry_id: "VOTRE_CONFIG_ENTRY_ID"

add_17track_package:
  alias: 17TRACK - Ajouter un colis
  fields:
    tracking:
      required: true
      selector:
        text:
    name:
      required: true
      selector:
        text:
  sequence:
    - service: seventeentrack_custom.add_package
      data:
        config_entry_id: "VOTRE_CONFIG_ENTRY_ID"
        package_tracking_number: "{{ tracking }}"
        package_friendly_name: "{{ name }}"
```
