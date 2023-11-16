# Aviation Safety Network Wrapper

This Python script collects aviation accident data from the [Aviation Safety Network](https://aviation-safety.net) website and stores it in a SQLite database.

## Getting Started

These instructions will help you set up the project on your local machine.

### Prerequisites

- Python 3.x
- [virtualenv](https://pypi.org/project/virtualenv/) (recommended for virtual environment)

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/snrufomechanic/aviation-safety-network-wrapper.git
    cd aviation-safety-network-wrapper
    ```

2. Create a virtual environment (optional but recommended):

    ```bash
    virtualenv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the script:

    ```bash
    python main.py
    ```

