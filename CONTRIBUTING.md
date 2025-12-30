# Contributing to EOG Image Annotation Plugin

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/eog-annotation-plugin.git
   cd eog-annotation-plugin
   ```
3. Install the plugin locally:
   ```bash
   ./install.sh
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Add docstrings to all classes and public methods
- Use descriptive variable names

### Testing

1. Test your changes:
   ```bash
   python3 test_plugin.py
   ```
2. Test in EOG:
   ```bash
   eog /path/to/test/image.png
   ```
3. Enable debug mode to see detailed output:
   ```bash
   EOG_ANNOTATION_DEBUG=1 eog /path/to/test/image.png
   ```

### Submitting Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test thoroughly
4. Commit with clear messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```
5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. Create a Pull Request on GitHub

## Areas for Contribution

- Bug fixes
- New annotation tools
- UI improvements
- Performance optimizations
- Documentation improvements
- Translation/localization

## Questions?

Open an issue on GitHub for questions or discussions.

