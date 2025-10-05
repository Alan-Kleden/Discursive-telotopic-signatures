# -*- coding: utf-8 -*-
from __future__ import annotations

DOMAINS = {
    "climate": [
        "climate", "net zero", "emissions", "renewable", "carbon",
        "decarbon", "greenhouse", "paris agreement", "environment"
    ],
    "immigration": [
        "immigration", "migrant", "asylum", "visa", "border", "deportation",
        "refugee", "illegal migration", "removal", "detention"
    ],
    "security": [
        "security", "national security", "terrorism", "policing", "defence",
        "defense", "counter-terror", "law enforcement", "homeland"
    ],
    "health": [
        "health", "public health", "nhs", "hospital", "pandemic", "medical",
        "vaccin", "disease", "epidemic"
    ],
}

# règle d’assignation : ≥2 occurrences (mots/phrases) d’un domaine → assignation
MIN_MATCHES = 2
MIN_TOKENS = 800  # filtrage longueur
