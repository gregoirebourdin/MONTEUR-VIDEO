# ManySetter : « Silence → Booked »
### Brief de la pub promo · v1 · à valider avant production

> **Statut :** brief et casting voix envoyés. Rien n'est construit tant que tu n'as pas dit **GO** et choisi la voix.

---

## 0. Le prompt maître (version ManySetter du template)

```
Fais-moi une pub pour ManySetter (www.manysetter.com), l'AI setter pour Manychat.

- Référence : le site lui-même. Même ADN visuel : crème chaud, orange #ff611d → #e64b15,
  Nohemi SemiBold serré pour les titres, Inter pour l'UI, l'ovale orange dessiné à la main
  autour du mot-clé, lignes pointillées orange, bulles de chat, sections sombres à halo orange.
- Message : les leads Manychat meurent après le premier DM. ManySetter reprend la
  conversation, qualifie et réserve l'appel dans le DM.
- Script : tu l'écris, en phrases complètes et claires, compréhensibles sur un haut-parleur
  de téléphone. Aucun chiffre de résultat inventé (« +X % d'appels » est interdit : le site
  lui-même dit qu'aucun outil ne peut promettre un nombre d'appels).
- Voix : Gemini 3.8 Flash TTS. Je choisis parmi 6 voix. Chaque prise est vérifiée mot à mot
  par transcription avant usage. Les noms de marque doivent être bien prononcés.
- Durée : ~35 s + carte de fin 2,5 s. Master 16:9 1920×1080 + version 9:16 1080×1920
  recomposée (pas recadrée), 60 fps.
- À éviter : faux visages, photos stock, iPhone en 3D cheap, stats inventées, logos
  approximatifs, texte coupé sur mobile, transitions génériques.

RÈGLES PERMANENTES
LOOK : vraies UI rebâties à l'identique depuis les maquettes officielles du site (même
texte, mêmes couleurs, mêmes polices). Logos officiels uniquement. Scène sombre → bascule
dans la lumière crème/orange de la marque. Kinetic type + couche motion design constante.
Flou de mouvement sur tous les déplacements rapides.
SON : musique originale codée, arrangée autour de la voix (≥ 15 dB sous la VO pendant les
mots). Design sonore dense : whoosh avant chaque titre, impact sur chaque arrivée, un son
sur chaque mouvement d'UI et sur le logo. Master -14 LUFS / -1 dBTP.
QA : zéro bug. Lint + validation runtime HyperFrames, planche contact, détection frames
noires / gelées, texte dans la zone sûre, VO vérifiée mot à mot, loudness mesurée.

ORDRE : brief → OK · voix → choix · preview v1 16:9 + planche → retours · finals 16:9 +
9:16 + stems + README.
```

---

## 1. Le concept

**Le DM qui reste sans réponse.** On ouvre dans le noir, sur une conversation Instagram
qui meurt : le Reel a marché, Manychat a envoyé le lien, le lead répond… et personne ne
répond. Un compteur « Pas de réponse · 2 jours » défile, la bulle se décolore et s'éloigne.
La musique se coupe net sur « quiet » : une vraie demi-seconde de silence.

Puis le « M » du logo se dessine en lumière orange dans le noir, et toute la scène bascule
dans l'univers crème et orange du site. **Le noir, c'est le lead perdu. La lumière, c'est
l'appel réservé.** Trois preuves produit, une promesse de contrôle, un CTA sans risque.

**Pourquoi ça marche :** la cible (coachs, consultants, agences Manychat) a vécu ce silence
cent fois. On ouvre sur *leur* douleur, pas sur notre logo.

## 2. Les arguments mis en avant (dans cet ordre)

| # | Argument | Pourquoi c'est le bon | Source |
|---|---|---|---|
| 1 | Les bons leads meurent après le 1er DM | La douleur exacte, celle qui coûte de l'argent | Section « The problem » |
| 2 | Il apprend ton offre **et ta voix** | Lève l'objection n°1 : « une IA, ça sonne robot » | « Your leads hear your brand » |
| 3 | Il qualifie avec **tes** règles | Protège l'agenda des curieux ; le non-qualifié reçoit quand même une réponse utile | « Only the right leads get your calendar » |
| 4 | Il réserve l'appel **dans le DM** | Le résultat final, sans lien à cliquer (Cal.com, Calendly, iClosed) | Section « Calendar » |
| 5 | Tu gardes tes flows Manychat, tu reprends la main quand tu veux | Zéro friction, zéro perte de contrôle | « Keep what you built » + FAQ |
| 6 | Gratuit pour construire et tester, sans carte | Zéro risque pour essayer | Hero + Pricing |
| ★ | « Testé par 100+ agences marketing » | Preuve sociale (à l'écran, pas en voix) | Hero |

## 3. Script voix (anglais, comme le site) · ~80 mots · ~35 s

> *« Instagram Reel » plutôt que « Reel » seul : à l'oral, « Reel » se confond avec « real ». La transcription de contrôle l'a entendu ainsi sur une des voix.*

> **Langue :** je recommande l'**anglais** : ton site, tes prix en $ et ton marché sont en anglais.
> Une version française est possible ensuite (Gemini parle très bien français), dis-le-moi.

| # | VO (anglais) | Traduction |
|---|---|---|
| 1 | Your Instagram Reel worked. Manychat sent the link. The lead replied… and then, nothing. | Ton Reel Instagram a marché. Manychat a envoyé le lien. Le lead a répondu… et puis, rien. |
| 2 | That's where good leads go quiet. | C'est là que les bons leads disparaissent. |
| 3 | Meet ManySetter. The AI setter for Manychat. | Voici ManySetter. Le setter IA pour Manychat. |
| 4 | It learns your offer and your voice, so every reply sounds like you. | Il apprend ton offre et ta voix : chaque réponse sonne comme toi. |
| 5 | It qualifies every lead with your rules. Only the right ones get your calendar. | Il qualifie chaque lead avec tes règles. Seuls les bons accèdent à ton agenda. |
| 6 | Then it books the call, right in the DM. | Puis il réserve l'appel, directement dans le DM. |
| 7 | Keep your Manychat flows. Take over anytime. | Garde tes flows Manychat. Reprends la main quand tu veux. |
| 8 | Build and test your setter for free, at ManySetter dot com. | Crée et teste ton setter gratuitement, sur ManySetter point com. |

Variante CTA possible (argument ROI de ta page Pricing) : *« Sell a $1,500 offer? One extra client pays for the year. »* (+4 s).

## 4. Découpage minuté (16:9) · re-calé sur la vraie voix après le choix

| Temps | Scène | Ce qu'on voit | Motion / transitions | Son |
|---|---|---|---|---|
| 0:00–0:03 | **Le Reel marche** | Scène sombre. Notif « @sarah.coach commented: GUIDE », puis bulle Manychat « Thanks for the comment! Here's your link. » | Pop-in des bulles, léger travelling | Drone grave, tic d'horloge ; pop + blip message |
| 0:03–0:05 | **Le lead répond** | Points de saisie, puis « Thanks! Does it work for beginners? » | Points de saisie qui se transforment en bulle | Tap clavier, blip reçu |
| 0:05–0:07 | **…et puis rien** | Les points côté marque apparaissent… puis s'éteignent. Compteur « No reply · 2h → 1 day → 2 days ». La bulle se décolore et coule hors du point. | Défocus progressif, compteur qui roule | Counter, souffle, la musique se vide |
| 0:07–0:09 | **Kinetic** | **GOOD LEADS / GO QUIET.** Les lettres de « QUIET » s'éteignent une à une | Slam-in, puis fondu lettre par lettre | Impact, puis **silence total 0,4 s** |
| 0:09–0:12 | **Le réveil** | Le « M » du logo se dessine en trait de lumière orange, la tuile se remplit, un halo envahit l'écran, bascule crème. Wordmark + chip « The AI setter for Manychat » | Tracé SVG, bloom, wipe lumineux | Riser, **sting logo**, drop musical |
| 0:12–0:17 | **Preuve 1 : il apprend** | Titre « Your leads hear (your brand) », ovale dessiné. 4 cartes sources (Sales page, Offer doc, FAQ, Instagram posts) aspirées dans le panneau setter, chip vert « Learned ». Lignes qui s'écrivent : *12-week program · $1,500*, *Coaches with 2 to 10 clients*. Curseurs de ton : *Warm · direct · short* | Ovale tracé, cartes en vol + flou de mouvement, typewriter | Whoosh par carte, tick par ligne, swoosh de l'ovale |
| 0:17–0:22 | **Preuve 2 : il qualifie** | Écran partagé. Emma (Instagram) : « Five. Most leads never reach a call. » → chip vert « Fits 2–10 clients · qualified ». Alex (WhatsApp) : « I'm just starting out. » → « Free guide sent instead of a call ». Titre « Only the right leads get (your calendar) » | Split animé, porte de qualification, chips qui claquent | Snap, success léger, tick |
| 0:22–0:26 | **Preuve 3 : il réserve** | Scène sombre à halo orange (comme le site). Tuiles Cal.com / Calendly / iClosed reliées en pointillés orange à la pilule « Your setter · Finds a time that works ». « I've got Wed 4:30 PM or Thu 11 AM. Which works? » → « Wed 4:30 works! » → carte **Call booked · Discovery call · 30 min**, notes cochées | Pointillés qui courent, flip de carte | Blips, **chime de réservation**, ticks des notes |
| 0:26–0:29 | **Tes flows + le contrôle** | « Keep what you built. (Add the setter.) » Icônes Instagram / WhatsApp / Messenger en orbite autour du setter. Interrupteur « AI → Your team » | Orbite, toggle | Switch, whoosh |
| 0:29–0:33 | **CTA** | Fond sombre, halo orange (section finale du site). Bouton « Build my setter free → » qui s'enfonce. ✓ Free to build and test · ✓ No card to start · ✓ 14-day trial. Chip « Tested by 100+ marketing agencies ». **manysetter.com** | Punch-in sur le bouton, ticks en cascade | Clic, ticks, montée finale |
| 0:33–0:35,5 | **Carte de fin** | Logo + « Turn Manychat DMs into booked calls. » Mention légale discrète : *not affiliated with Manychat or Meta* | Respiration lente | Dernier accord qui résonne |

**Version 9:16 :** mêmes scènes recomposées en vertical (UI empilée, titres sur 2-3 lignes, tout dans les 80 % centraux de la largeur, rien dans le tiers bas réservé aux interfaces Reels/TikTok).

## 5. Direction visuelle

- **Palette** (extraite du CSS du site) : crème `#fdfcfb` / `#f5f3f2`, encre `#111111`, orange `#ff611d` → `#e64b15`, dégradé logo `#ff884d → #e64b15`, vert validation `#00bb7f`, scène sombre `#0f0d0c` + halo orange.
- **Typo** : Nohemi SemiBold (titres du site, interlettrage serré −0,04 em), Inter (UI).
- **Signatures empruntées au site et animées** : l'ovale orange dessiné à la main, le soulignement-swoosh, les connecteurs pointillés orange, la pilule « Your setter » à point vert, les cartes d'UI au contour fin.
- **Nouveaux mouvements** (jamais vus dans l'autre pub) : bulle qui se décolore et coule, lettres qui s'éteignent, logo tracé en lumière, aspiration des sources, porte de qualification, carte qui flippe.
- Grain très léger et halo orange qui dérive doucement pour que rien ne soit jamais statique.

## 6. Son

- **Voix** : Gemini `gemini-3.8-flash-tts`, style en métadonnées (jamais lu à voix haute), vérifiée mot à mot par whisper.
- **Musique** : composée en code (Python), ~98 BPM. Acte 1 : drone et pulsation sourde. Coupure nette sur « quiet ». Acte 2 : nappe chaude majeure, arpège pluck, groove léger, montée jusqu'au CTA, accord final qui résonne. Toujours ≥ 15 dB sous la voix.
- **SFX** : les 9 sons du kit (pop, tick, counter, chime, snap, star, switch, fill, success) + whooshes, risers, impacts, blips de message et sting logo synthétisés en code (aucune licence à gérer).
- **Master** : -14 LUFS intégrés, -1 dBTP. Stems séparés : voix / musique / SFX.

## 7. Liste d'assets (rien à télécharger chez des tiers)

| Asset | Source | Statut |
|---|---|---|
| Logo (icon.svg, icon-512.png) | manysetter.com (officiel) | ✅ récupéré |
| Polices Nohemi 500/600 | manysetter.com (polices du site) | ✅ récupéré |
| Police Inter 400/700 | kit du tuto (OFL) | ✅ récupéré |
| Logos Instagram / WhatsApp / Messenger / Cal.com / Calendly / iClosed | SVG intégrés au site lui-même | à extraire du site |
| Maquettes UI (chat, setter, agenda) | rebâties en HTML/CSS depuis les captures du site | captures faites (`research/`) |
| SFX | kit (9) + générés en code | ✅ kit copié |
| Musique | composée en code | à faire |
| Photos / visages | **aucun** (avatars à initiales, comme sur le site) | n/a |

**Optionnel mais recommandé :** 2 ou 3 vraies captures de ton app (dashboard, réglages du setter). Je peux en faire une scène « vrai produit ». Sans elles, je reste sur les maquettes officielles du site.

## 8. Livrables

- `renders/manysetter_16x9.mp4` : 1920×1080, 60 fps, H.264, AAC 48 kHz
- `renders/manysetter_9x16.mp4` : 1080×1920, 60 fps
- `renders/stems/` : vo.wav, music.wav, sfx.wav
- `renders/contact_sheet.png` + `README.md`

## 9. Contrôle qualité (« aucun bug »)

1. VO : transcription whisper comparée mot à mot au script, aucune prise non conforme n'est utilisée.
2. `hyperframes lint` + `validate` (erreurs JS, assets manquants, contraste) + `inspect` (débordements de texte).
3. Planche contact à chaque version ; vérification de la zone sûre en 9:16.
4. ffmpeg `blackdetect` / `freezedetect` : aucune frame noire ou gelée non voulue.
5. ffprobe : résolution, 60 fps, durée, synchro audio/vidéo.
6. Loudness mesurée : -14 LUFS ±0,5, true peak ≤ -1 dBTP.
