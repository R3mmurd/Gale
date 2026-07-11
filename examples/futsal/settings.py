"""
Futsal: a small 3-vs-3 indoor-soccer simulation built to exercise
gale.ecs (World/System/SystemScheduler manage the ball, the players'
positions/velocities, and their fatigue in a data-oriented way) and
gale.ai (behavior_tree + a shared blackboard coordinate each team,
steering behaviors turn a role's decision into a desired velocity).
Every visual is drawn with pygame.draw primitives, so it needs no
image/font/sound assets to run.
"""

import pygame

from gale import input_handler

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")

# Size we want to emulate
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 360

# Size of our actual window
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540

# The court fits entirely on screen (no camera needed): a rectangle
# inset from the virtual screen's edges, with a goal mouth centered on
# its left and right edges.
COURT_LEFT = 40
COURT_RIGHT = VIRTUAL_WIDTH - 40
COURT_TOP = 40
COURT_BOTTOM = VIRTUAL_HEIGHT - 40
COURT_CENTER_X = (COURT_LEFT + COURT_RIGHT) / 2
COURT_CENTER_Y = (COURT_TOP + COURT_BOTTOM) / 2

GOAL_HALF_HEIGHT = 40
GOAL_Y_TOP = COURT_CENTER_Y - GOAL_HALF_HEIGHT
GOAL_Y_BOTTOM = COURT_CENTER_Y + GOAL_HALF_HEIGHT
GOAL_DEPTH = 14

BALL_RADIUS = 5
PLAYER_RADIUS = 9
POSSESSION_MARGIN = 4

# How much closer (in world units) a rival must be than the current
# possessor before possession actually switches to them. Prevents two
# players contesting the same spot from flipping "closest" (and thus
# possession) every single tick over a hair's-width difference.
POSSESSION_STICKINESS = 6

# Base (unfatigued) max speed per role. Attackers are the fastest so
# they can win sprints to a loose ball; goalkeepers are the slowest
# since they mostly shuffle along the goal line.
GOALKEEPER_SPEED = 95
DEFENDER_SPEED = 115
ATTACKER_SPEED = 135
PLAYER_ACCELERATION = 600

GK_RUSH_RADIUS = 70
# How close the ball has to get to the goalkeeper before it *attempts*
# a save (see PlayerAI._make_save): a bit more than touching distance
# (PLAYER_RADIUS + BALL_RADIUS = 14), roughly an outstretched arm's
# reach, not the whole penalty area -- a keeper glued to the goal line
# via guard_goal_line tracks the ball closely enough that a larger
# radius turned every shot into an automatic save.
GK_SAVE_RADIUS = 18
# Not every attempt within reach is actually stopped -- a real keeper
# doesn't save 100% of shots on target either. Without some chance of
# missing, a keeper that reacts as fast/precisely as this one does
# turns into an impenetrable wall (0 goals conceded ever) rather than
# a goalkeeper.
GK_SAVE_SUCCESS_CHANCE = 0.55
# Minimum time between save-chance rolls while the ball stays within
# GK_SAVE_RADIUS (see PlayerAI._make_save) -- rolling every tick would
# make the keeper nearly unbeatable; never rolling again after one
# attempt would let a dead ball sitting next to him go untouched
# forever.
GK_SAVE_COOLDOWN = 0.4
# How hard a save/clearance sends the ball back out towards midfield.
GK_CLEAR_SPEED = 220
# How close an opponent may be to the goalkeeper's own goal before he
# no longer "feels safe" enough to sweep forward (see
# PlayerAI._feels_safe/_sweep) -- he stays back and guards the line
# instead.
GK_SAFE_OPPONENT_RADIUS = 160
DEFENSIVE_THIRD_DEPTH = 170
SHOOT_RADIUS = 150
SHOT_SPEED = 260
DRIBBLE_SPEED = 90

# Fatigue: stamina drains while sprinting (and a little while jogging),
# regenerates while idle/walking, and caps the effective max speed the
# steering layer is allowed to ask for, in between base_max_speed (full
# stamina) and base_max_speed * FATIGUE_MIN_SPEED_RATIO (empty tank).
MAX_STAMINA = 100.0
SPRINT_SPEED_RATIO = 0.8
JOG_SPEED_RATIO = 0.35
FATIGUE_DRAIN_RATE = 9.0
FATIGUE_JOG_DRAIN_RATE = 2.5
FATIGUE_REGEN_RATE = 14.0
FATIGUE_MIN_SPEED_RATIO = 0.45

BALL_FRICTION = 0.985

MATCH_DURATION = 60.0
GOAL_FLASH_DURATION = 1.6

COLOR_BACKGROUND = (18, 24, 20)
COLOR_COURT = (40, 90, 55)
COLOR_LINES = (210, 220, 210)
COLOR_BALL = (240, 230, 210)
COLOR_TEAM_A = (90, 160, 255)
COLOR_TEAM_B = (235, 90, 90)
COLOR_GOALKEEPER_RING = (255, 220, 60)
COLOR_TEXT = (235, 235, 235)
COLOR_FLASH = (255, 210, 60)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
