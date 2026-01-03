# main.py

from interface.input_text import get_input
from interface.output_text import send_output
from core.controller import handle_input

def main():
    while True:
        text = get_input()
        response = handle_input(text)
        send_output(response)

if __name__ == "__main__":
    main()
