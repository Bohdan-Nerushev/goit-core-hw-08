from collections import UserDict
from datetime import datetime, timedelta
import re
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if len(value) == 10 and value.isdigit():
            super().__init__(value)
        else:
            raise ValueError("Неправильний формат номера телефону: повинен бути рівно 10 цифр")

    def __str__(self):
        return str(self.value)


class Birthday(Field):
    def __init__(self, value):
        try:
            pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
            match = re.search(pattern, value)
            if match:
                date_value = datetime.strptime(value, '%d.%m.%Y').date()
                if date_value > datetime.now().date():
                    raise ValueError("Дата народження не може бути в майбутньому")
                super().__init__(date_value)
            else:
                raise ValueError("Неправильний формат дати. Використовуйте DD.MM.YYYY")
        except ValueError as e:
            raise ValueError("Неправильний формат дати. Використовуйте DD.MM.YYYY") from e

    def __str__(self):
        return self.value.strftime('%d.%m.%Y')


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        if any(p.value == phone for p in self.phones):
            raise ValueError("Цей номер телефону вже існує")
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                break

    def edit_phone(self, old_phone, new_phone):
        phone = self.find_phone(old_phone)
        if phone:
            phone.value = new_phone
        else:
            raise ValueError("Номер телефону не знайдено")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def info_birthday(self):
        return self.birthday

    def __str__(self):
        phones = "; ".join(str(p) for p in self.phones)
        birthday_str = f", дата народження: {self.birthday}" if self.birthday else ""
        return f"Ім'я контакту: {self.name}, телефони: {phones}{birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record):
        if not isinstance(record, Record):
            raise ValueError("Лише об'єкти Record можуть бути додані до AddressBook.")
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = datetime.now().date()
        for record in self.data.values():
            if isinstance(record, Record) and record.birthday:
                birthday_date = record.birthday.value
                birthday_this_year = birthday_date.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                birthday_this_year = self.adjust_for_weekend(birthday_this_year)
                if today <= birthday_this_year <= today + timedelta(days=days):
                    upcoming_birthdays.append(
                        {"name": record.name.value, "birthday": birthday_this_year.strftime("%d.%m.%Y")}
                    )
        return upcoming_birthdays

    @staticmethod
    def adjust_for_weekend(date):
        if date.weekday() == 5:  # Субота
            return date + timedelta(days=2)
        elif date.weekday() == 6:  # Неділя
            return date + timedelta(days=1)
        return date


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, KeyError, IndexError, TypeError) as e:
            return str(e)

    return inner


def parse_input(user_input):
    return user_input.lower().strip().split()


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        return "Будь ласка, вкажіть і ім'я, і номер телефону."
    name, phone = args[:2]
    try:
        phone = Phone(phone)  # Валідація номера телефону
    except ValueError as e:
        return str(e)

    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    else:
        message = "Контакт оновлено."
    try:
        record.add_phone(phone.value)
    except ValueError as e:
        return str(e)
    return message


@input_error
def change_contact(book: AddressBook, name, new_phone):
    try:
        new_phone = Phone(new_phone).value  # Валідація номера телефону
    except ValueError as e:
        return str(e)

    record = book.find(name)
    if record:
        if len(record.phones) == 0:
            return "Немає телефонів для зміни."
        old_phone = record.phones[0].value
        record.edit_phone(old_phone, new_phone)
        return "Контакт оновлено."
    else:
        return "Контакт не знайдено."


@input_error
def show_phone(book: AddressBook, name):
    record = book.find(name)
    if record:
        return ", ".join(str(phone) for phone in record.phones)
    else:
        return "Контакт не знайдено."


@input_error
def show_all(book: AddressBook):
    contacts_info = [str(record) for record in book.data.values() if isinstance(record, Record)]
    return '\n'.join(contacts_info) or "Список контактів порожній."


@input_error
def add_birthday(book: AddressBook, name, birthday):
    record = book.find(name)
    if record:
        try:
            record.add_birthday(birthday)
            return "День народження додано/оновлено."
        except ValueError as e:
            return str(e)
    else:
        return "Контакт не знайдено."


@input_error
def show_birthday(book: AddressBook, name):
    record = book.find(name)
    if record:
        birthday_info = record.info_birthday()
        if birthday_info:
            return f"День народження {record.name.value}: {birthday_info}"
        else:
            return "Інформація про день народження не знайдена."
    else:
        return "Контакт не знайдено."


@input_error
def birthdays(book: AddressBook, days=7):
    upcoming_birthdays = book.get_upcoming_birthdays(days)
    if upcoming_birthdays:
        result = [
            {"name": info["name"], "congratulation_date": info["birthday"]} for info in upcoming_birthdays
        ]
        return result
    else:
        return "Найближчі дні народження не знайдені."


@input_error
def save_data(book, filename="addressbook.txt"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)
    return "Дані збережено."


@input_error
def load_data(filename="addressbook.txt"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    try:
        book = load_data()
        print("Ласкаво просимо до асистент бота!")
        while True:
            user_input = input("Введіть команду: ")
            if not user_input.strip():
                print("Будь ласка, введіть команду.")
                continue

            command, *args = parse_input(user_input)

            if command in ["close", "exit", 'stop']:
                print(save_data(book))
                print("До побачення!")
                break
            elif command == "hello":
                print("Чим можу допомогти?")

            elif command == "add":
                print(add_contact(args, book))
            elif command == "change":
                if len(args) < 2:
                    print("Будь ласка, вкажіть ім'я контакту і новий номер телефону.")
                else:
                    print(change_contact(book, args[0], args[1]))
            elif command == "phone":
                if args:
                    print(show_phone(book, args[0]))
                else:
                    print("Будь ласка, вкажіть ім'я контакту для команди phone.")
            elif command == "all":
                print(show_all(book))
            elif command == "add-birthday":
                if len(args) < 2:
                    print("Будь ласка, вкажіть і ім'я контакту, і дату народження.")
                else:
                    print(add_birthday(book, args[0], args[1]))
            elif command == "show-birthday":
                if args:
                    print(show_birthday(book, args[0]))
                else:
                    print("Будь ласка, вкажіть ім'я контакту для команди show-birthday.")
            elif command == "birthdays":
                days = int(args[0]) if args and args[0].isdigit() else 7
                result = birthdays(book, days)
                if isinstance(result, str):
                    print(result)
                else:
                    print("[")
                    for entry in result:
                        print(f"    {entry},")
                    print("]")
            else:
                print("Невірна команда. Будь ласка, спробуйте ще раз.")
    except KeyboardInterrupt:
        print("\nПроцес перервано користувачем. Дані збережено.")
        save_data(book)
        print("До побачення!")


if __name__ == '__main__':
    main()
