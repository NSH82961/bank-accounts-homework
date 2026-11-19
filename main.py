from abc import ABC, abstractmethod
from uuid import uuid4
from math import isfinite 
from datetime import datetime


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

class SavingsAccount(BankAccount):

    def __init__(self, account_number=None, owner=None, balance=0,
                 status="active", currency="USD",
                 min_balance=0, monthly_interest_rate=0.01):

       
        if not isinstance(min_balance, (int, float)) or isinstance(min_balance, bool):
            raise InvalidOperationError("Минимальный остаток должен быть числом")

        if not isfinite(min_balance) or min_balance < 0:
            raise InvalidOperationError("Минимальный остаток должен быть конечным и неотрицательным")

        if min_balance > balance:
            raise InvalidOperationError("Минимальный остаток не может превышать начальный баланс")

        if not isinstance(monthly_interest_rate, (int, float)) or isinstance(monthly_interest_rate, bool):
            raise InvalidOperationError("Процентная ставка должна быть числом")

        if not isfinite(monthly_interest_rate) or monthly_interest_rate < 0:
            raise InvalidOperationError("Процентная ставка должна быть конечной и неотрицательной")

        super().__init__(
                    account_number, owner, balance, status, currency
                )

        self.min_balance = min_balance
        self.monthly_interest_rate = monthly_interest_rate

    def withdraw(self, amount):

        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительным конечным числом")

        if self._balance - amount < self.min_balance:
            raise InsufficientFundsError(
                "Нельзя снять деньги: будет нарушен минимальный остаток"
            )

        super().withdraw(amount)    

    def apply_monthly_interest(self):

        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт")

        interest = self._balance * self.monthly_interest_rate

        self._balance += interest

        print("Начислены проценты:", interest)

    def get_account_info(self):

        info = super().get_account_info()

        info["account_type"] = "SavingsAccount"
        info["min_balance"] = self.min_balance
        info["monthly_interest_rate"] = self.monthly_interest_rate

        return info

    def __str__(self):

        return (
            f"SavingsAccount | "
            f"Владелец: {self.owner} | "
            f"Номер: ****{self.account_number[-4:]} | "
            f"Статус: {self.status} | "
            f"Баланс: {self._balance:.2f} {self.currency} | "
            f"Минимальный остаток: {self.min_balance:.2f} | "
            f"Месячная ставка: {self.monthly_interest_rate:.2%}"
        )

class PremiumAccount(BankAccount):

    def __init__(self, account_number=None, owner=None, balance=0,
                 status="active", currency="USD",
                 overdraft_limit=500, withdrawal_limit=10000,
                 transaction_fee=5):

        if not isinstance(overdraft_limit, (int, float)) or isinstance(overdraft_limit, bool):
            raise InvalidOperationError("Лимит овердрафта должен быть числом")

        if not isfinite(overdraft_limit) or overdraft_limit < 0:
            raise InvalidOperationError("Лимит овердрафта должен быть конечным и неотрицательным")

        if not isinstance(withdrawal_limit, (int, float)) or isinstance(withdrawal_limit, bool):
            raise InvalidOperationError("Лимит снятия должен быть числом")

        if not isfinite(withdrawal_limit) or withdrawal_limit <= 0:
            raise InvalidOperationError("Лимит снятия должен быть положительным конечным числом")

        if not isinstance(transaction_fee, (int, float)) or isinstance(transaction_fee, bool):
            raise InvalidOperationError("Комиссия должна быть числом")

        if not isfinite(transaction_fee) or transaction_fee < 0:
            raise InvalidOperationError("Комиссия должна быть конечной и неотрицательной")

        super().__init__(
            account_number, owner, balance, status, currency
        )

        self.overdraft_limit = overdraft_limit
        self.withdrawal_limit = withdrawal_limit
        self.transaction_fee = transaction_fee 

    def withdraw(self, amount):

        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительным конечным числом"
            )

        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Превышен лимит снятия")

        total_amount = amount + self.transaction_fee

        if self._balance - total_amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                "Превышен разрешённый лимит овердрафта"
            )

        self._balance -= total_amount

        print("Со счёта снято:", amount)
        print("Комиссия:", self.transaction_fee)

    def get_account_info(self):

        info = super().get_account_info()

        info["account_type"] = "PremiumAccount"
        info["overdraft_limit"] = self.overdraft_limit
        info["withdrawal_limit"] = self.withdrawal_limit
        info["transaction_fee"] = self.transaction_fee

        return info

    def __str__(self):

        return (
            f"PremiumAccount | "
            f"Владелец: {self.owner} | "
            f"Номер: ****{self.account_number[-4:]} | "
            f"Статус: {self.status} | "
            f"Баланс: {self._balance:.2f} {self.currency} | "
            f"Овердрафт: {self.overdraft_limit:.2f} | "
            f"Лимит снятия: {self.withdrawal_limit:.2f} | "
            f"Комиссия: {self.transaction_fee:.2f}"
        )

class InvestmentAccount(BankAccount):

    def __init__(self, account_number=None, owner=None, balance=0,
                 status="active", currency="USD"):

        super().__init__(
            account_number, owner, balance, status, currency
        )

        self.portfolio = {
            "stocks": 0,
            "bonds": 0,
            "etf": 0
        }

    def invest(self, asset_type, amount):

        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт")

        if asset_type not in self.portfolio:
            raise InvalidOperationError("Недопустимый тип актива")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма инвестиции должна быть положительным конечным числом"
            )

        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно средств для инвестиции")

        self._balance -= amount
        self.portfolio[asset_type] += amount

        print("Инвестировано:", amount, "в", asset_type)

    def project_yearly_growth(self, growth_rates):

        if not isinstance(growth_rates, dict):
            raise InvalidOperationError("Ставки должны быть словарём")

        total_growth = 0

        for asset_type, amount in self.portfolio.items():

            if asset_type not in growth_rates:
                raise InvalidOperationError(
                    "Отсутствует ставка для актива: " + asset_type
                )

            rate = growth_rates[asset_type]

            if not isinstance(rate, (int, float)) or isinstance(rate, bool):
                raise InvalidOperationError("Ставка должна быть числом")

            if not isfinite(rate) or rate < 0:
                raise InvalidOperationError(
                    "Ставка должна быть конечной и неотрицательной"
                )

            growth = amount * rate

            total_growth += growth

        return total_growth

    def withdraw(self, amount):

        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")

        if self.status == "closed":
            raise AccountClosedError("Счёт закрыт")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма снятия должна быть положительным конечным числом"
            )

        if amount > self._balance:
            raise InsufficientFundsError(
                "Недостаточно свободных средств для снятия"
            )

        super().withdraw(amount)

    def get_account_info(self):

        info = super().get_account_info()

        invested_amount = sum(self.portfolio.values())
        total_amount = self._balance + invested_amount

        info["account_type"] = "InvestmentAccount"
        info["portfolio"] = self.portfolio.copy()
        info["invested_amount"] = invested_amount
        info["total_amount"] = total_amount

        return info

    def __str__(self):

        invested_amount = sum(self.portfolio.values())
        total_amount = self._balance + invested_amount

        return (
            f"InvestmentAccount | "
            f"Владелец: {self.owner} | "
            f"Номер: ****{self.account_number[-4:]} | "
            f"Статус: {self.status} | "
            f"Свободный баланс: {self._balance:.2f} {self.currency} | "
            f"Инвестировано: {invested_amount:.2f} {self.currency} | "
            f"Всего средств: {total_amount:.2f} {self.currency}"
        )

class Client:

    def __init__(self, full_name, age, phone, email, password="1234"):

        if not isinstance(full_name, str) or not full_name.strip():
            raise InvalidOperationError("ФИО клиента должно быть непустой строкой")

        if not isinstance(age, int) or isinstance(age, bool):
            raise InvalidOperationError("Возраст должен быть целым числом")

        if age < 18:
            raise InvalidOperationError("Клиент должен быть старше 17 лет")

        self.client_id = str(uuid4())[:8]
        self.full_name = full_name
        self.age = age
        self.phone = phone
        self.email = email
        self.status = "active"
        self.account_numbers = []

        if not isinstance(password, str) or not password:
            raise InvalidOperationError(
                "Пароль должен быть непустой строкой"
            )

        self.password = password
        self.failed_login_attempts = 0


class Bank:

    def __init__(self, name):

        self.name = name
        self.clients = {}
        self.accounts = {}
        self.suspicious_activities = []


    def add_client(self, client):

        if not isinstance(client, Client):
            raise InvalidOperationError(
                "Можно добавлять только объекты Client"
            )

        if client.client_id in self.clients:
            raise InvalidOperationError(
                "Клиент уже зарегистрирован в банке"
            )

        self.clients[client.client_id] = client

        print("Клиент добавлен:", client.full_name)


    def open_account(self, client_id, account):

        if client_id not in self.clients:
            raise InvalidOperationError(
                "Клиент не зарегистрирован в банке"
            )

        if not isinstance(account, BankAccount):
            raise InvalidOperationError(
                "Можно открывать только банковские счета"
            )

        client = self.clients[client_id]

        if client.status != "active":
            raise InvalidOperationError(
                "Клиент заблокирован"
            )

        if account.owner != client.full_name:
            raise InvalidOperationError(
                "Владелец счёта не совпадает с клиентом"
            )

        if account.status != "active":
            raise InvalidOperationError(
                "Можно открывать только активные счета"
            )

        if account.account_number in self.accounts:
            raise InvalidOperationError(
                "Счёт уже зарегистрирован в банке"
            )

        self.accounts[account.account_number] = account

        client.account_numbers.append(account.account_number)

        print("Счёт открыт для клиента:", client.full_name)


    def freeze_account(self, account_number):

        if account_number not in self.accounts:
            raise InvalidOperationError(
                "Счёт не найден в банке"
            )

        account = self.accounts[account_number]

        if account.status == "closed":
            raise AccountClosedError(
                "Нельзя заморозить закрытый счёт"
            )

        if account.status == "frozen":
            raise InvalidOperationError(
                "Счёт уже заморожен"
            )

        account.status = "frozen"

        print("Счёт заморожен:", account_number)


    def unfreeze_account(self, account_number):

        if account_number not in self.accounts:
            raise InvalidOperationError(
                "Счёт не найден в банке"
            )

        account = self.accounts[account_number]

        if account.status == "closed":
            raise AccountClosedError(
                "Нельзя разморозить закрытый счёт"
            )

        if account.status == "active":
            raise InvalidOperationError(
                "Счёт уже активен"
            )

        account.status = "active"

        print("Счёт разморожен:", account_number)


    def close_account(self, account_number):

        if account_number not in self.accounts:
            raise InvalidOperationError(
                "Счёт не найден в банке"
            )

        account = self.accounts[account_number]

        if account.status == "closed":
            raise AccountClosedError(
                "Счёт уже закрыт"
            )

        if account._balance != 0:
            raise InvalidOperationError(
                "Нельзя закрыть счёт с ненулевым балансом"
            )

        if isinstance(account, InvestmentAccount):
            if sum(account.portfolio.values()) != 0:
                raise InvalidOperationError(
                    "Нельзя закрыть счёт с активными инвестициями"
                )

        account.status = "closed"

        print("Счёт закрыт:", account_number)


    def flag_suspicious_activity(self, client_id, reason):

        activity = {
            "client_id": client_id,
            "reason": reason
        }

        self.suspicious_activities.append(activity)

        print("Подозрительное действие:", reason)

    def check_operation_time(self, current_hour=None, client_id=None):

        if current_hour is None:
            current_hour = datetime.now().hour

        if not isinstance(current_hour, int) or isinstance(current_hour, bool):
            raise InvalidOperationError("Час должен быть целым числом")

        if current_hour < 0 or current_hour > 23:
            raise InvalidOperationError("Час должен быть от 0 до 23")

        if 0 <= current_hour < 5:

            if client_id is not None:
                self.flag_suspicious_activity(
                    client_id,
                    "Попытка банковской операции в запрещённое время"
                )

            raise InvalidOperationError(
                "Банковские операции запрещены с 00:00 до 05:00"
            )

        return True

    def withdraw(self, client_id, account_number, amount, current_hour=None):

        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден в банке")

        client = self.clients[client_id]

        if client.status != "active":
            raise InvalidOperationError("Клиент заблокирован")

        if account_number not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")

        if account_number not in self.accounts:
            raise InvalidOperationError("Счёт не найден в банке")

        self.check_operation_time(current_hour, client_id)

        account = self.accounts[account_number]

        account.withdraw(amount)

        print("Банк успешно выполнил снятие денег")

    def deposit(self, client_id, account_number, amount, current_hour=None):

        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден в банке")

        client = self.clients[client_id]

        if client.status != "active":
            raise InvalidOperationError("Клиент заблокирован")

        if account_number not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")

        if account_number not in self.accounts:
            raise InvalidOperationError("Счёт не найден в банке")

        self.check_operation_time(current_hour, client_id)

        account = self.accounts[account_number]

        account.deposit(amount)

        print("Банк успешно выполнил пополнение счёта")


    def search_accounts(self, client_id=None, status=None, account_number=None):

        results = []

        if status is not None and status not in ("active", "frozen", "closed"):
            raise InvalidOperationError(
                "Недопустимый статус для поиска счетов"
            )

        if client_id is not None and client_id not in self.clients:
            raise InvalidOperationError(
                "Клиент не найден в банке"
    )

        for account in self.accounts.values():

            if client_id is not None:
                if client_id not in self.clients:
                    raise InvalidOperationError("Клиент не найден в банке")

                client = self.clients[client_id]

                if account.account_number not in client.account_numbers:
                    continue

            if status is not None:
                if account.status != status:
                    continue

            if account_number is not None:
                if account.account_number != account_number:
                    continue

            results.append(account)

        return results


    def get_total_balance(self):

        total = 0

        for account in self.accounts.values():

            total += account._balance

            if isinstance(account, InvestmentAccount):
                total += sum(account.portfolio.values())

        return total


    def get_clients_ranking(self):

        ranking = []

        for client in self.clients.values():

            total = 0

            for account_number in client.account_numbers:

                account = self.accounts[account_number]

                total += account._balance

                if isinstance(account, InvestmentAccount):
                    total += sum(account.portfolio.values())

            ranking.append({
                "client_id": client.client_id,
                "full_name": client.full_name,
                "total_balance": total
            })

        ranking.sort(
            key=lambda client: client["total_balance"],
            reverse=True
        )

        return ranking


    def authenticate_client(self, client_id, password):

        if client_id not in self.clients:
            raise InvalidOperationError(
                "Клиент не найден в банке"
            )

        client = self.clients[client_id]

        if client.status == "blocked":

            self.flag_suspicious_activity(
                client_id,
                "Попытка входа заблокированного клиента"
            )

            raise InvalidOperationError(
                "Клиент заблокирован"
            )

        if password == client.password:
            client.failed_login_attempts = 0
            print("Вход выполнен успешно:", client.full_name)
            return True

        client.failed_login_attempts += 1

        print(
            "Неверный пароль. Попытка:",
            client.failed_login_attempts
        )

        if client.failed_login_attempts >= 3:

            client.status = "blocked"

            self.flag_suspicious_activity(
                client_id,
                "Три неправильные попытки входа"
            )

            print("Клиент заблокирован после трёх неверных попыток")

        return False


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


    print("\n--- DAY2: SAVINGS ACCOUNT ---")

    savings1 = SavingsAccount(
        owner="Alex",
        balance=1000,
        min_balance=200,
        monthly_interest_rate=0.01
    )

    print(savings1)
    print("Минимальный остаток:", savings1.min_balance)
    print("Месячная ставка:", savings1.monthly_interest_rate)


    print("\nПроверка снятия денег:")

    savings1.withdraw(500)
    print(savings1)

    try:
        savings1.withdraw(400)
    except InsufficientFundsError as error:
        print("Ошибка:", error)



    print("\nПроверка начисления процентов:")

    savings1.apply_monthly_interest()

    print(savings1)


    print("\nПроверка информации о сберегательном счёте:")

    print(savings1.get_account_info())
    print(savings1)



    print("\nПроверка неправильного минимального остатка:")

    try:
        savings_invalid = SavingsAccount(
            owner="Peter",
            balance=1000,
            min_balance=-200
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)



    print("\nПроверка минимального остатка больше баланса:")

    try:
        savings_invalid2 = SavingsAccount(
            owner="Anna",
            balance=1000,
            min_balance=1500
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)



    print("\nПроверка отрицательной процентной ставки:")

    try:
        savings_invalid3 = SavingsAccount(
            owner="John",
            balance=1000,
            min_balance=200,
            monthly_interest_rate=-0.05
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)



    print("\n--- DAY2: PREMIUM ACCOUNT ---")

    premium1 = PremiumAccount(
        owner="Michael",
        balance=1000,
        overdraft_limit=500,
        withdrawal_limit=10000,
        transaction_fee=5
    )

    print(premium1)
    print("Лимит овердрафта:", premium1.overdraft_limit)
    print("Лимит снятия:", premium1.withdrawal_limit)
    print("Комиссия:", premium1.transaction_fee)




    print("\nПроверка снятия с овердрафтом:")

    premium1.withdraw(1200)

    print("Баланс после снятия:", premium1.get_account_info()["balance"])

    try:
        premium1.withdraw(400)
    except InsufficientFundsError as error:
        print("Ошибка:", error)


    print("\nПроверка информации о премиальном счёте:")

    print(premium1.get_account_info())
    print(premium1)



    print("\nПроверка пополнения PremiumAccount:")

    premium1.deposit(300)

    print(premium1)


    print("\nПроверка превышения лимита снятия:")

    try:
        premium1.withdraw(12000)
    except InvalidOperationError as error:
        print("Ошибка:", error)


    print("\nПроверка замороженного PremiumAccount:")

    premium2 = PremiumAccount(
        owner="Anna",
        balance=5000,
        status="frozen",
        overdraft_limit=1000,
        withdrawal_limit=20000,
        transaction_fee=10
    )

    print(premium2)

    try:
        premium2.withdraw(100)
    except AccountFrozenError as error:
        print("Ошибка:", error)



    print("\n--- DAY2: INVESTMENT ACCOUNT ---")

    investment1 = InvestmentAccount(
        owner="David",
        balance=10000
    )

    print(investment1)
    print("Инвестиционный портфель:", investment1.portfolio)



    print("\nПроверка инвестирования:")

    investment1.invest("stocks", 3000)
    investment1.invest("bonds", 2000)
    investment1.invest("etf", 1000)

    print("Свободный баланс:", investment1.get_account_info()["balance"])
    print("Инвестиционный портфель:", investment1.portfolio)



    print("\nПроверка годового прироста инвестиций:")

    growth_rates = {
        "stocks": 0.10,
        "bonds": 0.04,
        "etf": 0.07
    }

    yearly_growth = investment1.project_yearly_growth(growth_rates)

    print("Ожидаемый годовой прирост:", yearly_growth, "USD")
    print("Свободный баланс после прогноза:", investment1._balance)
    print("Портфель после прогноза:", investment1.portfolio)




    print("\nПроверка снятия денег с инвестиционного счёта:")

    investment1.withdraw(1000)

    print("Свободный баланс:", investment1._balance)
    print("Портфель:", investment1.portfolio)

    try:
        investment1.withdraw(5000)
    except InsufficientFundsError as error:
        print("Ошибка:", error)



    print("\nПроверка информации об инвестиционном счёте:")

    print(investment1.get_account_info())
    print(investment1)



    print("\n--- DAY2: ПРОВЕРКА ОШИБОК ИНВЕСТИРОВАНИЯ ---")

    # Тест 1. Недопустимый тип актива
    try:
        investment1.invest("gold", 500)
    except InvalidOperationError as error:
        print("Тест 1. Ошибка:", error)


    # Тест 2. Отрицательная сумма
    try:
        investment1.invest("stocks", -100)
    except InvalidOperationError as error:
        print("Тест 2. Ошибка:", error)


    # Тест 3. Недостаточно свободных средств
    try:
        investment1.invest("etf", 5000)
    except InsufficientFundsError as error:
        print("Тест 3. Ошибка:", error)


    print("Свободный баланс после тестов:", investment1._balance)
    print("Портфель после тестов:", investment1.portfolio)



    print("\n--- DAY2: ПРОВЕРКА ПОЛИМОРФИЗМА ---")

    accounts = [savings1, premium1, investment1]

    for account in accounts:
        print("\nТип объекта:", type(account).__name__)
        print(account)
        print("Информация:", account.get_account_info())


    print("\n--- DAY2: ПРОВЕРКА СТАВОК ДОХОДНОСТИ ---")

    # Тест 1. Отсутствует ставка для ETF
    try:
        investment1.project_yearly_growth({
            "stocks": 0.10,
            "bonds": 0.04
        })
    except InvalidOperationError as error:
        print("Тест 1. Ошибка:", error)


    # Тест 2. Отрицательная ставка
    try:
        investment1.project_yearly_growth({
            "stocks": -0.10,
            "bonds": 0.04,
            "etf": 0.07
        })
    except InvalidOperationError as error:
        print("Тест 2. Ошибка:", error)

    # Тест 3. Ставка передана как строка
    try:
        investment1.project_yearly_growth({
            "stocks": "10%",
            "bonds": 0.04,
            "etf": 0.07
        })
    except InvalidOperationError as error:
        print("Тест 3. Ошибка:", error)



    print("\n--- DAY2: ДОПОЛНИТЕЛЬНЫЕ СЧЕТА ---")

    # Второй сберегательный счёт
    savings2 = SavingsAccount(
        owner="Emma",
        balance=5000,
        min_balance=1000,
        monthly_interest_rate=0.02
    )

    print("\nВторой SavingsAccount:")
    print(savings2)

    savings2.deposit(500)
    savings2.apply_monthly_interest()

    print("После операций:")
    print(savings2)


    # Второй инвестиционный счёт
    investment2 = InvestmentAccount(
        owner="Sophia",
        balance=20000
    )

    print("\nВторой InvestmentAccount:")
    print(investment2)

    investment2.invest("stocks", 5000)
    investment2.invest("bonds", 3000)
    investment2.invest("etf", 2000)

    print("После инвестирования:")
    print(investment2)

    growth2 = investment2.project_yearly_growth({
        "stocks": 0.10,
        "bonds": 0.04,
        "etf": 0.07
    })

    print("Ожидаемый годовой прирост:", growth2, "USD")



    print("\nПроверка замороженного инвестиционного счёта:")

    investment3 = InvestmentAccount(
        owner="Robert",
        balance=5000,
        status="frozen"
    )

    try:
        investment3.invest("stocks", 1000)
    except AccountFrozenError as error:
        print("Ошибка:", error)

    try:
        investment3.withdraw(500)
    except AccountFrozenError as error:
        print("Ошибка:", error)



    print("\nПроверка защиты инвестиционного портфеля:")

    info = investment1.get_account_info()

    info["portfolio"]["stocks"] = 999999

    print("Изменённая копия:", info["portfolio"])
    print("Настоящий портфель:", investment1.portfolio)



    print("\n--- DAY3: CLIENT ---")

    client1 = Client(
        full_name="Alex Johnson",
        age=25,
        phone="+1234567890",
        email="alex@example.com"
    )

    print("ID клиента:", client1.client_id)
    print("ФИО:", client1.full_name)
    print("Возраст:", client1.age)
    print("Телефон:", client1.phone)
    print("Email:", client1.email)
    print("Статус:", client1.status)
    print("Счета:", client1.account_numbers)



    print("\n--- DAY3: ПРОВЕРКА ВОЗРАСТА КЛИЕНТА ---")

    # Тест 1. Клиент младше 18 лет
    try:
        client2 = Client(
            full_name="John Smith",
            age=16,
            phone="+1234567890",
            email="john@example.com"
        )
    except InvalidOperationError as error:
        print("Тест 1. Ошибка:", error)


    # Тест 2. Клиенту ровно 18 лет
    client3 = Client(
        full_name="Emma Wilson",
        age=18,
        phone="+1987654321",
        email="emma@example.com"
    )

    print("Тест 2. Клиент создан:", client3.full_name)
    print("Возраст:", client3.age)



    print("\n--- DAY3: BANK ---")

    bank = Bank("My First Bank")

    print("Название банка:", bank.name)
    print("Клиенты:", bank.clients)
    print("Счета:", bank.accounts)


    print("\n--- DAY3: ДОБАВЛЕНИЕ КЛИЕНТОВ ---")

    bank.add_client(client1)
    bank.add_client(client3)

    print("Количество клиентов:", len(bank.clients))

    for client_id, client in bank.clients.items():
        print("ID:", client_id, "| ФИО:", client.full_name)




    print("\n--- DAY3: ПОВТОРНАЯ РЕГИСТРАЦИЯ ---")

    try:
        bank.add_client(client1)
    except InvalidOperationError as error:
        print("Ошибка:", error)

    print("Количество клиентов:", len(bank.clients))



    print("\n--- DAY3: ОТКРЫТИЕ БАНКОВСКИХ СЧЕТОВ ---")

    # Открываем сберегательный счёт для Alex
    alex_savings = SavingsAccount(
        owner="Alex Johnson",
        balance=5000,
        min_balance=1000,
        monthly_interest_rate=0.01
    )

    bank.open_account(client1.client_id, alex_savings)

    print("Счета Alex:", client1.account_numbers)

    # Открываем инвестиционный счёт для Emma
    emma_investment = InvestmentAccount(
        owner="Emma Wilson",
        balance=10000
    )

    bank.open_account(client3.client_id, emma_investment)

    print("Счета Emma:", client3.account_numbers)

    print("Всего счетов в банке:", len(bank.accounts))



    print("\n--- DAY3: ЗАМОРОЗКА СЧЁТА ---")

    print("Статус до заморозки:", alex_savings.status)

    bank.freeze_account(alex_savings.account_number)

    print("Статус после заморозки:", alex_savings.status)

    try:
        alex_savings.withdraw(500)
    except AccountFrozenError as error:
        print("Ошибка:", error)



    print("\n--- DAY3: РАЗМОРОЗКА СЧЁТА ---")

    print("Статус до разморозки:", alex_savings.status)

    bank.unfreeze_account(alex_savings.account_number)

    print("Статус после разморозки:", alex_savings.status)

    alex_savings.withdraw(500)

    print("Баланс после снятия:", alex_savings.get_account_info()["balance"])



    print("\n--- DAY3: ЗАКРЫТИЕ СЧЁТА ---")

    # Проверяем попытку закрыть счёт с деньгами
    try:
        bank.close_account(alex_savings.account_number)
    except InvalidOperationError as error:
        print("Ошибка:", error)


    # Создаём новый счёт с нулевым балансом
    empty_account = BankAccount(
        owner="Alex Johnson",
        balance=0
    )

    bank.open_account(client1.client_id, empty_account)

    print("Статус до закрытия:", empty_account.status)

    bank.close_account(empty_account.account_number)

    print("Статус после закрытия:", empty_account.status)


    # Проверяем, что закрытый счёт нельзя пополнить
    try:
        empty_account.deposit(100)
    except AccountClosedError as error:
        print("Ошибка:", error)



    print("\n--- DAY3: ПОДГОТОВКА АУТЕНТИФИКАЦИИ ---")

    print("Клиент:", client1.full_name)
    print("Количество неправильных попыток:", client1.failed_login_attempts)
    print("Статус клиента:", client1.status)


    print("\n--- DAY3: УСПЕШНАЯ АУТЕНТИФИКАЦИЯ ---")

    result = bank.authenticate_client(
        client1.client_id,
        "1234"
    )

    print("Результат входа:", result)
    print("Количество ошибок:", client1.failed_login_attempts)
    print("Статус клиента:", client1.status)



    print("\n--- DAY3: ТРИ НЕПРАВИЛЬНЫЕ ПОПЫТКИ ---")

    for i in range(3):
        result = bank.authenticate_client(
            client3.client_id,
            "wrong_password"
        )

        print("Результат входа:", result)

    print("Количество ошибок:", client3.failed_login_attempts)
    print("Статус клиента:", client3.status)


    print("\n--- DAY3: ВХОД ПОСЛЕ БЛОКИРОВКИ ---")

    try:
        bank.authenticate_client(
            client3.client_id,
            "1234"
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)



    print("\n--- DAY3: ПОДОЗРИТЕЛЬНЫЕ ДЕЙСТВИЯ ---")

    for activity in bank.suspicious_activities:
        print(activity)

    print(
        "Всего подозрительных действий:",
        len(bank.suspicious_activities)
    )


    print("\n--- DAY3: ПРОВЕРКА НОЧНОГО ОГРАНИЧЕНИЯ ---")

    for hour in [0, 2, 4, 5, 12, 23]:
        try:
            result = bank.check_operation_time(hour)
            print(f"{hour:02d}:00 — операция разрешена:", result)
        except InvalidOperationError as error:
            print(f"{hour:02d}:00 — ошибка:", error)


    print("\n--- DAY3: ПОДОЗРИТЕЛЬНАЯ НОЧНАЯ ОПЕРАЦИЯ ---")

    try:
        bank.check_operation_time(
            current_hour=2,
            client_id=client1.client_id
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)

    print("\nИстория подозрительных действий:")

    for activity in bank.suspicious_activities:
        print(activity)

    print(
        "Всего подозрительных действий:",
        len(bank.suspicious_activities)
    )


    print("\n--- DAY3: ПРОВЕРКА НОЧНОГО СНЯТИЯ ---")

    balance_before = alex_savings.get_account_info()["balance"]

    print("Баланс до операции:", balance_before)

    try:
        bank.withdraw(
            client_id=client1.client_id,
            account_number=alex_savings.account_number,
            amount=500,
            current_hour=2
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)

    balance_after = alex_savings.get_account_info()["balance"]

    print("Баланс после операции:", balance_after)

    print(
        "Количество подозрительных действий:",
        len(bank.suspicious_activities)
    )



    print("\n--- DAY3: ДНЕВНОЕ СНЯТИЕ ДЕНЕГ ---")

    print("Баланс до снятия:", alex_savings._balance)

    bank.withdraw(
        client_id=client1.client_id,
        account_number=alex_savings.account_number,
        amount=500,
        current_hour=12
    )

    print("Баланс после снятия:", alex_savings._balance)

    print(
        "Количество подозрительных действий:",
        len(bank.suspicious_activities)
    )


    print("\n--- DAY3: ПРОВЕРКА ПОПОЛНЕНИЯ ---")

    print("Начальный баланс:", alex_savings._balance)

    # Пополнение в 12:00
    bank.deposit(
        client_id=client1.client_id,
        account_number=alex_savings.account_number,
        amount=1000,
        current_hour=12
    )

    print("Баланс после дневного пополнения:", alex_savings._balance)

    # Попытка пополнения в 02:00
    try:
        bank.deposit(
            client_id=client1.client_id,
            account_number=alex_savings.account_number,
            amount=500,
            current_hour=2
        )
    except InvalidOperationError as error:
        print("Ошибка:", error)

    print("Баланс после ночной попытки:", alex_savings._balance)

    print(
        "Количество подозрительных действий:",
        len(bank.suspicious_activities)
    )



    print("\n--- DAY3: ПОИСК БАНКОВСКИХ СЧЕТОВ ---")

    print("\nВсе счета Alex:")
    for account in bank.search_accounts(client_id=client1.client_id):
        print(account)

    print("\nВсе закрытые счета:")
    for account in bank.search_accounts(status="closed"):
        print(account)

    print("\nПоиск по номеру счёта:")
    for account in bank.search_accounts(
        account_number=alex_savings.account_number
    ):
        print(account)

    print("\nКоличество счетов в банке:", len(bank.accounts))


    print("\n--- DAY3: ОБЩИЙ БАЛАНС БАНКА ---")

    total_balance = bank.get_total_balance()

    print("Общая сумма средств в банке:", total_balance)



    print("\n--- DAY3: РЕЙТИНГ КЛИЕНТОВ ---")

    ranking = bank.get_clients_ranking()

    for position, client in enumerate(ranking, start=1):
        print(
            f"{position}. {client['full_name']} — "
            f"{client['total_balance']} USD"
        )


    print("\n--- DAY3: ПРОВЕРКА ОШИБОК ПОИСКА ---")

    try:
        bank.search_accounts(status="unknown")
    except InvalidOperationError as error:
        print("Тест 1. Ошибка:", error)

    try:
        bank.search_accounts(client_id="nonexistent")
    except InvalidOperationError as error:
        print("Тест 2. Ошибка:", error)