# Contributing

Thanks for your interest in Pirate Arcade!

## Getting Started

1. Fork and clone the repository.
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
3. Create a branch for your changes.

## Code Style

- Follow PEP 8.
- Use existing patterns (classes, imports, naming).
- Do not add comments unless they explain *why*, not *what*.
- Use `pygame.gfxdraw` for anti-aliased rendering where possible.
- Keep rendering and game logic separate (gameplay classes should not import heavy rendering modules).

## Testing

- All tests must pass before merging.
- Run tests:
  ```bash
  pytest -v
  ```
- Pygame tests use `SDL_VIDEODRIVER=dummy` — no display required.
- Add tests for new functionality in the appropriate `tests/test_*.py` file.
- For gameplay logic tests, use the `MockAudio` pattern:
  ```python
  class MockAudio:
      def play(self, name):
          pass
  ```

## Adding a New Game

1. Create `games/your_game/` with `game.py`, `gameplay.py`, and any needed modules.
2. Register it in `launcher.py` — add a `GameCard` entry in the list.
3. Update `main.py` to handle the new game's run method.
4. Add tests in `tests/test_your_game.py`.
5. Update the README game table.

## Submitting Changes

1. Push your branch and open a pull request.
2. Describe what the change does and why.
3. Link any related issues.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
