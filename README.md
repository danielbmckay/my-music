# Equality Music

Independent record label founded by Danny McKay. Represents all cultures and all people.

## Roster

| Project | Artist | Description |
|---------|--------|-------------|
| **'89 Vision** | Danny Boy | Public/world-facing project — 7 albums, 64 tracks |
| **AA Audible** | Danny McKay | Faith and reflection — 4 albums, 8 tracks |

## The 10 Core Songs

These songs made it through the full creative pipeline — from iPhone freestyle to written lyrics to Ableton production to mastered release to branded artwork. Present in all 5 sources (Voice Memos, Apple Notes, Ableton, eMastered, Canva):

1. **It Hurts** — the magnum opus, full lyrics + vocal dynamics + multiple raw takes
2. **'89 Vision** — the title track, letter to dad
3. **Muzak** — the musical influences tribute
4. **My Baby** — for Danielle
5. **Starfighter** — air traffic control motif, Danny is the Starfighter
6. **The Sea** — spiritual metaphor, love as the ocean
7. **The Way** — recovery and faith
8. **The Beginning** — faith, the psychiatric hold, giving it all away
9. **Satellite** — wounded satellite, '89 Vision connection
10. **Sandy Eggo** — San Diego, for the kids

## The Creative Pipeline

```
Voice Memo (iPhone) → Apple Notes (lyrics) → Ableton (production) → eMastered (mastering) → Canva (artwork)
```

## Discography

### '89 Vision

| Album | Tracks |
|-------|--------|
| **'89 Vision** | '89 Vision (Reggae), Starfighter |
| **Free Style** | Above The Clouds, Bee Kind (Remixed), Chimes, FTW, Jain, Rainy Daze |
| **Feels** | Floating, Flyin', For Real (Proof), Freaks, Fresh — each with vocal + instrumental |
| **Sunny Daze** | Baby Girl, The Thing, Trapped, Where Do We Go? — plus alternates/remasters |
| **Birds Eye** | Muzak My Baby, The Starfighter's Satellite (feat. Luca The Legacy), The Way to The Sea |
| **Cover Up** | Creep (Acoustic) |
| **Instrumental** | 19 instrumentals — the production catalog |

Plus 16 extras not on any album.

### AA Audible

| Album | Description |
|-------|-------------|
| **My Savior** | Scripture-based tracks — Praise, Psalm 1, Psalm 124, Truth |
| **My Religion** | In progress |
| **My Testimony** | In progress |
| **Reflections** | Personal journal entries — 4-15-2024, Daily Reflection 8-13-24 |

## Album Plans vs Reality

- **'89 Vision, Free Style, Cover Up, Bird's Eye, Sunny Daze, Instrumental** — all planned in Notes AND released on eMastered. Plans matched reality almost exactly.
- **Quality Music (Demo)** — absorbed into '89 Vision album (all 6 tracks landed there)
- **Feels** — released on eMastered but NOT planned in Notes (iLLPeTiLL collaboration emerged separately)
- **My Savior, My Religion, My Testimony, Reflections** — AA Audible albums, released on eMastered with full Canva artwork, but no Notes album plans for these

## Unreleased Concepts

23 tracks exist as written lyrics/concepts in Apple Notes but were never produced:

- **Starfighter concept (8):** Pops, Blue Dream, Blucifer, Dominoes, Blue AF, The Tower, God Is Good, Reds
- **Sandy Eggo concept (12):** Freedom, Inspire Me, Brotherly, Scarlet, Grow Happiness, Skylar, Strong, Raising Myself, Austin, Arielle, Frankenstein, Legacy
- **Forever concept (1):** Easy Coast
- **The Sea concept (2):** Psalm 91, Bread

## Content Inventory

| Source | Total | Matched | Orphaned | Notable Orphans |
|--------|-------|---------|----------|-----------------|
| eMastered | 40 tracks | 100% | 0% | Everything released has at least one other source |
| Voice Memos | 126 | 48% | 52% | Mostly practice (14 Frets series), fragments, unreleased covers |
| Apple Notes | ~55 titles | 58% | 42% | All 23 unreleased concept tracks |
| Ableton | 81 sessions | 68% | 32% | Experimental: Butterfly, Etherial, Mary Jane, Road Monger |
| Canva | 148 pages | 88% | 12% | Photo/promo pages |

## Repo Structure

```
My Music/
├── 89 Vision/          # '89 Vision catalog — albums, extras, per-song metadata
│   ├── Albums/         # Track .md files organized by album
│   └── Extras/         # Tracks not on any album
├── AA Audible/         # AA Audible catalog — same structure
│   └── Albums/
├── Tools/              # Python helper scripts (Ableton parser, audio analysis, etc.)
├── CLAUDE.md           # Label info, conventions, tool references
└── README.md
```

Audio files (.aif), Ableton sessions (.als), voice memos (.m4a), and samples are stored locally but excluded from git. Each song has a `.md` file with metadata (key, BPM, sample sources) and lyrics where available.

## Musical Inspirations

Bob Marley and Bradley Nowell (Sublime)
