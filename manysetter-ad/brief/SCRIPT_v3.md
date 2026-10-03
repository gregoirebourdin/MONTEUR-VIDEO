# ManySetter · Script v3 : la promo complète
### ~75 s · fonctionnalités + ce que ça fait gagner · voix expressive · touche d'humour

**Format du film :** chaque idée passe par deux temps :
- **STOMP** : les mots de la voix claquent à l'écran, en typographie animée, au mot près ;
- **ÉCRAN** : on voit la fonctionnalité dans la vraie interface de l'app, reconstruite en vectoriel.

L'humour reste léger et premium : un clin d'œil par acte, jamais de blague lourde.

| # | Voix (anglais) | Traduction | Ce qu'on voit | Jeu de la voix |
|---|---|---|---|---|
| 1 | Your Reel worked. Manychat sent the link. The lead replied… and then? Nothing. | Ton Reel a marché. Manychat a envoyé le lien. Le lead a répondu… et puis ? Rien. | ÉCRAN : le DM qui meurt, compteur « 2 days ». STOMP final : **« Nothing. »** | Raconté à un ami, petit soupir sur « Nothing » |
| 2 | That's where good leads go quiet. | C'est là que les bons leads disparaissent. | STOMP : **Good leads / go quiet.** (les lettres s'éteignent) puis silence | Bas, posé |
| 3 | Meet ManySetter. It picks up right where Manychat stops. | Voici ManySetter. Il reprend là où Manychat s'arrête. | Le M tracé en lumière, bascule dans la lumière, logo | Sourire, révélation |
| 4 | Give it your sales page, your offer, your FAQ. In about two minutes, it knows what you sell, and how you say it. | Donne-lui ta page de vente, ton offre, ta FAQ. En deux minutes environ, il sait ce que tu vends, et comment tu le dis. | STOMP : **Your sales page. Your offer. Your FAQ.** ÉCRAN : le Playbook « Built from 6 documents », le doc Voice qui s'écrit | Énergie qui monte |
| 5 | Then it replies the moment they finish typing. In your voice. Even at two a.m. You? You're asleep. | Puis il répond dès qu'ils ont fini d'écrire. Avec ta voix. Même à 2 h du matin. Toi ? Tu dors. | ÉCRAN : un DM à **2:07 AM**, réponse immédiate. STOMP humour : **You? You're asleep.** + icône lune, mode « Sleep » | Complice, sourire sur la chute |
| 6 | It asks your questions, handles objections, and only books the leads who fit. | Il pose tes questions, répond aux objections, et ne réserve que les leads qui correspondent. | STOMP : **Asks. Handles. Books.** ÉCRAN : diptyque Emma qualifiée / Alex reçoit le guide, ta règle au centre | Rythmé, sûr |
| 7 | Right in the DM, with a summary waiting in your calendar. | Directement dans le DM, avec un résumé qui t'attend dans ton agenda. | ÉCRAN : créneaux, « Wed 4:30 works! », la carte **Call booked** se retourne | Satisfait |
| 8 | Lead gone quiet? It follows up. Even with a voice note, in your voice. Yes, really. | Le lead ne répond plus ? Il relance. Même avec une note vocale, avec ta voix. Oui, vraiment. | ÉCRAN : relances activées, note vocale qui se joue. STOMP : **Yes, really.** | Petit rire dans « Yes, really » |
| 9 | Every reply is explained. And you can take over in one click. | Chaque réponse est expliquée. Et tu reprends la main en un clic. | ÉCRAN : « Why this reply? » s'ouvre (étape du script, règle utilisée), puis clic sur **Reply myself** | Rassurant |
| 10 | Don't like an answer? Fix it in one sentence. Testing is free. | Une réponse ne te plaît pas ? Corrige-la en une phrase. Les tests sont gratuits. | ÉCRAN : « Tell your setter what to change… » s'écrit, la réponse se met à jour (Before → Updated). STOMP : **One sentence.** | Léger |
| 11 | No setter to hire. No commission. No lead left on read. | Pas de setter à recruter. Pas de commission. Plus aucun lead laissé en « vu ». | STOMP en rafale, chaque phrase barrée puis cochée | Punchy |
| 12 | Sell a fifteen-hundred-dollar offer? One extra client pays for a full year. | Tu vends une offre à 1 500 $ ? Un seul client en plus paie une année complète. | STOMP chiffré : **$1,500 offer** → **1 extra client** = **a full year** (la carte de prix $119/mo apparaît) | Évident, confiant |
| 13 | ManySetter. Turn your Manychat DMs into booked calls. Build yours free, at ManySetter dot com. | ManySetter. Transforme tes DMs Manychat en appels réservés. Crée le tien gratuitement sur ManySetter point com. | CTA : bouton pressé, « No card to start », puis carte de fin, dernier accord | Invitation chaleureuse |

## Les promesses à valider (chacune reprend ton site)

| Phrase | Source sur ton site |
|---|---|
| « In about two minutes » | How it works : *Your playbook is ready in about two minutes* |
| « Replies the moment they finish typing, in your voice » | How it works : *In your voice and their language, once they've finished typing* |
| « Even at two a.m. » | Le setter tourne seul (*It runs on its own*) |
| « Asks your questions, handles objections » | How it works : *Your fit questions… Objections answered from your playbook* |
| « Summary waiting in your calendar » | Calendar : *Writes the lead's summary into the event* |
| « Follows up… voice note, in your voice » | Pricing : *Up to 3 follow-ups per lead, voice notes in your voice* |
| « Every reply is explained » | How it works : *Every reply is explained* |
| « Fix it in one sentence. Testing is free. » | Home : *Fix any reply in one sentence* · *Test messages are free* |
| « No commission » | Prix fixe de 119 $/mois, sans pourcentage sur les ventes |
| « One extra client pays for a full year » | Pricing : *Sell a $1,500 offer? One extra client pays for a full year.* |

Aucun chiffre de résultat inventé (pas de « +X % d'appels »).

## Direction voix (Gemini 3.8, émotion phrase par phrase)

Une seule prise, avec une direction propre à chaque phrase : `speech_metadata.style` par segment, plus les
balises `<sigh>`, `<short pause>`, `<long pause>` et `<chuckle>` là où elles servent le jeu. Casting n° 2 sur
les lignes 1, 5 et 8 (accroche, humour, « Yes, really ») avec : `en-us-training-5`,
`en-us-storyteller-14`, `en-us-commercial-3`, `en-us-brio` et Charon rejoué.
