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

        # Банк, в котором зарегистрирован счёт
        # Пока счёт не зарегистрирован, значение None
        self._bank = None

        # Разрешена ли сейчас финансовая операция банком
        self._operation_authorized = False

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
        if self._bank is not None and not self._operation_authorized:
            raise InvalidOperationError(
                "Пополнение должно выполняться через банк"
            )

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
        if self._bank is not None and not self._operation_authorized:
            raise InvalidOperationError(
                "Снятие должно выполняться через банк"
    )

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

        if self._bank is not None and not self._operation_authorized:
            raise InvalidOperationError(
                "Снятие с премиального счёта должно выполняться через банк"
            )

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

        if self._bank is not None and not self._operation_authorized:
            raise InvalidOperationError(
                "Инвестирование должно выполняться через банк"
            )

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

class CurrencyConverter:
    """
    Конвертация валют по фиксированным учебным курсам.
    Курс показывает, сколько единиц валюты дают за 1 USD.
    Используется и банком (итоги, рейтинг), и процессором транзакций.
    """

    EXCHANGE_RATES = {
        "USD": 1,
        "EUR": 0.92,
        "RUB": 90,
        "KZT": 450,
        "CNY": 7.2
    }

    @classmethod
    def convert(cls, amount, from_currency, to_currency):

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом")

        if not isfinite(amount):
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if from_currency not in cls.EXCHANGE_RATES:
            raise InvalidOperationError("Неизвестная исходная валюта")

        if to_currency not in cls.EXCHANGE_RATES:
            raise InvalidOperationError("Неизвестная валюта получателя")

        if from_currency == to_currency:
            return amount

        amount_in_usd = amount / cls.EXCHANGE_RATES[from_currency]

        return amount_in_usd * cls.EXCHANGE_RATES[to_currency]

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

        if account._bank is not None:
            raise InvalidOperationError(
                "Счёт уже зарегистрирован в другом банке"
            )

        self.accounts[account.account_number] = account

        client.account_numbers.append(account.account_number)

        # Связываем банковский счёт с банком
        account._bank = self

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

        try:
            account._operation_authorized = True
            account.withdraw(amount)
        finally:
            account._operation_authorized = False

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

        try:
            account._operation_authorized = True
            account.deposit(amount)
        finally:
            account._operation_authorized = False

        print("Банк успешно выполнил пополнение счёта")

    def invest(self, client_id, account_number, asset_type, amount, current_hour=None):

        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден в банке")

        client = self.clients[client_id]

        if client.status != "active":
            raise InvalidOperationError("Клиент заблокирован")

        if account_number not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")

        if account_number not in self.accounts:
            raise InvalidOperationError("Счёт не найден в банке")

        account = self.accounts[account_number]

        if not isinstance(account, InvestmentAccount):
            raise InvalidOperationError("Инвестировать можно только с инвестиционного счёта")

        self.check_operation_time(current_hour, client_id)

        try:
            account._operation_authorized = True
            account.invest(asset_type, amount)
        finally:
            account._operation_authorized = False

        print("Банк успешно выполнил инвестиционную операцию")


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


    @staticmethod
    def _get_account_total(account):
        """Все средства счёта: свободный баланс + инвестиционный портфель."""

        total = account._balance

        if isinstance(account, InvestmentAccount):
            total += sum(account.portfolio.values())

        return total

    @staticmethod
    def _validate_base_currency(base_currency):

        if base_currency not in CurrencyConverter.EXCHANGE_RATES:
            raise InvalidOperationError("Недопустимая базовая валюта")

    def get_total_balance(self, base_currency="USD"):
        """
        Возвращает:
        - by_currency — суммы отдельно по каждой валюте (без конвертации);
        - total — общая сумма, приведённая к базовой валюте.
        """

        self._validate_base_currency(base_currency)

        by_currency = {}
        total = 0

        for account in self.accounts.values():

            amount = self._get_account_total(account)
            currency = account.currency

            by_currency[currency] = by_currency.get(currency, 0) + amount

            total += CurrencyConverter.convert(
                amount, currency, base_currency
            )

        return {
            "base_currency": base_currency,
            "by_currency": by_currency,
            "total": round(total, 2)
        }


    def get_clients_ranking(self, base_currency="USD"):
        """
        Единый рейтинг клиентов: средства всех счетов клиента
        переводятся в базовую валюту, затем клиенты сортируются.
        """

        self._validate_base_currency(base_currency)

        ranking = []

        for client in self.clients.values():

            by_currency = {}
            total = 0

            for account_number in client.account_numbers:

                account = self.accounts[account_number]
                amount = self._get_account_total(account)
                currency = account.currency

                by_currency[currency] = by_currency.get(currency, 0) + amount

                total += CurrencyConverter.convert(
                    amount, currency, base_currency
                )

            ranking.append({
                "client_id": client.client_id,
                "full_name": client.full_name,
                "total_balance": round(total, 2),
                "base_currency": base_currency,
                "balances_by_currency": by_currency
            })

        ranking.sort(
            key=lambda item: item["total_balance"],
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

class Transaction:

    def __init__(
        self,
        transaction_type,
        amount,
        currency,
        sender,
        receiver,
        fee=0,
        priority=1,
        scheduled_at=None,
        is_external=False
    ):

        if transaction_type not in ("transfer", "deposit", "withdraw"):
            raise InvalidOperationError(
                "Недопустимый тип транзакции"
            )

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError(
                "Сумма транзакции должна быть числом"
            )

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма транзакции должна быть положительным конечным числом"
            )

        if currency not in ("USD", "EUR", "RUB", "KZT", "CNY"):
            raise InvalidOperationError(
                "Недопустимая валюта транзакции"
            )

        if not isinstance(fee, (int, float)) or isinstance(fee, bool):
            raise InvalidOperationError(
                "Комиссия должна быть числом"
            )

        if not isfinite(fee) or fee < 0:
            raise InvalidOperationError(
                "Комиссия должна быть неотрицательным конечным числом"
            )

        self.transaction_id = str(uuid4())[:8]
        self.transaction_type = transaction_type
        self.amount = amount
        self.currency = currency
        self.sender = sender
        self.receiver = receiver
        self.fee = fee

        if not isinstance(is_external, bool):
            raise InvalidOperationError(
                "Признак внешнего перевода должен быть True или False"
            )

        self.is_external = is_external

        if type(priority) is not int or priority not in (1, 2, 3):
            raise InvalidOperationError(
                "Приоритет должен быть целым числом от 1 до 3"
            )

        self.priority = priority

        if scheduled_at is not None and not isinstance(scheduled_at, datetime):
            raise InvalidOperationError(
                "Время отложенной операции должно быть datetime"
            )

        self.scheduled_at = scheduled_at

        self.status = "pending"
        self.failure_reason = None

        self.created_at = datetime.now()
        self.completed_at = None

    def complete(self):

        if self.status != "pending":
            raise InvalidOperationError(
                "Завершить можно только ожидающую транзакцию"
            )

        self.status = "completed"
        self.failure_reason = None
        self.completed_at = datetime.now()

    def fail(self, reason):

        if self.status != "pending":
            raise InvalidOperationError(
                "Отклонить можно только ожидающую транзакцию"
            )

        if not isinstance(reason, str) or not reason.strip():
            raise InvalidOperationError(
                "Необходимо указать причину отказа"
            )

        self.status = "failed"
        self.failure_reason = reason
        self.completed_at = datetime.now()

class TransactionQueue:

    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):

        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(
                "В очередь можно добавлять только объекты Transaction"
            )

        if transaction.status != "pending":
            raise InvalidOperationError(
                "В очередь можно добавлять только ожидающие транзакции"
            )

        self.transactions.append(transaction)
        self.transactions.sort(
            key=lambda transaction: transaction.priority,
            reverse=True
        )

        print("Транзакция добавлена в очередь:", transaction.transaction_id)


    def get_ready_transactions(self):

        ready_transactions = []
        current_time = datetime.now()

        for transaction in self.transactions:

            if transaction.status != "pending":
                continue

            if transaction.scheduled_at is None:
                ready_transactions.append(transaction)

            elif transaction.scheduled_at <= current_time:
                ready_transactions.append(transaction)

        return ready_transactions


    def cancel_transaction(self, transaction_id):

        for transaction in self.transactions:

            if transaction.transaction_id == transaction_id:

                if transaction.status != "pending":
                    raise InvalidOperationError(
                        "Отменить можно только ожидающую транзакцию"
                    )

                transaction.status = "cancelled"
                transaction.failure_reason = "Отменена пользователем"
                transaction.completed_at = datetime.now()

                print("Транзакция отменена:", transaction_id)

                return True

        raise InvalidOperationError(
            "Транзакция не найдена в очереди"
        )

class TransactionProcessor:

    def __init__(self, bank):
        self.bank = bank
        self.processed_transactions = []
        self.error_log = []

    def get_transaction_count(self):
        return len(self.processed_transactions)

    def calculate_fee(self, amount, is_external=False):

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError(
                "Сумма должна быть числом"
            )

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительным конечным числом"
            )

        if is_external:
            return round(amount * 0.02, 2)

        return 0

    def convert_currency(self, amount, from_currency, to_currency):

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidOperationError(
                "Сумма должна быть числом"
            )

        if not isfinite(amount) or amount <= 0:
            raise InvalidOperationError(
                "Сумма должна быть положительным конечным числом"
            )

        converted_amount = CurrencyConverter.convert(
            amount, from_currency, to_currency
        )

        return round(converted_amount, 2)

    def calculate_total_amount(self, amount, is_external=False):

        fee = self.calculate_fee(amount, is_external)

        total_amount = amount + fee

        return total_amount

    def set_transaction_fee(self, transaction, is_external=False):

        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(
                "Передан неправильный объект транзакции"
            )

        if transaction.status != "pending":
            raise InvalidOperationError(
                "Изменять комиссию можно только у ожидающей транзакции"
            )

        fee = self.calculate_fee(
            transaction.amount,
            is_external
        )

        transaction.fee = fee

        return fee

    def record_error(self, transaction, error):

        error_info = {
            "transaction_id": transaction.transaction_id,
            "error": str(error),
            "timestamp": datetime.now()
        }

        self.error_log.append(error_info)

        if transaction.status == "pending":
            transaction.fail(str(error))

        if transaction not in self.processed_transactions:
            self.processed_transactions.append(transaction)

        print("Ошибка транзакции записана:", error)

    def process_safely(self, transaction, current_hour=None):

        try:
            return self.process_transaction(
                transaction,
                current_hour
            )

        except (
            InvalidOperationError,
            InsufficientFundsError,
            AccountFrozenError,
            AccountClosedError
        ) as error:

            if transaction.status == "pending":
                self.record_error(transaction, error)

            return False

    def process_with_retry(self, transaction, current_hour=None, max_attempts=3):

        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(
                "Передан неправильный объект транзакции"
            )

        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
            raise InvalidOperationError(
                "Количество попыток должно быть целым числом"
            )

        if max_attempts < 1:
            raise InvalidOperationError(
                "Количество попыток должно быть больше нуля"
            )

        for attempt in range(1, max_attempts + 1):

            print("Попытка выполнения:", attempt)

            try:
                return self.process_transaction(
                    transaction,
                    current_hour
                )

            except ConnectionError as error:

                print("Временная ошибка подключения:", error)

                if attempt == max_attempts:
                    self.record_error(transaction, error)
                    return False

            except (
                InvalidOperationError,
                InsufficientFundsError,
                AccountFrozenError,
                AccountClosedError
            ) as error:

                self.record_error(transaction, error)
                return False

    def find_account_owner(self, account_number):

        if account_number not in self.bank.accounts:
            raise InvalidOperationError(
                "Счёт не найден в банке"
            )

        for client in self.bank.clients.values():

            if account_number in client.account_numbers:
                return client

        raise InvalidOperationError(
            "Владелец банковского счёта не найден"
        )

    def process_transaction(self, transaction, current_hour=None):

        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(
                "Передан неправильный объект транзакции"
            )

        if transaction.status != "pending":
            raise InvalidOperationError(
                "Транзакция уже обработана или отменена"
            )

        if transaction.transaction_type != "transfer":
            raise InvalidOperationError(
                "Пока поддерживаются только переводы"
            )

        if transaction.scheduled_at is not None:
            if transaction.scheduled_at > datetime.now():
                raise InvalidOperationError(
                    "Время выполнения транзакции ещё не наступило"
                )

        if transaction.sender not in self.bank.accounts:
            raise InvalidOperationError("Счёт отправителя не найден")

        if transaction.receiver not in self.bank.accounts:
            raise InvalidOperationError("Счёт получателя не найден")

        sender_account = self.bank.accounts[transaction.sender]
        receiver_account = self.bank.accounts[transaction.receiver]

        sender_client = self.find_account_owner(transaction.sender)
        receiver_client = self.find_account_owner(transaction.receiver)

        if transaction.sender == transaction.receiver:
            raise InvalidOperationError(
                "Нельзя переводить деньги на тот же счёт"
            )

        if sender_account.currency != transaction.currency:
            raise InvalidOperationError(
                "Валюта отправителя не совпадает с валютой транзакции"
            )

        received_amount = transaction.amount

        if receiver_account.currency != transaction.currency:
            received_amount = self.convert_currency(
                transaction.amount,
                transaction.currency,
                receiver_account.currency
            )


        if not isinstance(sender_account, (BankAccount, PremiumAccount)):
            raise InvalidOperationError(
                "Неподдерживаемый тип счёта отправителя"
            )

        if type(receiver_account) is not BankAccount:
            raise InvalidOperationError(
                "Пока поддерживается перевод только на обычный счёт"
            )

        if sender_account.status != "active":
            raise InvalidOperationError(
                "Счёт отправителя неактивен"
            )

        if receiver_account.status != "active":
            raise InvalidOperationError(
                "Счёт получателя неактивен"
            )

        if transaction.is_external:
            transaction.fee = self.calculate_fee(
                transaction.amount,
                is_external=True
            )

        total_amount = transaction.amount + transaction.fee

        if isinstance(sender_account, PremiumAccount):

            premium_total = total_amount + sender_account.transaction_fee

            if total_amount > sender_account.withdrawal_limit:
                raise InvalidOperationError(
                    "Превышен лимит снятия премиального счёта"
                )

            if sender_account._balance - premium_total < -sender_account.overdraft_limit:
                raise InsufficientFundsError(
                    "Превышен лимит овердрафта"
                )

        else:

            if sender_account._balance < total_amount:
                raise InsufficientFundsError(
                    "Недостаточно средств для перевода с учётом комиссии"
                )

        self.bank.check_operation_time(
            current_hour, sender_client.client_id
        )

        self.bank.check_operation_time(
            current_hour, receiver_client.client_id
        )

        sender_balance_before = sender_account._balance
        receiver_balance_before = receiver_account._balance

        try:
            self.bank.withdraw(
                sender_client.client_id,
                sender_account.account_number,
                total_amount,
                current_hour
            )

            self.bank.deposit(
                receiver_client.client_id,
                receiver_account.account_number,
                received_amount,
                current_hour
            )

        except Exception:
            sender_account._balance = sender_balance_before
            receiver_account._balance = receiver_balance_before
            raise

        transaction.complete()
        self.processed_transactions.append(transaction)

        print("Перевод успешно выполнен")
        return True


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
        bank.withdraw(
            client1.client_id,
            alex_savings.account_number,
            500,
            current_hour=12
        )
    except AccountFrozenError as error:
        print("Ошибка:", error)



    print("\n--- DAY3: РАЗМОРОЗКА СЧЁТА ---")

    print("Статус до разморозки:", alex_savings.status)

    bank.unfreeze_account(alex_savings.account_number)

    print("Статус после разморозки:", alex_savings.status)

    bank.withdraw(
        client1.client_id,
        alex_savings.account_number,
        500,
        current_hour=12
)

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
        bank.deposit(
            client1.client_id,
            empty_account.account_number,
            100,
            current_hour=12
        )
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

    total_balance = bank.get_total_balance("USD")

    for currency, amount in total_balance["by_currency"].items():
        print(f"Сумма в {currency}: {amount:.2f}")

    print(
        f"Итого в базовой валюте: "
        f"{total_balance['total']:.2f} {total_balance['base_currency']}"
    )



    print("\n--- DAY3: РЕЙТИНГ КЛИЕНТОВ ---")

    ranking = bank.get_clients_ranking("USD")

    for position, client in enumerate(ranking, start=1):

        print(
            f"{position}. {client['full_name']} — "
            f"{client['total_balance']:.2f} {client['base_currency']}"
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


    print("\n--- DAY4: ПЕРВАЯ ТРАНЗАКЦИЯ ---")

    transaction1 = Transaction(
        transaction_type="transfer",
        amount=500,
        currency="USD",
        sender="ACC001",
        receiver="ACC002",
        fee=5
    )

    print("ID транзакции:", transaction1.transaction_id)
    print("Тип:", transaction1.transaction_type)
    print("Сумма:", transaction1.amount)
    print("Валюта:", transaction1.currency)
    print("Отправитель:", transaction1.sender)
    print("Получатель:", transaction1.receiver)
    print("Комиссия:", transaction1.fee)
    print("Статус:", transaction1.status)
    print("Причина отказа:", transaction1.failure_reason)



    print("Время создания:", transaction1.created_at)
    print("Время завершения:", transaction1.completed_at)



    print("\n--- DAY4: УСПЕШНОЕ ЗАВЕРШЕНИЕ ТРАНЗАКЦИИ ---")

    transaction1.complete()

    print("Статус:", transaction1.status)
    print("Причина отказа:", transaction1.failure_reason)
    print("Время завершения:", transaction1.completed_at)


    print("\n--- DAY4: ОТКЛОНЕНИЕ ТРАНЗАКЦИИ ---")

    transaction2 = Transaction(
        transaction_type="transfer",
        amount=1000,
        currency="USD",
        sender="ACC003",
        receiver="ACC004"
    )

    print("Статус до обработки:", transaction2.status)

    transaction2.fail("Недостаточно средств")

    print("Статус после обработки:", transaction2.status)
    print("Причина отказа:", transaction2.failure_reason)
    print("Время завершения:", transaction2.completed_at)



    print("\n--- DAY4: СОЗДАНИЕ ОЧЕРЕДИ ТРАНЗАКЦИЙ ---")

    queue = TransactionQueue()

    transaction3 = Transaction(
        transaction_type="transfer",
        amount=200,
        currency="USD",
        sender="ACC005",
        receiver="ACC006"
    )

    transaction4 = Transaction(
        transaction_type="transfer",
        amount=300,
        currency="USD",
        sender="ACC007",
        receiver="ACC008"
    )

    queue.add_transaction(transaction3)
    queue.add_transaction(transaction4)

    print("Количество транзакций в очереди:", len(queue.transactions))

    for transaction in queue.transactions:
        print(
            "ID:", transaction.transaction_id,
            "| Сумма:", transaction.amount,
            "| Статус:", transaction.status
        )


    print("\n--- DAY4: ПРОВЕРКА ПРИОРИТЕТОВ ---")

    priority_queue = TransactionQueue()

    normal = Transaction(
        "transfer", 200, "USD", "ACC001", "ACC002",
        priority=1
    )

    urgent = Transaction(
        "transfer", 500, "USD", "ACC003", "ACC004",
        priority=3
    )

    medium = Transaction(
        "transfer", 300, "USD", "ACC005", "ACC006",
        priority=2
    )

    priority_queue.add_transaction(normal)
    priority_queue.add_transaction(urgent)
    priority_queue.add_transaction(medium)

    for transaction in priority_queue.transactions:
        print(
            "Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority
        )



    print("\n--- DAY4: ОТЛОЖЕННЫЕ ТРАНЗАКЦИИ ---")

    delayed_queue = TransactionQueue()

    immediate = Transaction(
        "transfer", 100, "USD", "ACC001", "ACC002",
        priority=1
    )

    delayed = Transaction(
        "transfer", 500, "USD", "ACC003", "ACC004",
        priority=3,
        scheduled_at=datetime(2026, 12, 1, 10, 0)
    )

    delayed_queue.add_transaction(immediate)
    delayed_queue.add_transaction(delayed)

    print("Всего транзакций:", len(delayed_queue.transactions))

    ready = delayed_queue.get_ready_transactions()

    print("Готовы к выполнению:", len(ready))

    for transaction in ready:
        print(
            "Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority,
            "| Запланирована:", transaction.scheduled_at
        )



    print("\n--- DAY4: ОТМЕНА ТРАНЗАКЦИИ ---")

    print("Статус до отмены:", delayed.status)

    delayed_queue.cancel_transaction(delayed.transaction_id)

    print("Статус после отмены:", delayed.status)
    print("Причина:", delayed.failure_reason)
    print("Время отмены:", delayed.completed_at)

    ready = delayed_queue.get_ready_transactions()

    print("Всего транзакций в очереди:", len(delayed_queue.transactions))
    print("Готовы к выполнению:", len(ready))




    print("\n--- DAY4: СОЗДАНИЕ ПРОЦЕССОРА ---")

    processor = TransactionProcessor(bank)

    print("Банк:", processor.bank.name)
    print("Обработано транзакций:", processor.get_transaction_count())
    print("Ошибок:", len(processor.error_log))


    print("\n--- DAY4: ПОИСК ВЛАДЕЛЬЦА СЧЁТА ---")

    owner = processor.find_account_owner(
        alex_savings.account_number
    )

    print("Номер счёта:", alex_savings.account_number)
    print("Владелец:", owner.full_name)
    print("ID клиента:", owner.client_id)



    print("\n--- DAY4: ПРОВЕРКА ДАННЫХ ТРАНЗАКЦИИ ---")

    test_amounts = [-100, 0, "500", 500]

    for amount in test_amounts:
        try:
            transaction = Transaction(
                "transfer",
                amount,
                "USD",
                "ACC001",
                "ACC002"
            )

            print("Сумма:", amount, "— транзакция создана")

        except InvalidOperationError as error:
            print("Сумма:", amount, "— ошибка:", error)



    print("\n--- DAY4: ПОДГОТОВКА БАНКОВСКОГО ПЕРЕВОДА ---")

    transfer_client1 = Client(
        "Transfer Sender",
        30,
        "+1234567001",
        "sender@example.com",
        "password123"
    )

    transfer_client2 = Client(
        "Transfer Receiver",
        28,
        "+1234567002",
        "receiver@example.com",
        "password456"
    )

    bank.add_client(transfer_client1)
    bank.add_client(transfer_client2)

    transfer_account1 = BankAccount(
        owner=transfer_client1.full_name,
        balance=1000,
        currency="USD"
    )

    transfer_account2 = BankAccount(
        owner=transfer_client2.full_name,
        balance=200,
        currency="USD"
    )

    bank.open_account(transfer_client1.client_id, transfer_account1)
    bank.open_account(transfer_client2.client_id, transfer_account2)

    print("Отправитель:", transfer_account1)
    print("Получатель:", transfer_account2)



    print("\n--- DAY4: ПЕРВЫЙ БАНКОВСКИЙ ПЕРЕВОД ---")

    first_transfer = Transaction(
        transaction_type="transfer",
        amount=300,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    print("Баланс отправителя до:", transfer_account1._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    processor.process_transaction(
        first_transfer,
        current_hour=12
    )

    print("Баланс отправителя после:", transfer_account1._balance)
    print("Баланс получателя после:", transfer_account2._balance)
    print("Статус транзакции:", first_transfer.status)
    print("Обработано транзакций:", processor.get_transaction_count())



    print("\n--- DAY4: ПРОВЕРКА ЖУРНАЛА ОШИБОК ---")

    failed_transfer = Transaction(
        transaction_type="transfer",
        amount=2000,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    try:
        processor.process_transaction(
            failed_transfer,
            current_hour=12
        )

    except InsufficientFundsError as error:
        processor.record_error(failed_transfer, error)

    print("Статус транзакции:", failed_transfer.status)
    print("Причина отказа:", failed_transfer.failure_reason)
    print("Количество ошибок:", len(processor.error_log))
    print("Обработано транзакций:", processor.get_transaction_count())
    print("Баланс отправителя:", transfer_account1._balance)
    print("Баланс получателя:", transfer_account2._balance)



    print("\n--- DAY4: АВТОМАТИЧЕСКАЯ ОБРАБОТКА ОШИБОК ---")

    automatic_failed_transfer = Transaction(
        transaction_type="transfer",
        amount=3000,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    result = processor.process_safely(
        automatic_failed_transfer,
        current_hour=12
    )

    print("Результат перевода:", result)
    print("Статус:", automatic_failed_transfer.status)
    print("Причина отказа:", automatic_failed_transfer.failure_reason)
    print("Количество ошибок:", len(processor.error_log))
    print("Обработано транзакций:", processor.get_transaction_count())
    print("Баланс отправителя:", transfer_account1._balance)
    print("Баланс получателя:", transfer_account2._balance)



    print("\n--- DAY4: РАСЧЁТ КОМИССИЙ ---")

    amounts = [100, 300, 500, 1000]

    for amount in amounts:

        internal_fee = processor.calculate_fee(
            amount,
            is_external=False
        )

        external_fee = processor.calculate_fee(
            amount,
            is_external=True
        )

        print(
            "Сумма:", amount,
            "| Внутренняя комиссия:", internal_fee,
            "| Внешняя комиссия:", external_fee
        )



    print("\n--- DAY4: ОБЩАЯ СУММА СПИСАНИЯ ---")

    amount = 300

    internal_total = processor.calculate_total_amount(
        amount,
        is_external=False
    )

    external_total = processor.calculate_total_amount(
        amount,
        is_external=True
    )

    print("Сумма перевода:", amount)
    print("Внутренний перевод — всего списать:", internal_total)
    print("Внешний перевод — всего списать:", external_total)



    print("\n--- DAY4: СОХРАНЕНИЕ КОМИССИИ ---")

    fee_test_transaction = Transaction(
        transaction_type="transfer",
        amount=300,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    print("Комиссия до расчёта:", fee_test_transaction.fee)

    processor.set_transaction_fee(
        fee_test_transaction,
        is_external=True
    )

    print("Комиссия после расчёта:", fee_test_transaction.fee)
    print("Сумма перевода:", fee_test_transaction.amount)
    print(
        "Всего к списанию:",
        fee_test_transaction.amount + fee_test_transaction.fee
    )


    print("\n--- DAY4: ПЕРЕВОД С КОМИССИЕЙ ---")

    print("Баланс отправителя до:", transfer_account1._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    fee_transfer = Transaction(
        transaction_type="transfer",
        amount=300,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    processor.set_transaction_fee(
        fee_transfer,
        is_external=True
    )

    processor.process_transaction(
        fee_transfer,
        current_hour=12
    )

    print("Сумма перевода:", fee_transfer.amount)
    print("Комиссия:", fee_transfer.fee)
    print("Статус:", fee_transfer.status)
    print("Баланс отправителя после:", transfer_account1._balance)
    print("Баланс получателя после:", transfer_account2._balance)



    print("\n--- DAY4: КОНВЕРТАЦИЯ ВАЛЮТ ---")

    usd_to_eur = processor.convert_currency(100, "USD", "EUR")
    eur_to_usd = processor.convert_currency(100, "EUR", "USD")
    usd_to_kzt = processor.convert_currency(100, "USD", "KZT")
    kzt_to_cny = processor.convert_currency(4500, "KZT", "CNY")

    print("100 USD =", usd_to_eur, "EUR")
    print("100 EUR =", eur_to_usd, "USD")
    print("100 USD =", usd_to_kzt, "KZT")
    print("4500 KZT =", kzt_to_cny, "CNY")



    print("\n--- DAY4: ПЕРЕВОД USD В EUR ---")

    euro_account = BankAccount(
        owner=transfer_client2.full_name,
        balance=100,
        currency="EUR"
    )

    bank.open_account(
        transfer_client2.client_id,
        euro_account
    )

    currency_transfer = Transaction(
        transaction_type="transfer",
        amount=100,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=euro_account.account_number
    )

    print("Баланс отправителя до:", transfer_account1._balance, "USD")
    print("Баланс получателя до:", euro_account._balance, "EUR")

    processor.process_transaction(
        currency_transfer,
        current_hour=12
    )

    print("Баланс отправителя после:", transfer_account1._balance, "USD")
    print("Баланс получателя после:", euro_account._balance, "EUR")
    print("Статус:", currency_transfer.status)


    print("\n--- DAY4: ПОДГОТОВКА PREMIUMACCOUNT ---")

    premium_account = PremiumAccount(
        owner=transfer_client1.full_name,
        balance=100,
        currency="USD",
        overdraft_limit=500,
        withdrawal_limit=1000,
        transaction_fee=5
    )

    bank.open_account(
        transfer_client1.client_id,
        premium_account
    )

    print("Владелец:", premium_account.owner)
    print("Начальный баланс:", premium_account._balance)
    print("Лимит овердрафта:", premium_account.overdraft_limit)
    print("Лимит снятия:", premium_account.withdrawal_limit)
    print("Комиссия за операцию:", premium_account.transaction_fee)
    print("Статус:", premium_account.status)




    print("\n--- DAY4: ПЕРЕВОД С PREMIUMACCOUNT ---")

    premium_transfer = Transaction(
        transaction_type="transfer",
        amount=300,
        currency="USD",
        sender=premium_account.account_number,
        receiver=transfer_account2.account_number
    )

    print("Баланс PremiumAccount до:", premium_account._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    processor.process_transaction(
        premium_transfer,
        current_hour=12
    )

    print("Баланс PremiumAccount после:", premium_account._balance)
    print("Баланс получателя после:", transfer_account2._balance)
    print("Статус:", premium_transfer.status)



    print("\n--- DAY4: ПРОВЕРКА ЛИМИТА ОВЕРДРАФТА ---")

    overdraft_transfer = Transaction(
        transaction_type="transfer",
        amount=400,
        currency="USD",
        sender=premium_account.account_number,
        receiver=transfer_account2.account_number
    )

    print("Баланс PremiumAccount до:", premium_account._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    result = processor.process_safely(
        overdraft_transfer,
        current_hour=12
    )

    print("Результат перевода:", result)
    print("Статус транзакции:", overdraft_transfer.status)
    print("Причина отказа:", overdraft_transfer.failure_reason)
    print("Баланс PremiumAccount после:", premium_account._balance)
    print("Баланс получателя после:", transfer_account2._balance)



    print("\n--- DAY4: ПРОВЕРКА ПОВТОРНЫХ ПОПЫТОК ---")

    retry_transaction = Transaction(
        transaction_type="transfer",
        amount=5000,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    result = processor.process_with_retry(
        retry_transaction,
        current_hour=12,
        max_attempts=3
    )

    print("Результат:", result)
    print("Статус:", retry_transaction.status)
    print("Причина отказа:", retry_transaction.failure_reason)



    print("\n--- DAY4: ВРЕМЕННАЯ ОШИБКА ПОДКЛЮЧЕНИЯ ---")

    connection_transaction = Transaction(
        transaction_type="transfer",
        amount=50,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number
    )

    original_process = processor.process_transaction

    attempts = [0]

    def simulate_connection_error(transaction, current_hour=None):

        attempts[0] += 1

        if attempts[0] < 3:
            raise ConnectionError(
                "Временная недоступность банковского сервиса"
            )

        return original_process(transaction, current_hour)

    processor.process_transaction = simulate_connection_error

    try:
        result = processor.process_with_retry(
            connection_transaction,
            current_hour=12,
            max_attempts=3
        )
    finally:
        processor.process_transaction = original_process

    print("Результат:", result)
    print("Количество попыток:", attempts[0])
    print("Статус:", connection_transaction.status)
    print("Баланс отправителя:", transfer_account1._balance)
    print("Баланс получателя:", transfer_account2._balance)



    print("\n--- DAY4: ОЧЕРЕДЬ ИЗ 10 ТРАНЗАКЦИЙ ---")

    test_queue = TransactionQueue()

    for i in range(10):

        transaction = Transaction(
            transaction_type="transfer",
            amount=10 * (i + 1),
            currency="USD",
            sender=transfer_account1.account_number,
            receiver=transfer_account2.account_number,
            priority=(i % 3) + 1
        )

        test_queue.add_transaction(transaction)

    print("Всего транзакций:", len(test_queue.transactions))

    print("\nТранзакции в очереди:")

    for transaction in test_queue.transactions:
        print(
            "ID:", transaction.transaction_id,
            "| Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority,
            "| Статус:", transaction.status
        )



    print("\n--- DAY4: ГОТОВЫЕ ТРАНЗАКЦИИ ---")

    ready_transactions = test_queue.get_ready_transactions()

    print("Готовы к выполнению:", len(ready_transactions))

    for transaction in ready_transactions:
        print(
            "Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority,
            "| Статус:", transaction.status
        )


    print("\n--- DAY4: ОБРАБОТКА ОЧЕРЕДИ ИЗ 10 ТРАНЗАКЦИЙ ---")

    print("Баланс отправителя до:", transfer_account1._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    successful = 0
    failed = 0

    for transaction in ready_transactions:

        print("\nОбрабатываем транзакцию:", transaction.transaction_id)
        print("Сумма:", transaction.amount)
        print("Приоритет:", transaction.priority)

        result = processor.process_safely(
            transaction,
            current_hour=12
        )

        if result:
            successful += 1
        else:
            failed += 1

    print("\n--- РЕЗУЛЬТАТЫ ОБРАБОТКИ ОЧЕРЕДИ ---")

    print("Успешных транзакций:", successful)
    print("Отклонённых транзакций:", failed)

    print("Баланс отправителя после:", transfer_account1._balance)
    print("Баланс получателя после:", transfer_account2._balance)

    print("\nСтатусы транзакций:")

    for transaction in test_queue.transactions:
        print(
            "Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority,
            "| Статус:", transaction.status
        )


    print("\n--- DAY4: ПРОВЕРКА ОТЛОЖЕННОЙ ТРАНЗАКЦИИ ---")

    from datetime import timedelta

    delayed_queue = TransactionQueue()

    delayed_transaction = Transaction(
        transaction_type="transfer",
        amount=20,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number,
        priority=3,
        scheduled_at=datetime.now() + timedelta(days=1)
    )

    delayed_queue.add_transaction(delayed_transaction)

    print("Всего транзакций:", len(delayed_queue.transactions))
    print("Запланирована на:", delayed_transaction.scheduled_at)

    ready = delayed_queue.get_ready_transactions()

    print("Готовы к выполнению:", len(ready))
    print("Статус транзакции:", delayed_transaction.status)


    print("\n--- DAY4: ПРОВЕРКА НАСТУПЛЕНИЯ ВРЕМЕНИ ---")

    past_transaction = Transaction(
        transaction_type="transfer",
        amount=15,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number,
        priority=2,
        scheduled_at=datetime.now() - timedelta(days=1)
    )

    delayed_queue.add_transaction(past_transaction)

    ready = delayed_queue.get_ready_transactions()

    print("Всего транзакций:", len(delayed_queue.transactions))
    print("Готовы к выполнению:", len(ready))

    for transaction in ready:
        print(
            "Сумма:", transaction.amount,
            "| Приоритет:", transaction.priority,
            "| Статус:", transaction.status
        )


    print("\n--- DAY4: ВЫПОЛНЕНИЕ ОТЛОЖЕННОЙ ТРАНЗАКЦИИ ---")

    print("Баланс отправителя до:", transfer_account1._balance)
    print("Баланс получателя до:", transfer_account2._balance)

    for transaction in ready:

        result = processor.process_safely(
            transaction,
            current_hour=12
        )

        print("Результат выполнения:", result)
        print("Статус транзакции:", transaction.status)

    print("Баланс отправителя после:", transfer_account1._balance)
    print("Баланс получателя после:", transfer_account2._balance)


    print("\n--- DAY4: АВТОМАТИЧЕСКАЯ КОМИССИЯ ---")

    auto_fee_transaction = Transaction(
        transaction_type="transfer",
        amount=10,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=transfer_account2.account_number,
        is_external=True
    )

    print("Комиссия до обработки:", auto_fee_transaction.fee)

    result = processor.process_safely(
        auto_fee_transaction,
        current_hour=12
    )

    print("Результат:", result)
    print("Комиссия после обработки:", auto_fee_transaction.fee)
    print("Статус:", auto_fee_transaction.status)
    print("Баланс отправителя:", transfer_account1._balance)
    print("Баланс получателя:", transfer_account2._balance)



    print("\n--- DAY4: ПРОВЕРКА ЗАМОРОЖЕННЫХ СЧЕТОВ ---")

    frozen_sender = BankAccount(
        owner=transfer_client1.full_name,
        balance=500,
        currency="USD",
        status="frozen"
    )

    frozen_receiver = BankAccount(
        owner=transfer_client2.full_name,
        balance=200,
        currency="USD",
        status="frozen"
    )

    # Регистрируем счета в банке как активные,
    # затем замораживаем их через Bank
    frozen_sender.status = "active"
    frozen_receiver.status = "active"

    bank.open_account(transfer_client1.client_id, frozen_sender)
    bank.open_account(transfer_client2.client_id, frozen_receiver)

    frozen_sender.status = "frozen"
    frozen_receiver.status = "frozen"

    print("\nТест 1: заморожен отправитель")

    test_frozen_sender = Transaction(
        transaction_type="transfer",
        amount=100,
        currency="USD",
        sender=frozen_sender.account_number,
        receiver=transfer_account2.account_number
    )

    result1 = processor.process_safely(
        test_frozen_sender,
        current_hour=12
    )

    print("Результат:", result1)
    print("Статус:", test_frozen_sender.status)
    print("Баланс отправителя:", frozen_sender._balance)

    print("\nТест 2: заморожен получатель")

    test_frozen_receiver = Transaction(
        transaction_type="transfer",
        amount=100,
        currency="USD",
        sender=transfer_account1.account_number,
        receiver=frozen_receiver.account_number
    )

    result2 = processor.process_safely(
        test_frozen_receiver,
        current_hour=12
    )

    print("Результат:", result2)
    print("Статус:", test_frozen_receiver.status)
    print("Баланс получателя:", frozen_receiver._balance)



    print("\n--- DAY4: ПРОВЕРКА СОХРАННОСТИ БАЛАНСОВ ---")

    print("Замороженный отправитель:", frozen_sender._balance)
    print("Замороженный получатель:", frozen_receiver._balance)
    print("Обычный счёт отправителя:", transfer_account1._balance)
    print("Обычный счёт получателя:", transfer_account2._balance)


    print("\n--- DAY3: ТЕСТ РАЗНЫХ ВАЛЮТ ---")

    currency_bank = Bank("Currency Test Bank")

    client_usd = Client("Test USD", 25, "+12025550101", "usd@example.com")
    client_eur = Client("Test EUR", 30, "+12025550102", "eur@example.com")
    client_rub = Client("Test RUB", 35, "+12025550103", "rub@example.com")
    client_kzt = Client("Test KZT", 40, "+12025550104", "kzt@example.com")
    client_cny = Client("Test CNY", 45, "+12025550105", "cny@example.com")

    currency_bank.add_client(client_usd)
    currency_bank.add_client(client_eur)
    currency_bank.add_client(client_rub)
    currency_bank.add_client(client_kzt)
    currency_bank.add_client(client_cny)

    account_usd = BankAccount(owner="Test USD", balance=100, currency="USD")
    account_eur = BankAccount(owner="Test EUR", balance=200, currency="EUR")
    account_rub = BankAccount(owner="Test RUB", balance=5000, currency="RUB")
    account_kzt = BankAccount(owner="Test KZT", balance=45000, currency="KZT")
    account_cny = BankAccount(owner="Test CNY", balance=700, currency="CNY")

    currency_bank.open_account(client_usd.client_id, account_usd)
    currency_bank.open_account(client_eur.client_id, account_eur)
    currency_bank.open_account(client_rub.client_id, account_rub)
    currency_bank.open_account(client_kzt.client_id, account_kzt)
    currency_bank.open_account(client_cny.client_id, account_cny)

    total_balance = currency_bank.get_total_balance("USD")

    print("Суммы по валютам:", total_balance["by_currency"])
    print("Итого:", total_balance["total"], total_balance["base_currency"])

    print("\nЕдиный рейтинг в USD:")

    for position, client in enumerate(
        currency_bank.get_clients_ranking("USD"), start=1
    ):
        print(
            f"{position}. {client['full_name']} — "
            f"{client['total_balance']:.2f} USD "
            f"(на счетах: {client['balances_by_currency']})"
        )



    print("\n--- DAY3: ТЕСТ СВЯЗИ СЧЁТА С БАНКОМ ---")

    print("Банк счёта USD:", account_usd._bank.name)
    print("Счёт связан с правильным банком:", account_usd._bank is currency_bank)



    print("\n--- DAY3: ТЕСТ НОЧНОГО ОГРАНИЧЕНИЯ ИНВЕСТИЦИЙ ---")

    # Создаём отдельного клиента для тестирования
    test_investor = Client(
        "Test Investor",
        30,
        "+12025550110",
        "investor@example.com"
    )

    bank.add_client(test_investor)

    # Создаём инвестиционный счёт
    test_investment = InvestmentAccount(
        owner="Test Investor",
        balance=1000
    )

    bank.open_account(test_investor.client_id, test_investment)

    # Запоминаем начальный баланс
    balance_before = test_investment._balance

    # Тест 1. Попытка инвестирования ночью
    try:
        bank.invest(
            test_investor.client_id,
            test_investment.account_number,
            "stocks",
            100,
            current_hour=2
        )
    except InvalidOperationError as error:
        print("Ночная операция заблокирована:", error)

    print("Баланс не изменился:", test_investment._balance == balance_before)

    # Тест 2. Инвестирование днём
    bank.invest(
        test_investor.client_id,
        test_investment.account_number,
        "stocks",
        100,
        current_hour=12
    )

    print("Баланс после дневной инвестиции:", test_investment._balance)

    # Тест 3. Прямое инвестирование
    try:
        test_investment.invest("stocks", 100)
    except InvalidOperationError as error:
        print("Прямая инвестиция заблокирована:", error)



    print("\n--- DAY3: ПРОВЕРКА ЖУРНАЛА ПОДОЗРИТЕЛЬНЫХ ОПЕРАЦИЙ ---")

    for activity in bank.suspicious_activities:
        if activity["client_id"] == test_investor.client_id:
            print("Клиент:", activity["client_id"])
            print("Причина:", activity["reason"])


    print("\n--- DAY3: ТЕСТ ЗАЩИТЫ ПРЯМЫХ ОПЕРАЦИЙ ---")

    # Используем зарегистрированный инвестиционный счёт
    # из предыдущего теста

    balance_before = test_investment._balance

    # Тест 1. Прямое пополнение
    try:
        test_investment.deposit(100)
    except InvalidOperationError as error:
        print("Прямое пополнение заблокировано:", error)

    # Тест 2. Прямое снятие
    try:
        test_investment.withdraw(100)
    except InvalidOperationError as error:
        print("Прямое снятие заблокировано:", error)

    # Проверяем, что баланс не изменился
    print(
        "Баланс не изменился:",
        test_investment._balance == balance_before
    )

    # Проверяем, что разрешение сброшено
    print(
        "Разрешение после операций:",
        test_investment._operation_authorized
    )


    print("\n--- DAY3: ТЕСТ ЗАЩИТЫ PREMIUM ACCOUNT ---")

    premium_client = Client(
        "Test Premium",
        35,
        "+12025550120",
        "premium@example.com"
    )

    bank.add_client(premium_client)

    premium_test = PremiumAccount(
        owner="Test Premium",
        balance=1000
    )

    bank.open_account(premium_client.client_id, premium_test)

    balance_before = premium_test._balance

    # Проверяем прямое снятие
    try:
        premium_test.withdraw(100)
    except InvalidOperationError as error:
        print("Прямое снятие заблокировано:", error)

    print("Баланс не изменился:", premium_test._balance == balance_before)

    # Проверяем снятие ночью
    try:
        bank.withdraw(
            premium_client.client_id,
            premium_test.account_number,
            100,
            current_hour=2
        )
    except InvalidOperationError as error:
        print("Ночное снятие заблокировано:", error)

    print("Баланс после ночной попытки:", premium_test._balance)
    print("Разрешение после операций:", premium_test._operation_authorized)


    print("\n--- DAY3: ТЕСТ ЗАЩИТЫ ОБЫЧНОГО СЧЁТА ---")

    # Создаём клиента
    regular_client = Client(
        "Test Regular",
        30,
        "+12025550130",
        "regular@example.com"
    )

    bank.add_client(regular_client)

    # Создаём обычный банковский счёт
    regular_account = BankAccount(
        owner="Test Regular",
        balance=1000
    )

    bank.open_account(regular_client.client_id, regular_account)

    # Тест 1. Прямое снятие
    try:
        regular_account.withdraw(100)
    except InvalidOperationError as error:
        print("Прямое снятие заблокировано:", error)

    # Тест 2. Прямое пополнение
    try:
        regular_account.deposit(100)
    except InvalidOperationError as error:
        print("Прямое пополнение заблокировано:", error)

    # Тест 3. Ночное снятие
    try:
        bank.withdraw(
            regular_client.client_id,
            regular_account.account_number,
            100,
            current_hour=2
        )
    except InvalidOperationError as error:
        print("Ночное снятие заблокировано:", error)

    # Тест 4. Дневное снятие
    bank.withdraw(
        regular_client.client_id,
        regular_account.account_number,
        100,
        current_hour=12
    )

    # Тест 5. Дневное пополнение
    bank.deposit(
        regular_client.client_id,
        regular_account.account_number,
        200,
        current_hour=12
    )

    print("Итоговый баланс:", regular_account._balance)
    print("Разрешение после операций:", regular_account._operation_authorized)



    print("\n--- DAY3: ТЕСТ ПОВТОРНОЙ РЕГИСТРАЦИИ СЧЁТА ---")

    # Создаём второй банк
    second_bank = Bank("Second Test Bank")

    # Создаём клиента с тем же именем
    second_client = Client(
        "Test Regular",
        30,
        "+12025550140",
        "second@example.com"
    )

    second_bank.add_client(second_client)

    # Пытаемся зарегистрировать счёт из первого банка
    try:
        second_bank.open_account(
            second_client.client_id,
            regular_account
        )
    except InvalidOperationError as error:
        print("Повторная регистрация заблокирована:", error)

    # Проверяем, что счёт остался в первоначальном банке
    print(
        "Счёт остался в первоначальном банке:",
        regular_account._bank is bank
    )

    # Проверяем, что второй банк не получил этот счёт
    print(
        "Счёта нет во втором банке:",
        regular_account.account_number not in second_bank.accounts
    )