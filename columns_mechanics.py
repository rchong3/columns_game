#Richard Chong 85923095

from collections import namedtuple


Vector2D = namedtuple("Vector2D", ("x", "y")) #can either represent a positional or translational vector

def vector_addition_2D(vectors: (Vector2D)) -> Vector2D:
	'''returns the vector sum of the tuple of 2-dimensional vectors'''

	x, y = 0, 0

	for vector in vectors:
		x += vector.x
		y += vector.y

	return Vector2D(x, y)

DOWN = Vector2D(0, -1)
UP = Vector2D(0, 1)
LEFT = Vector2D(-1, 0)
RIGHT = Vector2D(1, 0)

FALLER = 0
LANDED = 1
FROZEN = 2
MATCHED = 3

COLORS = ("S", "T", "V", "W", "X", "Y", "Z")


class InvalidMatchError(Exception):
	'''raised if an unfrozen Piece object is marked as matched'''
	pass

class GameOverError(Exception):
	'''raised if a Piece object is frozen above the visible field'''
	pass

class InvalidColorError(Exception):
	'''raised if a faller piece's color is not valid'''
	pass

class InvalidActionError(Exception):
	'''raised if an invalid action is attempted'''
	pass

class Piece:
	'''
	Piece represents a gamepiece with a given color (S, T, V, W, X, Y, or Z)
	and a status (0 meaning faller, 1 meaning landed, 2 meaning frozen, and
	3 meaning matched)
	'''

	def __init__(self, color: str) -> None:
		'''initializes faller Piece of color as dictated by the input'''

		if color not in COLORS:
			raise InvalidColorError

		self._color = color
		self._status = 0

	def get_color(self) -> str:
		'''returns the color of the Piece'''

		return self._color

	def get_status(self) -> str:
		'''returns the status (faller, landed, or frozen) of the Piece'''

		return self._status

	def update_status(self, matched: bool = False) -> None:
		'''
		if not matched, updates the Piece's status to next possible state
		if matched, check if Piece is frozen, updating the status to matched
		if so and raising an error if invalid match
		'''

		if not matched:
			self._status = (self._status + 1) % 3

		elif MATCHED >= self._status > FALLER:
			self._status = MATCHED

		else:
			raise InvalidMatchError(f"You can't match an unfrozen piece with status {self._status}")


class Field:
	'''Field represents a game field (both hidden and visible) containing Pieces'''

	def __init__(self, rows: int, columns: int, starting_field: [[str]]) -> None:
		'''
		initializes field object with empty field of a given size and
		hidden section above field represented by dictionary
		'''

		self._rows = rows
		self._columns = columns
		self._field = [[Piece(char) if char is not " " else None for char in line] for line in starting_field]
		self._hidden: {Vector2D: Piece} = {} #Vector2D represents location here
		self._all_frozen = False #represents whether or not all pieces in the field are frozen
		self._matches = False #represents whether or not there are any matched pieces still on the field
		self._column_base: Vector2D = None #represents location of lowest faller in new column

		while not self._all_frozen:
			self._drop_all()
		
		self._label_all_matches()

	def get_field(self) -> [[Piece]]:
		'''returns a copy of the field'''

		return self._field[:]

	def get_all_frozen(self) -> bool:
		'''returns True if all pieces in the field are frozen'''

		return self._all_frozen

	def get_matches(self) -> bool:
		'''returns True if there are any matches still on the field'''

		return self._matches

	def add_column(self, colors: (str), column: int) -> None:
		'''
		creates a new piece at the desired location, adding
		to the hidden area of field if necessary
		'''

		if not(self._columns > column >= 0 and self._all_frozen and not self._matches) or len(colors) != 3:
			raise InvalidActionError(self._matches)

		pieces = [Piece(color) for color in colors]
		if self._field[self._rows - 2][column] != None:
			for piece in pieces:
				piece.update_status()

		self._column_base = Vector2D(column, self._rows - 1)
		self._all_frozen = False
		self._field[self._rows - 1][column] = pieces[0]
		self._hidden[Vector2D(column, self._rows)] = pieces[1]
		self._hidden[Vector2D(column, self._rows + 1)] = pieces[2]

	def next(self) -> None:
		'''change the field in accordance to a single time interval'''

		if self._matches:
			self._clear_matches()
			while not self._all_frozen:
				self._drop_all()

		if self._all_frozen or self._field[self._column_base.y][self._column_base.x] != None and self._field[self._column_base.y][self._column_base.x].get_status() == LANDED:
			self._label_all_matches()

		if self._column_base != None:
			self._drop_all()

	def shift(self, direction: Vector2D) -> None:
		'''
		shifts all fallers one cell to the left or right given the
		appropriate constant, if nothing is blocking it
		'''

		if self._column_base == None or self._matches:
			raise InvalidActionError

		if self._move(self._column_base, direction):
			self._move(vector_addition_2D((self._column_base, UP)), direction)
			self._move(vector_addition_2D((self._column_base, UP, UP)), direction)
			self._column_base = vector_addition_2D((self._column_base, direction))

			below = vector_addition_2D((self._column_base, DOWN))
			if below.y > -1 and self._field[below.y][below.x] == None and self._field[self._column_base.y][self._column_base.x].get_status() == LANDED:
				self._shift_status(2)
			elif below.y > -1 and self._field[below.y][below.x] != None and self._field[self._column_base.y][self._column_base.x].get_status() == FALLER:
				self._shift_status(1)
 

	def rotate(self) -> None:
		'''moves all fallers one grid down except the bottom faller moves to where the top faller was'''

		if self._column_base == None or self._matches:
			raise InvalidActionError

		temporary_cell = self._field[self._column_base.y][self._column_base.x]
		self._field[self._column_base.y][self._column_base.x] = None
		self._move(vector_addition_2D((self._column_base, UP)), DOWN)
		self._move(vector_addition_2D((self._column_base, UP, UP)), DOWN)

		if self._column_base.y + 2 >= self._rows:
			self._hidden[vector_addition_2D((self._column_base, UP, UP))] = temporary_cell
		else:
			self._field[self._column_base.y + 2][self._column_base.x] = temporary_cell

	def _drop_all(self) -> None:
		'''
		drops all fallers by one grid and update _all_frozen attribute
		'''

		self._all_frozen = True

		self._drop_visible()
		self._drop_hidden()
		self._update_faller_base()

	def _drop_visible(self) -> None:
		'''drops all fallers on the field'''

		for row_index in range(self._rows):
			for column_index in range(self._columns):
				cell_location = Vector2D(column_index, row_index)
				cell = self._field[cell_location.y][cell_location.x]

				if cell != None and cell.get_status() < FROZEN:
					if self._move(cell_location, DOWN):
						self._all_frozen = False
						location_below = vector_addition_2D((cell_location, DOWN, DOWN))
						if location_below.y == -1 or self._field[location_below.y][location_below.x] != None and self._field[location_below.y][location_below.x].get_status() > FALLER:
							self._field[location_below.y + 1][location_below.x].update_status()
					else:
						cell.update_status()
						if cell.get_status() != FROZEN:
							self._all_frozen = False

	def _drop_hidden(self) -> None:
		'''drops all fallers hidden above the field'''

		for cell_location in sorted(self._hidden):
			new_location = vector_addition_2D((cell_location, DOWN))
			cell_status = self._hidden[cell_location].get_status()

			if self._within_bounds(new_location) and self._field[new_location.y][new_location.x] == None or new_location not in self._hidden and not self._within_bounds(new_location):
				if self._within_bounds(new_location):
					self._field[new_location.y][new_location.x] = self._hidden[cell_location]
					new_cell = self._field[new_location.y][new_location.x]
				else:
					self._hidden[new_location] = self._hidden[cell_location]
					new_cell = self._hidden[new_location]
				location_below = vector_addition_2D((new_location, DOWN))

				if self._field[location_below.y][location_below.x] == None:
					new_cell.update_status()
					new_cell.update_status()
					self._all_frozen = False
				elif self._field[location_below.y][location_below.x].get_status() != FALLER:
					new_cell.update_status()
					self._all_frozen = False
				del self._hidden[cell_location]

			elif cell_status == FALLER:
				self._hidden[cell_location].update_status()

			elif not self._matches:
				raise GameOverError()

	def _update_faller_base(self) -> None:
		'''updates the position of the faller column's lowest piece'''

		if self._column_base != None:
			if self._field[self._column_base.y][self._column_base.x] == None or self._field[self._column_base.y][self._column_base.x].get_status() == FROZEN:
				self._column_base = None
			else:
				self._column_base = vector_addition_2D((self._column_base, DOWN))

	def _label_all_matches(self) -> None:
		'''updates the status of all pieces that are matched in the field'''

		if not self._all_frozen and self._field[self._column_base.y][self._column_base.x].get_status() != LANDED:
			raise InvalidActionError

		starting_cells = (Vector2D(0, 0), Vector2D(0, 0), Vector2D(self._columns - 3, 0), Vector2D(0, self._rows - 3), Vector2D(2, 0), Vector2D(self._columns - 1, self._rows - 3))
		shift_directions = (RIGHT, UP, LEFT, DOWN, RIGHT, DOWN)
		check_directions = (UP, RIGHT, Vector2D(1, 1), Vector2D(1, 1), Vector2D(-1, 1), Vector2D(-1, 1))

		for i in range(len(starting_cells)):
			self._label_sequences(starting_cells[i], shift_directions[i], check_directions[i])

		
	def _label_sequences(self, start_position: Vector2D, shift_direction: Vector2D, check_direction: Vector2D) -> None:
		'''
		iterates through all sequences of Piece objects along each check direction
		starting from the start position and shifting along a single direction
		'''

		while self._within_bounds(start_position):
			position = start_position
			sequence: [Piece] = []

			while self._within_bounds(position, hidden=True):
				if self._within_bounds(position):
					a = self._field[position.y][position.x]
					sequence.append(self._field[position.y][position.x])
				elif position in self._hidden:
					a = self._hidden[position]
					sequence.append(self._hidden[position])
				position = vector_addition_2D((position, check_direction))

			self._label_sequence(sequence)
			start_position = vector_addition_2D((start_position, shift_direction))

	def _label_sequence(self, pieces: [Piece]) -> None:
		'''iterates through the given pieces, updating their statuses if matches are found'''

		previous_color = None
		count = 1

		for piece_index in range(len(pieces)):
			if pieces[piece_index] == None:
				previous_color = None
				continue
			current_color = pieces[piece_index].get_color()
			if current_color == previous_color:
				count += 1
				if count == 3:
					self._matches = True
					for matched_index in range(piece_index - 2, piece_index + 1):
						pieces[matched_index].update_status(matched=True)
				elif count > 3:
					pieces[piece_index].update_status(matched=True)

			else:
				count = 1
			previous_color = current_color

	def _clear_matches(self) -> None:
		'''deletes all matched pieces and update the status of pieces above now empty spaces'''

		if not self._all_frozen:
			raise InvalidActionError

		self._matches = False

		#deletes all matched pieces in the visible field and update above cells to be faller
		for row_index in range(self._rows):
			for column_index in range(self._columns):
				cell = self._field[row_index][column_index]

				if cell != None and cell.get_status() == MATCHED:
					self._field[row_index][column_index] = None
					self._all_frozen = False

					for above_index in range(row_index + 1, self._rows):
						cell_above = self._field[above_index][column_index]

						if cell_above != None and cell_above.get_status() == FROZEN:
							cell_above.update_status()

					for cell_above in self._hidden:
						if cell_above.x == column_index and self._hidden[cell_above].get_status() < 3:
							self._hidden[cell_above].update_status()
							if self._hidden[cell_above].get_status() == LANDED:
								self._hidden[cell_above].update_status()
								self._hidden[cell_above].update_status()

		#deletes all matched pieces in the hidden field
		for cell in tuple(self._hidden):
			if self._hidden[cell].get_status() == MATCHED:
				del self._hidden[cell]


	def _move(self, start: Vector2D, direction: Vector2D) -> bool:
		'''
		moves the piece in the given location (row, column) in the given direction,
		which can be a constant DOWN, LEFT, or RIGHT if the spot in that direction
		is valid
		returns True if the move was successful and False if the move was invalid
		'''

		target = vector_addition_2D((start, direction))

		if self._valid_move(start, target):
			if 0 <= start.y < self._rows:
				piece = self._field[start.y][start.x]
				self._field[start.y][start.x] = None
			else:
				piece = self._hidden[start]
				del self._hidden[start]

			if 0 <= target.y < self._rows:
				self._field[target.y][target.x] = piece
			else:
				self._hidden[target] = piece
			return True

		else:
			return False

	def _shift_status(self, status_shifts: int) -> None:
		'''update status of fallers if change occurs where status_shifts determines how many times to update the status'''

		for row in range(self._column_base.y, self._column_base.y + 3):
			if row < self._rows:
				for i in range(status_shifts):
					self._field[row][self._column_base.x].update_status()

			else:
				for i in range(status_shifts):
					self._hidden[Vector2D(self._column_base.x, row)].update_status()

	def _valid_move(self, start: Vector2D, target: Vector2D) -> bool:
		'''returns True if the move is valid and False if the move is invalid'''

		return self._within_bounds(target) and\
			self._within_bounds(start, hidden=True) and\
			self._field[target.y][target.x] == None or\
			target.y >= self._rows and\
			start.y >= self._rows and\
			self._within_bounds(target, hidden=True) and\
			self._within_bounds(start, hidden=True) and\
			target not in self._hidden

	def _within_bounds(self, location: Vector2D, hidden = False) -> bool:
		'''returns True if the given location is within the field (include hidden part if hidden == True)'''

		return 0 <= location.x < self._columns and\
			(0 <= location.y < self._rows + 2 and hidden or\
			0 <= location.y < self._rows and not hidden)

