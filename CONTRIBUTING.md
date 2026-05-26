# Contributing to Vantage Mail

Thank you for your interest in contributing to Vantage Mail! We welcome contributions to help improve the application.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vantage-mail.git
   cd vantage-mail
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies in editable mode:
   ```bash
   pip install -e .[dev]
   ```

## Code Quality Standards

* **PyQt6 Naming and Practices**: Always import QAction from `PyQt6.QtGui`, not `PyQt6.QtWidgets`.
* **Asynchronous Operations**: All network and database intensive operations must be executed off the main UI thread using `QThread` and worker objects. Store worker instances in `self._workers` to prevent garbage collection.
* **Compatibility**: Keep Python source files encoded in UTF-8 with `# -*- coding: utf-8 -*-` headers.
* **Testing**: Write unit tests for new services and modules under `tests/unit`. Run tests using:
   ```bash
   pytest tests/ -v
   ```

## Pull Request Process

1. Fork the repository and create a feature branch.
2. Implement your changes, verifying all tests pass.
3. Commit your changes with clear, descriptive commit messages.
4. Push your branch and open a Pull Request explaining the modification.
