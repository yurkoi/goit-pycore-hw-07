from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name can't be empty.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        if birthday > datetime.today().date():
            raise ValueError("Birthday can't be in the future.")
        super().__init__(birthday)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        if self.find_phone(phone) is not None:
            raise ValueError(f"Phone {phone} already exists.")
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found = self.find_phone(phone)
        if found is None:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(found)

    def edit_phone(self, old_phone, new_phone):
        found = self.find_phone(old_phone)
        if found is None:
            raise ValueError(f"Phone {old_phone} not found.")
        if self.find_phone(new_phone) is not None:
            raise ValueError(f"Phone {new_phone} already exists.")
        index = self.phones.index(found)
        self.phones[index] = Phone(new_phone)

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        if self.birthday is None:
            return f"Contact name: {self.name.value}, phones: {phones}"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {self.birthday}"


def birthday_in_year(birthday, year):
    try:
        return birthday.replace(year=year)
    except ValueError:
        return birthday.replace(year=year, day=28)


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name not in self.data:
            raise KeyError(name)
        del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value
            birthday_this_year = birthday_in_year(birthday, today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_in_year(birthday, today.year + 1)

            days_until_birthday = (birthday_this_year - today).days

            if days_until_birthday <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date = congratulation_date + timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date = congratulation_date + timedelta(days=1)

                upcoming.append((congratulation_date, record.name.value))

        upcoming.sort()

        result = []
        for congratulation_date, name in upcoming:
            result.append({
                "name": name,
                "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
            })

        return result


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter user name."

    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book):
    if len(args) < 2:
        raise ValueError("Give me name and phone please.")
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."
    record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args, book):
    if len(args) < 3:
        raise ValueError("Give me name, old phone and new phone please.")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if not record.phones:
        return f"{name} has no phones."
    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(book):
    if not book.data:
        return "No contacts saved."
    lines = []
    for record in book.data.values():
        lines.append(str(record))
    return "\n".join(lines)


@input_error
def add_birthday(args, book):
    if len(args) < 2:
        raise ValueError("Give me name and birthday please.")
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if record.birthday is None:
        record.add_birthday(birthday)
        return "Birthday added."
    record.add_birthday(birthday)
    return "Birthday updated."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if record.birthday is None:
        return f"{name} has no birthday saved."
    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next week."
    lines = []
    for item in upcoming:
        lines.append(f"{item['congratulation_date']}: {item['name']}")
    return "\n".join(lines)


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        try:
            user_input = input("Enter a command: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGood bye!")
            break

        if not user_input.strip():
            print("Invalid command.")
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
