#!/usr/bin/env python3
"""show_race_data.py — Print race results from racing_data.db

Run:
  python3 show_race_data.py [--limit N] [--csv FILE]

Examples:
  python3 show_race_data.py --limit 20
  python3 show_race_data.py --csv results.csv

"""

import sqlite3
import os
import argparse
import sys
import csv

DB_FILE = "racing_data.db"


def fetch_results(db_path, limit=None):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='race_results';")
    if not cur.fetchone():
        print("No table 'race_results' found in database.")
        conn.close()
        return []
    query = "SELECT id, winner_name, car_type, lap_time, date FROM race_results ORDER BY date DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return rows


def print_table(rows):
    if not rows:
        print("No results to show.")
        return
    headers = ["id", "winner_name", "car_type", "lap_time", "date"]
    # compute column widths
    widths = [len(h) for h in headers]
    for r in rows:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], len(str(v)))
    sep = ' | '
    header_line = sep.join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    print(header_line)
    print('-' * len(header_line))
    for r in rows:
        print(sep.join(str(r[i]).ljust(widths[i]) for i in range(len(headers))))


def export_csv(rows, path):
    """Export rows to CSV at `path`. Overwrites existing file."""
    try:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "winner_name", "car_type", "lap_time", "date"]) 
            for r in rows:
                writer.writerow(r)
        print(f"Exported {len(rows)} row(s) to {path}")
    except Exception as e:
        print(f"Failed to export CSV: {e}")


def main():
    parser = argparse.ArgumentParser(description='Show racing game results from racing_data.db')
    parser.add_argument('-n', '--limit', type=int, help='Limit number of rows (most recent)')
    parser.add_argument('-o', '--csv', dest='csv', help='Export results to CSV file (path)')
    args = parser.parse_args()

    rows = fetch_results(DB_FILE, args.limit)
    if args.csv:
        export_csv(rows, args.csv)

    print(f"Showing {len(rows)} result(s) from {DB_FILE}\n")
    print_table(rows)


if __name__ == '__main__':
    main()
