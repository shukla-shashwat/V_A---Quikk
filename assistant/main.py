"""main.py
Small runner that demonstrates importing the modules and using the controller.
"""

from assistant.core import controller
from assistant.io import output_text


def main():
    res = controller.handle_input("Hello, I need help")
    output_text.print_output(f"Startup: {res}")


if __name__ == "__main__":
    main()
