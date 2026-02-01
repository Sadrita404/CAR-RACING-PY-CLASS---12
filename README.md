# CAR RACING GAME  🚗

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
# Architecture 
<img width="1101" height="1358" alt="diagram-export-02-02-2026-01_59_59" src="https://github.com/user-attachments/assets/22307ce7-8ae6-4883-9b85-be4dcf861435" />

___
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
# Gme Overview 
<img width="1362" height="749" alt="Screenshot 2026-02-02 at 2 06 18 AM" src="https://github.com/user-attachments/assets/b65426f0-6027-4563-98e3-7cbf17c0afd3" />

<img width="1362" height="744" alt="Screenshot 2026-02-02 at 2 06 27 AM" src="https://github.com/user-attachments/assets/e0d512e7-0f09-49ab-9052-e24dea2c802c" />

<img width="1364" height="751" alt="Screenshot 2026-02-02 at 2 06 53 AM" src="https://github.com/user-attachments/assets/cbb38586-8e77-4e29-a151-76320f1d7278" />

<img width="1375" height="746" alt="Screenshot 2026-02-02 at 2 07 30 AM" src="https://github.com/user-attachments/assets/43d37ca9-605e-47c2-913f-8605a82b992c" />

---
# SQLite (built into Python stdlib)

<img width="1109" height="746" alt="Screenshot 2026-02-02 at 1 15 05 AM" src="https://github.com/user-attachments/assets/155c51fd-4804-4fa3-a290-fe5bd06de8ef" />

<img width="850" height="427" alt="Screenshot 2026-02-02 at 1 33 14 AM" src="https://github.com/user-attachments/assets/7ab76aa6-ca64-442c-a633-67038ab5e170" />

<img width="518" height="626" alt="Screenshot 2026-02-02 at 1 13 33 AM" src="https://github.com/user-attachments/assets/4f2d3225-6b96-4218-8e3f-cf531b5f77a9" />


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

