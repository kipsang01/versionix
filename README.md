# Versionix (VSX)

Versionix is a lightweight Version Control System (VCS) implemented in Python, providing core version control functionality through a simple command-line interface.

## Features

- Initialize repositories
- Stage and commit changes
- View commit history
- Check repository status
- Branch management
- Merge branches
- Compare differences between branches
- Clone repositories

## Installation

```bash
pip install git+ssh://git@github.com/kipsang01/versionix.git
```

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/versionix.git
cd versionix
```


### Running in Development Mode

To run the CLI during development:
```bash
python -m versionix.cli
```

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

#### Development Guidelines

- Follow PEP 8 style guidelines
- Write unit tests for new features
- Ensure all tests pass before submitting a pull request
- Use type hints
- Document new methods and functions

## Usage

### Initializing a Repository

Initialize a new repository in the current directory:
```bash
vsx init
```

Or specify a path:
```bash
vsx init /path/to/project
```

### Basic Workflow

1. Stage files:
```bash
vsx add file1.py file2.py
```

2. Commit changes:
```bash
vsx commit -m "Description of changes"
```

### Branch Operations

Create a new branch:
```bash
vsx branch new-feature
```

Checkout an existing branch:
```bash
vsx checkout main
```

### Advanced Commands

View commit history:
```bash
vsx log
```

Check repository status:
```bash
vsx status
```

Compare branches:
```bash
vsx diff branch1 branch2
```

Merge branches:
```bash
vsx merge source-branch target-branch
```

Clone a repository:
```bash
vsx clone /path/to/source /path/to/destination
```

## Requirements

- Python 3.10+
- No external dependencies

## Project Structure

```
versionix/
│
├── versionix/
│   ├── __init__.py
│   ├── cli.py
│   └── vsx.py
│
├── tests/
│   ├── test_init.py
│   ├── test_commit.py
│   └── ...
│
├── setup.py
├── README.md
└── requirements.txt
```

## License

[MIT License](LICENSE)

## Author

[Enock Kipsang](https://github.com/kipsang01)

## Disclaimer

This is a simplified Version Control System and should not be used as a replacement for production-grade VCS like Git.
But who 👃(knows)🙂
