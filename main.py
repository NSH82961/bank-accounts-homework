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