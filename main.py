from abc import ABC, abstractmethod
from uuid import uuid4
from math import isfinite 


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass

class AbstractAccount(ABC):

    used_account_numbers = set()

    def __init__(self, account_number=None, owner=None, balance=0,
             status="active", currency="USD"):

        if account_number is None:
            account_number = str(uuid4())[:8]

            while account_number in AbstractAccount.used_account_numbers:
                account_number = str(uuid4())[:8]

        if not isinstance(account_number, str) or not account_number.strip():
            raise InvalidOperationError("Номер счёта должен быть непустой строкой")

        if account_number in AbstractAccount.used_account_numbers:
            raise InvalidOperationError("Номер счёта уже существует")

        if not isinstance(owner, str) or not owner.strip():
            raise InvalidOperationError("Имя владельца должно быть непустой строкой")

        if not isinstance(balance, (int, float)) or isinstance(balance, bool):
            raise InvalidOperationError("Баланс должен быть числом")

        if not isfinite(balance):
            raise InvalidOperationError("Начальный баланс должен быть конечным числом")

        if balance < 0:
            raise InvalidOperationError("Начальный баланс не может быть отрицательным")

        if not isinstance(status, str) or status not in ("active", "frozen", "closed"):
            raise InvalidOperationError("Недопустимый статус счёта")

        if not isinstance(currency, str) or currency not in ("RUB", "USD", "EUR", "KZT", "CNY"):
            raise InvalidOperationError("Недопустимая валюта счёта")

        self.account_number = account_number
        self.owner = owner
        self._balance = balance
        self.status = status
        self.currency = currency

        AbstractAccount.used_account_numbers.add(account_number)

    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    @abstractmethod
    def get_account_info(self):
        pass

class BankAccount(AbstractAccount):

    def deposit(self, amount):
        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен. Операция запрещена")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт. Операция запрещена")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount):
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount <= 0:
            raise InvalidOperationError("Сумма пополнения должна быть больше нуля")

        self._balance += amount
        print("Счёт пополнен на", amount)

    def withdraw(self, amount):
        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен. Операция запрещена")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт. Операция запрещена")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount):
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount <= 0:
            raise InvalidOperationError("Сумма снятия должна быть больше нуля")

        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно средств на счёте")

        self._balance -= amount
        print("Со счёта снято", amount)

    def get_account_info(self):
        return {
            "account_number": self.account_number,
            "owner": self.owner,
            "balance": self._balance,
            "status": self.status,
            "currency": self.currency
        }

    def __str__(self):
        return (
            f"BankAccount | "
            f"Владелец: {self.owner} | "
            f"Номер: ****{self.account_number[-4:]} | "
            f"Статус: {self.status} | "
            f"Баланс: {self._balance} {self.currency}"
        )

if __name__ == "__main__":

    # 1. Создаём банковские счета
    account1 = BankAccount("12345678", "Alex", 1000)
    account2 = BankAccount("87654321", "Anna", 2000, "frozen", "EUR")
    account3 = BankAccount("55556666", "John", 300, "closed", "USD")

    # 2. Проверяем активный счёт
    print("\n--- АКТИВНЫЙ СЧЁТ ---")

    account1.deposit(500)
    account1.withdraw(400)
    print(account1)

    # 3. Проверяем замороженный счёт
    print("\n--- ЗАМОРОЖЕННЫЙ СЧЁТ ---")

    print(account2)

    try:
        account2.deposit(500)
    except AccountFrozenError as error:
        print("Ошибка:", error)

    try:
        account2.withdraw(300)
    except AccountFrozenError as error:
        print("Ошибка:", error)

    # 4. Проверяем закрытый счёт
    print("\n--- ЗАКРЫТЫЙ СЧЁТ ---")

    print(account3)

    try:
        account3.deposit(100)
    except AccountClosedError as error:
        print("Ошибка:", error)

    try:
        account3.withdraw(100)
    except AccountClosedError as error:
        print("Ошибка:", error)

    # 5. Проверяем недостаточный баланс
    print("\n--- НЕДОСТАТОЧНО СРЕДСТВ ---")

    try:
        account1.withdraw(5000)
    except InsufficientFundsError as error:
        print("Ошибка:", error)

    # 6. Проверяем некорректную сумму
    print("\n--- ПРОВЕРКА СУММ ---")

    try:
        account1.deposit(-100)
    except InvalidOperationError as error:
        print("Ошибка:", error)

    try:
        account1.deposit("500")
    except InvalidOperationError as error:
        print("Ошибка:", error)

    # 7. Проверяем автоматическую генерацию UUID
    print("\n--- ГЕНЕРАЦИЯ UUID ---")

    account4 = BankAccount(owner="Michael", balance=500)
    account5 = BankAccount(owner="David", balance=700)

    print("Номер Michael:", account4.account_number)
    print("Номер David:", account5.account_number)

    # 8. Проверяем уникальность номера
    print("\n--- ПРОВЕРКА УНИКАЛЬНОСТИ ---")

    try:
        account6 = BankAccount("12345678", "Peter", 500)
    except InvalidOperationError as error:
        print("Ошибка:", error)

    # 9. Проверяем информацию о счёте
    print("\n--- ИНФОРМАЦИЯ О СЧЁТЕ ---")

    print(account1.get_account_info())

    print("\n--- DAY1: ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ---")


