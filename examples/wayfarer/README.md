# Wayfarer

A small top-down adventure built to exercise `gale.sequence`,
`gale.cutscene`, and `gale.quest` together in one coherent story: an
intro cutscene hands off into free-roam play tracked by a quest log,
and the quest's completion hands off into a closing cutscene.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/wayfarer
python main.py
```

## Controls

- Arrow keys / WASD: move (free-roam play only)
- `Enter` / `Space`: confirm -- advance dialogue during a cutscene;
  fight the wolf or report back to the Elder when standing next to
  them during play
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press confirm to start a new session
  (this also (re)builds a fresh `QuestLog`, so playing through again
  after the ending works).
- `IntroCutsceneState`: the Hero walks up to the Elder while the Elder
  switches to a "greeting" pose at the same time, then the Elder
  explains the wolf problem over a couple of lines of dialogue. Input
  only drives the cutscene here -- there is no way to move the Hero
  until it hands off into `PlayState`.
- `PlayState`: free-roam over a small single-screen village clearing.
  Walk into any of the 3 herbs to collect them, walk up to the
  (stationary) wolf and press confirm to defeat it, then walk back to
  the Elder and press confirm to report in. A HUD in the corner shows
  the active quest's title and its current stage's objectives with
  live progress (e.g. `[ ] Collect 2 herbs (1/2)`).
- `VictoryCutsceneState`: triggered automatically the moment the quest
  finishes (via `Quest.on_completed`) -- the Elder thanks the Hero over
  a few more lines, then returns to the title screen.

## What it exercises

- `gale.sequence`: the shared engine everything else here is built on.
  - `Step`/`duration`: `MoveActor` beats complete on their own after a
    fixed time.
  - `Step`/`advance_on_input`: every `Dialogue` beat advances on the
    "confirm" input instead of a timer -- duration-based and
    input-based steps play side by side in the same cutscene.
  - `StepGroup`: both cutscenes open with a `StepGroup` running a
    `MoveActor` and a `SetActorAnimation` at once (the Hero walks over
    while the Elder's pose switches, concurrently, not one after the
    other).
- `gale.cutscene`: `Cutscene` drives both `IntroCutsceneState` and
  `VictoryCutsceneState`, ticking/rendering the Hero and Elder
  `actors` every frame regardless of which beat is active. Beats used:
  `MoveActor` (Hero walks to the Elder in both scenes), `SetActorAnimation`
  (the Elder's "greet"/"thanks" pose swaps), and `Dialogue` (every
  line of story text, speaker box included).
- `gale.quest`: `src/quests.py` registers a `Quest` named
  `wolf_trouble` with two `Stage`s -- stage 1 requires both
  `Objective("herbs_collected", target=2)` and
  `Objective("wolf_defeated", target=1)` (a `Stage`'s default
  `require_all=True`); stage 2 is a single
  `Objective("reported", target=1)`. `PlayState` never reaches into
  the quest's internals to mark anything done -- it just calls
  `QuestLog.notify(key, amount)` from wherever that event actually
  happens (a herb's collision, the wolf's defeat, standing next to the
  Elder), the "game defines what progress means and reports it"
  principle the module is built around. The quest's `on_completed`
  callback (`Wayfarer._on_wolf_trouble_completed`) is what transitions
  the state machine into `victory_cutscene`.
- `gale.state.StateMachine`: `title` -> `intro_cutscene` -> `play` ->
  `victory_cutscene` -> `title`, wired once in `src/Wayfarer.py`. The
  Hero/Elder actors and the `QuestLog` are shared session data reached
  through `state_machine.game`, so the same actor objects a cutscene
  moves are the ones free-roam play (and the next cutscene) go on to
  use.
- `gale.input_handler`/`gale.text.render_text`: bindings and every
  piece of on-screen text (dialogue, the quest HUD, menus), the same
  shape every other example in this repo uses.
- `gale.animation.Animation`: each `Actor`'s `.animation` is a
  single-frame `Animation` standing in for a pose/expression
  ("idle"/"greet"/"thanks"); `SetActorAnimation` swaps it, and
  `Actor.render` draws a small ring around whoever isn't idle so the
  swap is visible without needing real sprite art.

The wolf is intentionally kept stationary -- the point of this example
is demonstrating quest progress reporting, not enemy AI depth (see
`examples/nightwatch` for `gale.ai.steering`/behavior trees put to
work on moving characters).

## Credits

- No image/font/sound assets -- everything is drawn with
  `pygame.draw` primitives.
