from PIL import Image, ImageDraw, ImageFont, ImageOps
from tkinter import filedialog, Tk
import random

def load_and_orient_image(image_path):
    """Load an image, ensure proper orientation using EXIF data, and ensure it is in portrait orientation."""
    image = Image.open(image_path).convert("RGBA")
    image = ImageOps.exif_transpose(image)  # Correct orientation based on EXIF data
    if image.width > image.height:
        image = image.rotate(90, expand=True)  # Rotate to portrait orientation if needed
    return image


def scale_image(image_path, target_size):
    """Scale an image to fit within the target size."""
    image = load_and_orient_image(image_path)
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    return image, image.size


def generate_word_search(words, grid_size=15):
    """Generate a word search grid and word positions."""
    grid = [[" " for _ in range(grid_size)] for _ in range(grid_size)]
    directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]

    word_positions = {}

    for word in words:
        word = word.upper()
        placed = False

        for _ in range(100):  # Attempt to place the word 100 times
            if placed:
                break
            direction = random.choice(directions)
            row = random.randint(0, grid_size - 1)
            col = random.randint(0, grid_size - 1)

            end_row = row + direction[0] * (len(word) - 1)
            end_col = col + direction[1] * (len(word) - 1)

            if 0 <= end_row < grid_size and 0 <= end_col < grid_size:
                positions = []
                valid = True

                for i in range(len(word)):
                    new_row = row + i * direction[0]
                    new_col = col + i * direction[1]

                    if grid[new_row][new_col] not in (" ", word[i]):
                        valid = False
                        break
                    positions.append((new_row, new_col))

                if valid:
                    for i, (r, c) in enumerate(positions):
                        grid[r][c] = word[i]
                    word_positions[word] = positions
                    placed = True

    # Fill empty spaces with random letters
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == " ":
                grid[r][c] = chr(random.randint(65, 90))

    return grid, word_positions


def contains_bad_words(grid, bad_words):
    """Check if the grid contains any bad words."""
    grid_size = len(grid)
    all_words = set()

    # Extract rows and columns
    for row in grid:
        all_words.add("".join(row))
        all_words.add("".join(row[::-1]))

    for col in range(grid_size):
        column = "".join(grid[row][col] for row in range(grid_size))
        all_words.add(column)
        all_words.add(column[::-1])

    # Extract diagonals
    for offset in range(-grid_size + 1, grid_size):
        diagonal = "".join(grid[row][col] for row in range(grid_size) for col in range(grid_size)
                           if row - col == offset)
        all_words.add(diagonal)
        all_words.add(diagonal[::-1])

    # Check for bad words
    for word in bad_words:
        if word in all_words:
            return True

    return False


def generate_clean_word_search(words, bad_words, grid_size=15):
    """Generate a word search that excludes bad words."""
    while True:
        grid, word_positions = generate_word_search(words, grid_size)
        if not contains_bad_words(grid, bad_words):
            return grid, word_positions


def generate_word_list_image(words, font_size=20, padding=10, max_words_per_column=6):
    """Generate an image of the word list with columns and spacing, with a transparent background."""
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    max_word_length = max(len(word) for word in words)
    column_spacing = int(0.75 * (max_word_length + 1) * font_size // 2)  # Spacing between columns

    # Calculate number of columns
    num_columns = (len(words) + max_words_per_column - 1) // max_words_per_column
    column_widths = [(max(len(words[i]) for i in range(j * max_words_per_column,
                                                        min((j + 5) * max_words_per_column, len(words)))) + 5) * font_size // 2
                     for j in range(num_columns)]
    column_height = max_words_per_column * (font_size + padding)

    word_list_width = sum(column_widths) + (num_columns - 1) * column_spacing
    word_list_height = column_height

    word_list_image = Image.new("RGBA", (word_list_width, word_list_height), (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(word_list_image)

    x_offset = 0
    for column, start_idx in enumerate(range(0, len(words), max_words_per_column)):
        for row, word in enumerate(words[start_idx:start_idx + max_words_per_column]):
            x = x_offset + padding
            y = padding + row * (font_size + padding)
            draw.text((x, y), word, font=font, fill="black")
        x_offset += column_widths[column] + column_spacing

    return word_list_image


def save_crossword_overlay_image(grid, word_positions, image_path, words_to_search_for, filename="crossword_overlay.png"):
    """Save the crossword grid overlayed on a portrait-oriented image."""
    # Load and orient the background image
    background_image = load_and_orient_image(image_path)
    image_width, image_height = background_image.size

    # Set word search grid width to 75% of the image width
    target_width = int(image_width * 0.75)  # 75% of the image width

    # Calculate the number of cells based on this target width
    cell_size = target_width // len(grid)  # Number of pixels per cell

    # Create a blank image with a white rectangle as the base layer (portrait orientation)
    crossword_image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 255))

    # Paste the background image onto the white base layer
    scaled_image, (scaled_width, scaled_height) = scale_image(image_path, (image_width, image_height))
    scaled_image.putalpha(100)  # Set transparency (128 == 50%)
    crossword_image.paste(scaled_image, (0, 0), scaled_image)

    # Draw the crossword grid
    draw = ImageDraw.Draw(crossword_image)
    try:
        font = ImageFont.truetype("arialbd.ttf", cell_size // 2 + 5)  # Increased font size by 5 points
    except IOError:
        font = ImageFont.load_default()

    # Calculate grid dimensions
    grid_width = len(grid) * cell_size
    grid_height = len(grid) * cell_size

    # Center the word search grid horizontally
    start_x = (image_width - grid_width) // 2

    # Vertically align the center of the wordsearch to the top 1/3 of the image
    start_y = image_height // 3 - grid_height // 2  # Align center of the grid to top 1/3 of the image

    # Adjust to move down by 10% of the total image height
    start_y += int(image_height * 0.10)  # Move down by 10%

    # Draw the grid with word highlights
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            letter = grid[row][col]

            # Check if this cell is part of any word's positions
            letter_color = "black"  # Default color
            for positions in word_positions.values():
                if (row, col) in positions:
                    letter_color = "blue"  # Change color to blue if part of the word
                    break

            bbox = draw.textbbox((0, 0), letter, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Adjust position to center the text in the cell
            draw.text((x + (cell_size - text_width) // 2, y + (cell_size - text_height) // 2), letter, font=font,
                      fill=letter_color)

    # Generate word list image and crop it
    words_list_image = generate_word_list_image(words_to_search_for, font_size=font.size)

    # Center the word list image halfway between the word search and the bottom of the image
    word_list_y_offset = start_y + grid_height + (
                image_height - grid_height - start_y) // 2 - words_list_image.height // 2  # Halfway
    word_list_x_offset = (image_width - words_list_image.width) // 2  # Center horizontally

    # Paste the word list image onto the crossword image
    crossword_image.paste(words_list_image, (word_list_x_offset, word_list_y_offset), words_list_image)

    crossword_image.save(filename)


if __name__ == "__main__":
    # Ask for the background image file
    Tk().withdraw()
    image_path = filedialog.askopenfilename(title="Select Background Image")

    # Load words from searchfor.txt
    words = []
    with open('searchfor.txt', 'r') as file:
        words = [line.strip() for line in file.readlines()]

    # Load bad words from bad_words.txt
    bad_words = []
    with open('bad_words.txt', 'r') as file:
        bad_words = [line.strip().upper() for line in file.readlines()]

    # Generate the crossword grid and word positions
    grid, word_positions = generate_clean_word_search(words, bad_words)

    # Generate and save the crossword overlay image
    save_crossword_overlay_image(grid, word_positions, image_path, words)
