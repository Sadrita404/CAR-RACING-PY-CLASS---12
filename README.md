# off_mult_game 🚗

**A lightweight offline multiplayer racing game (Pygame).**

---

## Project structure

```
off_mult_game/
├── racing game.py         # Main game script (pygame)
├── show_race_data.py     # Utility: prints / exports race_results from racing_data.db
├── setup.py               # Installer / packaging helper
├── package-lock.json      # Lockfile (if any node tooling used)
├── racing_data.db         # SQLite DB storing race_results
├── results.csv            # Example CSV export
├── f1.png                 # Car sprite: F1
├── nascar.png             # Car sprite: NASCAR
├── lemans.png             # Car sprite: Le Mans
├── super.png              # Car sprite: Super car
├── drift.png              # Car sprite: Drift car
├── tree.png               # Scenery asset
├── eng_v10.wav            # Sound assets (engine etc.)
├── eng_w16.wav
├── eng_v8.wav
├── eng_v6.mp3
├── start.wav
├── crash.mp3
└── skid.wav
```

---

## Quick start ⚡

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Run the game:

```bash
cd "$(pwd)"
python3 "racing game.py"
```

3. View/export race results (utility):

```bash
# Print results (all)
python3 show_race_data.py

# Print recent 20
python3 show_race_data.py --limit 20

# Export results to CSV
python3 show_race_data.py --csv results.csv
```

4. Inspect the database directly (optional):

```bash
sqlite3 racing_data.db ".tables"
sqlite3 -header -column racing_data.db "SELECT * FROM race_results ORDER BY date DESC LIMIT 20;"
```

Or use a GUI like *DB Browser for SQLite* (`brew install --cask db-browser-for-sqlite` on macOS).

---

## Requirements / Dependencies ✅

- Python 3.8+
- pygame (see `requirements.txt`)
- SQLite (built into Python stdlib)

---

## Notes & Tips 💡

- `racing_data.db` is created/updated by the game; `show_race_data.py` reads it and can export CSV.
- If you want the results shown in-game, I can add a small UI panel to `racing game.py`.

---

## Contributing

Feel free to open issues or PRs. If you want, I can add a simple CI test and a proper setup workflow.

---

## License

MIT License

