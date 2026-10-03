"""Kinetic type spec for the v7 film: every spoken word is written on screen, on its cue.

One scene per script part (P1..P9). A scene is a list of beats; a beat is one phrase on screen.
The words of a part's beats, in order, must be exactly the words of that part in timing.json
(build.py checks it), so the text can never drift from the voice.

Beat text syntax
  word            plain word, appears on its own cue
  *word           accent colour
  _word           soft colour
  word!slam       punchy entrance (scale + blur), !pop (spring), !soft (blur-fade), !count (number roll)
  {a b}~o         hand-drawn oval around a group of words (~u = underline)
  |               line break
  [[shown||spoken words]]  display text that stands for several spoken words

Beat keys
  pos   left | center | top | bottom          (text block placement; UI lives in the other space)
  size  font size in px
  fx    default entrance for the beat's words: rise (masked rise) | slam | pop | soft
  ui    True: the words are written by the scene's own UI (a chat bubble, a tile...), no type layer
  out   exit time override in film seconds ("hold" = stays until the scene ends)
"""

SCENES = [
    {
        "id": "s1",
        "part": "P1",
        "theme": "dark",
        "beats": [
            {"t": "I posted a *Reel.", "pos": "left", "size": 128},
            {"t": "Boom,!slam | it blew up.", "pos": "left", "size": 128},
            {"t": "Manychat sent | the links,", "pos": "left", "size": 112},
            {"t": "and I got…", "pos": "left", "size": 128},
            {"t": "*126!count | DMs!!slam", "pos": "center", "size": 260, "fx": "slam", "cls": "kt-tight"},
            {"t": "How am I supposed | to pitch my offer | to all of them?", "pos": "center", "size": 112},
            {"t": "It's!slam *9!slam *p.m.!!slam", "pos": "center", "size": 220, "fx": "slam"},
        ],
    },
    {
        "id": "s2",
        "part": "P2",
        "theme": "dark",
        "beats": [
            {"t": "If I reply too *late, | they'll forget me!", "pos": "left", "size": 112},
            {"t": "So all of that… | for nothing?!sink", "pos": "center", "size": 150},
        ],
    },
    {
        "id": "s3",
        "part": "P3",
        "theme": "dark",
        "beats": [
            {"t": "Quick,!slam | I need to hire | a *setter.", "pos": "left", "size": 120},
            {"t": "But I have to | train them, | pay them | commission…", "pos": "left", "size": 104},
            {"t": "and what if | they reply with | total *cringe like", "pos": "left", "size": 104},
            {"t": "Hey babe! Ready to ten-x your life?", "ui": True},
            {"t": "Uh…!pop | *no.!slam", "pos": "left", "size": 200},
        ],
    },
    {
        "id": "s4",
        "part": "P4",
        "theme": "dark",
        "beats": [
            {"t": "Wait… | what's this?", "pos": "top", "size": 92, "fx": "soft", "out": 30.78},
            {"t": "ManySetter?", "ui": True},
            {"t": "An *AI setter | that plugs into | my Manychat…", "pos": "left", "size": 108, "theme": "light"},
            {"t": "and talks exactly | {like me?}~o", "pos": "left", "size": 108, "theme": "light"},
        ],
    },
    {
        "id": "s5",
        "part": "P5",
        "theme": "light",
        "beats": [
            {"t": "Okay,!pop | let's try.", "pos": "center", "size": 150},
            {"t": "I give it | my *sales page…", "pos": "left", "size": 112},
            {"t": "two minutes later,", "pos": "left", "size": 112},
            {"t": "it knows my offer | {by heart.}~u", "pos": "left", "size": 112},
            {"t": "It answers | every DM,", "pos": "left", "size": 112},
            {"t": "handles the | “I need to | think about it”", "pos": "left", "size": 104},
            {"t": "and when | someone's a *fit,", "pos": "left", "size": 112},
            {"t": "it *books | the call.", "pos": "left", "size": 128},
            {"t": "Right in | the {DM.}~o", "pos": "left", "size": 128},
            {"t": "Wait…!soft | seriously?!slam", "pos": "center", "size": 170},
        ],
    },
    {
        "id": "s6",
        "part": "P6",
        "theme": "light",
        "beats": [
            {"t": "Oh, and it's | *sneaky.!pop", "pos": "center", "size": 160},
            {"t": "It waits a beat | before replying…", "pos": "left", "size": 104},
            {"t": "like a real | *human would.", "pos": "left", "size": 112},
            {"t": "Every lead gets | an *AI summary,", "pos": "left", "size": 104},
            {"t": "so I know exactly | who I'm calling.", "pos": "left", "size": 104},
            {"t": "And my | sales team?", "pos": "left", "size": 112},
            {"t": "They get | the *stats.", "pos": "left", "size": 112},
            {"t": "Conversations, qualified leads, calls booked.", "ui": True},
        ],
    },
    {
        "id": "s7",
        "part": "P7",
        "theme": "light",
        "beats": [
            {"t": "Next morning.", "pos": "center", "size": 160, "fx": "soft"},
            {"t": "Coffee in hand…", "pos": "center", "size": 150},
            {"t": "and the calls | are already | in my *calendar.", "pos": "left", "size": 108},
            {"t": "No setter.!slam | No commission.!slam", "pos": "left", "size": 120, "fx": "slam"},
            {"t": "And it still | sounds {like me.}~o", "pos": "left", "size": 120},
        ],
    },
    {
        "id": "s8",
        "part": "P8",
        "theme": "light",
        "beats": [
            {"t": "Got a *Reel | coming up?", "pos": "center", "size": 150},
            {"t": "Build your setter | for *free.", "pos": "top", "size": 120},
            {"t": "No card.!pop", "pos": "bottom", "size": 72, "fx": "pop", "style": "bottom: 250px"},
            {"t": "If your program's | [[$1,500,||fifteen hundred bucks,]]", "pos": "left", "size": 112},
            {"t": "one new client | pays for | the {whole year.}~u", "pos": "left", "size": 112},
        ],
    },
    {
        "id": "s9",
        "part": "P9",
        "theme": "light",
        "beats": [
            {"t": "ManySetter.", "ui": True},
            {"t": "Your DMs on *autopilot… | in your {voice.}~u", "pos": "bottom", "size": 92, "style": "bottom: 262px", "out": "hold"},
            {"t": "ManySetter dot com.", "ui": True},
        ],
    },
]
