#Richard Chong 85923095

import columns_mechanics
import pygame
import random


ROWS = 13
COLUMNS = 6
DEFAULT_WIDTH = 250
DEFAULT_HEIGHT = 500
BORDER_THICKNESS = 5
FRAME_RATE = 0 #increase above 20 (since a framerate parameter of 0 defaults to an fps of 20) for greater control sensitivity at the expense of increased computational cost
DROP_PERIOD = 1000
NEW_FALLER_DELAY = True #delays the generatino of a new faller by a single drop period
FAST_DOWN = True #allows you to force fallers to drop faster by pressing the down-arrow key

STARTING_FIELD = [[" "] * COLUMNS] * ROWS

#RGB Color Codes
BACKGROUND_COLOR = (128, 196, 255)
LINE_COLOR = (255, 255, 255)
JEWEL_COLORS = {"S": (255, 196, 196), "T": (64, 255, 64),
				"V": (128, 128, 128), "W": (0, 0, 0),
				"X": (255, 64, 64), "Y": (255, 255, 48),
				"Z": (169, 64, 255)}
JEWEL_BORDERS = (BACKGROUND_COLOR, (255, 196, 0), (0, 255, 255), (255, 255, 255))
#represents the following piece statuses: (faller, landed, frozen, matched)


def main() -> None:
	'''runs entire user interface'''

	pygame.init()

	running = True
	field = columns_mechanics.Field(ROWS, COLUMNS, STARTING_FIELD)
	clock = pygame.time.Clock()
	time = 0 #milliseconds elapsed
	surface = display_game(DEFAULT_WIDTH, DEFAULT_HEIGHT, field)
	new_piece = False

	field.add_column(("S", "X", "Y"), 3)

	while running:
		new_time = (time + clock.tick(FRAME_RATE)) % DROP_PERIOD

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.VIDEORESIZE:
				surface = display_game(event.w, event.h, field)
			elif event.type == pygame.KEYDOWN:
				try:
					process_keypress(event, field)
				except columns_mechanics.InvalidActionError:
					pass

		if time > new_time or FRAME_RATE == 1:
			try:
				field.next()
			except columns_mechanics.GameOverError:
				running = False

			if field.get_all_frozen() and not field.get_matches():
				if new_piece:
					new_piece = False
					add_random_column(field)
				else:
					new_piece = True
					if NEW_FALLER_DELAY:
						pygame.time.wait(DROP_PERIOD // 2)

		update_game(surface, field)
		time = new_time


	pygame.quit()


def display_game(width: int, height: int, field: columns_mechanics.Field) -> pygame.Surface:
	'''initializes a pygame display with the most recent game field'''

	surface = pygame.display.set_mode(size=(width, height), flags=pygame.RESIZABLE)

	update_game(surface, field)

	return surface


def update_game(surface: pygame.Surface, field: columns_mechanics.Field) -> None:
	'''updates the pygame display with the most recent game field'''

	_display_background(surface)
	_display_field(surface, field)

	pygame.display.flip()


def process_keypress(event: pygame.event, field: columns_mechanics.Field) -> bool:
	'''
	react to any user actions related to in-game changes
	return True if action is done
	'''

	if event.key == pygame.K_LEFT:
		field.shift(columns_mechanics.LEFT)

	elif event.key == pygame.K_RIGHT:
		field.shift(columns_mechanics.RIGHT)

	elif event.key == pygame.K_SPACE:
		field.rotate()

	elif event.key == pygame.K_DOWN and FAST_DOWN:
		field.next()
		return False

	else:
		return False

	return True


def add_random_column(field: columns_mechanics.Field) -> None:
	'''adds a new faller in a random column that has not been filled in the field'''
	
	random_column = random.randrange(COLUMNS)
	jewel_colors = tuple(JEWEL_COLORS)
	random_colors = (random.choice(jewel_colors), random.choice(jewel_colors), random.choice(jewel_colors))

	field.add_column(random_colors, random_column)


def _display_background(surface: pygame.Surface) -> None:
	'''draws the background of the game field onto the pygame surface'''
	
	surface.fill(BACKGROUND_COLOR)
	surface_width, surface_height = surface.get_size()

	for row in range(1, ROWS):
		y_coordinate = row * surface_height / (ROWS)
		pygame.draw.line(surface, LINE_COLOR, (0, y_coordinate), (surface_width, y_coordinate))

	for column in range(1, COLUMNS):
		x_coordinate = column * surface_width / COLUMNS
		pygame.draw.line(surface, LINE_COLOR, (x_coordinate, 0), (x_coordinate, surface_height))


def _display_field(surface: pygame.Surface, field: columns_mechanics.Field) -> None:
	'''draws the game field onto the pygame surface'''
	
	field = field.get_field()
	wait = False

	for row in range(ROWS):
		for column in range(COLUMNS):
			cell = field[row][column]
			if cell != None:
				_draw_piece(surface, cell, row, column)
				if cell.get_status() == 3:
					wait = True

	if wait:
		pygame.time.wait(DROP_PERIOD // 4)


def _draw_piece(surface: pygame.Surface, jewel: columns_mechanics.Piece, row: int, column: int) -> None:
	'''draws a jewel given a surface, location, and the piece itself'''

	jewel_color = JEWEL_COLORS[jewel.get_color()]
	border_color = JEWEL_BORDERS[jewel.get_status()]
	surface_width, surface_height = surface.get_size()

	rectangle = pygame.Rect(column * surface_width / COLUMNS + BORDER_THICKNESS,
		surface_height * (1 - (row + 1) / ROWS) + BORDER_THICKNESS,
		surface_width / COLUMNS - BORDER_THICKNESS * 2,
		surface_height / ROWS - BORDER_THICKNESS * 2)

	pygame.draw.rect(surface, jewel_color, rectangle) #fills rectangle
	pygame.draw.rect(surface, border_color, rectangle, BORDER_THICKNESS) #only outlines rectangle


if __name__ == '__main__':
	main()