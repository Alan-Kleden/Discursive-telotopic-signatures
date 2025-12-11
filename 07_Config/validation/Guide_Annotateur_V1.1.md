# Guide de l’annotateur — V1.1

## Objectif
Évaluer la **force conative** (rhétorique de volition/interdiction) dans chaque extrait de texte institutionnel.  
**Important** : vous n’évaluez **ni la qualité**, **ni l’éthique**, **ni votre accord personnel** avec le texte.  
Vous mesurez uniquement l’**intensité rhétorique** :
- **FC** = pousser à agir
- **FI** = freiner/interdire

## Renseigner **toujours** FC et FI
- **FC (0–5, décimales ok)** : force avec laquelle le texte pousse à l’action, exprime volonté/engagement.
- **FI (0–5, décimales ok)** : force avec laquelle le texte freine, interdit, s’oppose.
- On renseigne **toujours** les deux scores. Si l’un est absent → **mettez 0** (ne laissez pas vide).

---

## Échelles détaillées

### FC (Force Concordante — Promotion/Volition)
- **0.0** = Aucune volition (purement descriptif/procédural)
- **1.0** = Considération passive (« may consider », « could explore »)
- **2.0** = Intention faible (« should », « plan to »)
- **3.0** = Engagement modéré (« will », « commit to »)
- **4.0** = Engagement fort (« must ensure », « guarantee »)
- **5.0** = Impératif absolu (« shall », « is imperative »)

### FI (Force Inhibitrice — Opposition/Interdiction)
- **0.0** = Aucune opposition
- **1.0** = Désapprobation légère (« discourage », « avoid »)
- **2.0** = Restriction (« limit », « reduce », « control »)
- **3.0** = Opposition (« oppose », « reject », « prevent »)
- **4.0** = Interdiction forte (« ban », « prohibit », « eliminate »)
- **5.0** = Interdiction absolue (« abolish », « zero tolerance »)

---

## Cas typiques
- **Pousse action, n’interdit rien** → FC > 0, FI = 0  
- **Interdit/freine, sans proposer action** → FI > 0, FC = 0  
- **« Ban X, promote Y »** → FC > 0 **et** FI > 0  
- **Purement procédural/neutre** → FC = 0, FI = 0

---

## Repères linguistiques rapides
**Augmentent FC** : will, plan, commit, urge, support, expand, invest, ensure, deliver, adopt, implement  
**Augmentent FI** : must not, ban, prohibit, stop, oppose, reject, prevent, eliminate, abolish, restrict

---

## Exemples annotés
**Ex. 1** — « We will expand renewable energy… ensure… »  
FC = **3.5** ; FI = **0.0**

**Ex. 2** — « The government must ban all new fossil fuel subsidies… »  
FC = **2.0** ; FI = **4.5**

**Ex. 3** — « We are considering options and will consult… »  
FC = **1.5** ; FI = **0.0**

**Ex. 4** — « The framework establishes procedures… »  
FC = **0.5** ; FI = **0.0**

**Ex. 5** — « We strongly oppose this amendment and urge members to reject it, while supporting alternatives. »  
FC = **3.0** ; FI = **3.5**

---

## Cas difficiles
**Conditionnel** — « If funding is approved, we could expand… » → FC **1.0–1.5**  
**Passé/accompli** — « Measures have been implemented… » → FC **≈1.0**  
**Question rhétorique** — « Why would we not invest… ? » → FC **2.5–3.0**  
**Plusieurs actions** — Annotez la **tendance dominante** ; si équilibré : **moyenne** + note.

---

## Utilisation de `flag_incertain`
Mettez **1** si :
- Hésitation entre deux valeurs
- Extrait ambigu/mal structuré
- Vous pensez que l’autre annotateur pourrait diverger  
Laissez vide si annotation confiante. → Sert à prioriser la **réconciliation**.

---

## Règles importantes
1. **Décimales autorisées** (ex. 3.5)  
2. **Toujours remplir FC ET FI** (mettez 0 si absent)  
3. **Annoter uniquement l’extrait fourni** (pas le document complet)  
4. **En cas de doute** : décimales + `flag_incertain` + note courte  
5. **Verbatim de l’extrait** : ne pas ouvrir la source pour infléchir le score (sauf besoin d’un acronyme)

### Auto-check avant envoi
- [ ] FC et FI remplis  
- [ ] `flag_incertain` si hésitation  
- [ ] Note courte si cas ambigu  
- [ ] Zéro case vide

---

## Contact & transparence
**Contact** : alan.kleden@gmail.com  
**Projet OSF** : https://osf.io/rm42h
