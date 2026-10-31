# 🚀 Space Werewolf - Among Us Simplified Version

> A turn-based strategy deduction game inspired by Among Us, built with Python Tkinter.
> Supports single-device play (4-10 players) and **LAN multiplayer** (4-10 players).

[![English](https://img.shields.io/badge/README-English-blue.svg)](README.en.md)
[![简体中文](https://img.shields.io/badge/README-简体中文-red.svg)](README.zh-CN.md)

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-LGPL--2.1-yellow.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.0.0-brightgreen.svg)]()

---

A Space Werewolf tabletop game developed with Python Tkinter, supporting single-device play (4-10 players) and LAN multiplayer (4-10 players).

## Game Introduction

**Space Werewolf** is a turn-based strategy deduction game inspired by the classic game Among Us. Players are assigned to two roles: **Crewmate** or **Impostor**, engaging in a tense and thrilling battle of survival and deception aboard a spaceship.

Created by three Chinese middle school students. We have very limited time, please stay tuned for future updates.

## Game Rules

### Role Assignment

| Player Count | Impostor Count |
|:------------:|:--------------:|
| 4-6 players  | 1 Impostor     |
| 7-10 players | 2 Impostors    |

### Victory Conditions

**Crewmate Victory:**
- Complete all regular tasks (each crewmate needs to complete 3 tasks)
- Vote out all impostors

**Impostor Victory:**
- Impostor count equals crewmate count (with at least one player eliminated)
- Crew fails to repair within the time limit after oxygen system is sabotaged

## Game Interface

### Mode Selection Lobby (Added in v2.0.0)
- **Single Player**: the original same-screen turn-based mode
- **Create Room**: shows the local LAN IP and waits for other players
- **Join Room**: enter the host's IP and your own name to connect

### Role Viewing
- Display player name and role (Crewmate/Impostor)
- Role-specific tips
- Task count display (crewmates only)

### Main Game Interface
- **Top Status Bar**: Global round number, action steps, emergency meeting count, cooldown status
- **Left Map**: Spaceship map, click to move
- **Right Info Panel**: Current player info, task progress
- **Bottom Log**: Game event records

## Core Features

### Movement System
- 4 action steps per round
- Click rooms on the map to move
- Can only move to adjacent rooms

### Task System (Crewmates)
Crewmates need to complete 3 regular tasks:

| Task Name | Location | Difficulty |
|:----------:|:--------:|:----------:|
| Fix Wires | Electrical | ★ |
| Clean Filter | Oxygen | ★ |
| Body Scan | Medbay | ★★ |
| Download Data | Communications | ★★ |
| Calibrate Engines | Engine | ★★ |
| Repair Reactor | Reactor | ★★★ |
| Fuel Engines | Fuel | ★★ |
| Start Satellite | Security | ★★★ |
| Submit Code | Admin | ★★★ |

### Bomb System (Impostors) - Added in v1.1.0

**Place Bomb:**
- Impostors can place bombs in any room
- Consumes 1 action step
- Placement cooldown: 5 rounds (150 seconds in multiplayer)
- Bomb countdown: 3 minutes in single player (independent real-time timing); 60 seconds in multiplayer

**Bomb Explosion Effects:**
- Kills all crewmates in the room where bomb explodes (impostors unaffected)
- Explodes in Oxygen → Triggers oxygen repair task
- Explodes in Security → Triggers security camera repair task
- Explodes in Spaceship Hall → Disables emergency meeting for 2 rounds

**Defuse Bomb Task:**
- Crewmates can defuse bombs when in a room with a bomb
- Cut 4 wires in correct order
- 30-second countdown, explosion on wrong cut or timeout

### Ruin Cleaning System - Added in v1.2.0

**Ruin Generation:**
- Bomb explosions cause the room to become ruined
- Ruined rooms cannot execute normal tasks
- 🏚️ marker displayed on map

**Clean Ruins:**
- Crewmates must click "Clean Ruins" button in ruined rooms
- Drag debris into trash can to complete cleaning
- Room functions restored after cleaning
- Cannot initiate emergency meeting when Spaceship Hall is ruined

## Multiplayer Features - Added in v2.0.0

### Connection Protocol
- TCP-based room lobby system
- Host displays local LAN IP for other players to connect
- Automatic player sync and state broadcast

### Game Synchronization
- Real-time task completion sync across all players
- Vote results and elimination sync
- Bomb placement and explosion sync
- Movement tracking for all players

## Installation & Running

### Prerequisites
- Python 3.11 or higher
- Tkinter (usually included with Python)

### Running the Game

**Single Player Mode:**
```bash
python main_gui.py
```

**Multiplayer Mode:**
```bash
# Host (Create Room)
python impostor_entry.py  # or crewmate_entry.py

# Client (Join Room)
python impostor_entry.py  # or crewmate_entry.py
```

## License

This project is licensed under LGPL-2.1 License.

---

*[Back to Home](README.en.md) | [回到首页](README.zh-CN.md)*