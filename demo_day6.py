"""
Day 6 — демонстрационная программа банковской системы.

Запуск:  python demo_day6.py

Все классы берутся из main.py. Демонстрации Day1–Day5 при импорте
не запускаются, потому что в main.py они находятся под
if __name__ == "__main__":
"""

from datetime import datetime, timedelta

from main import (
    Bank, Client,
    BankAccount, SavingsAccount, PremiumAccount, InvestmentAccount,
    Transaction, TransactionQueue, TransactionProcessor,
    AuditLog, RiskAnalyzer, AuditReport
)


DAY_HOUR = 12      # дневное время операций
NIGHT_HOUR = 3     # ночное время операций


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ======================================================================
# 1. ИНИЦИАЛИЗАЦИЯ
# ======================================================================

section("1. ИНИЦИАЛИЗАЦИЯ БАНКА")

bank = Bank("Python Bank")

audit_log = AuditLog("day6_audit_log.jsonl", append=False)

risk_analyzer = RiskAnalyzer(
    bank,
    large_amount=8000,        # крупная сумма — от 8000 USD
    max_operations=5,         # 6-я и следующие операции ...
    time_window_minutes=10    # ... за 10 минут — частые операции
)

processor = TransactionProcessor(
    bank,
    audit_log=audit_log,
    risk_analyzer=risk_analyzer
)

queue = TransactionQueue(audit_log=audit_log)

print("\n--- Клиенты ---")

anna = Client("Anna Smirnova", 34, "+70000000101", "anna@example.com")
boris = Client("Boris Kuznetsov", 45, "+70000000102", "boris@example.com")
elena = Client("Elena Popova", 29, "+70000000103", "elena@example.com")
dmitry = Client("Dmitry Volkov", 38, "+70000000104", "dmitry@example.com")
olga = Client("Olga Sokolova", 52, "+70000000105", "olga@example.com")
pavel = Client("Pavel Morozov", 27, "+70000000106", "pavel@example.com")
irina = Client("Irina Lebedeva", 23, "+70000000107", "irina@example.com")

clients = [anna, boris, elena, dmitry, olga, pavel, irina]

for client in clients:
    bank.add_client(client)

print("\n--- Счета ---")

accounts = {
    "anna_main": BankAccount(owner=anna.full_name, balance=5000),
    "anna_savings": SavingsAccount(
        owner=anna.full_name, balance=10000, min_balance=2000
    ),
    "boris_eur": BankAccount(owner=boris.full_name, balance=4000, currency="EUR"),
    "boris_premium": PremiumAccount(
        owner=boris.full_name, balance=1000,
        overdraft_limit=2000, withdrawal_limit=5000, transaction_fee=5
    ),
    "elena_rub": BankAccount(owner=elena.full_name, balance=300000, currency="RUB"),
    "elena_invest": InvestmentAccount(owner=elena.full_name, balance=15000),
    "dmitry_usd": BankAccount(owner=dmitry.full_name, balance=2000),
    "dmitry_kzt": BankAccount(owner=dmitry.full_name, balance=900000, currency="KZT"),
    "olga_main": BankAccount(owner=olga.full_name, balance=25000),
    "olga_savings": SavingsAccount(
        owner=olga.full_name, balance=3000, min_balance=1000
    ),
    "pavel_cny": BankAccount(owner=pavel.full_name, balance=20000, currency="CNY"),
    "irina_main": BankAccount(owner=irina.full_name, balance=800),
    "irina_old": BankAccount(owner=irina.full_name, balance=0),
}

owners = {
    "anna": anna, "boris": boris, "elena": elena, "dmitry": dmitry,
    "olga": olga, "pavel": pavel, "irina": irina
}

for key, account in accounts.items():
    owner = owners[key.split("_")[0]]
    bank.open_account(owner.client_id, account)

# Короткие имена для номеров счетов
acc = {key: account.account_number for key, account in accounts.items()}

print("\n--- Подготовка состояний счетов ---")

bank.invest(elena.client_id, acc["elena_invest"], "stocks", 5000, DAY_HOUR)
bank.freeze_account(acc["pavel_cny"])
bank.close_account(acc["irina_old"])

print(f"\nБанк «{bank.name}»: клиентов — {len(bank.clients)}, "
      f"счетов — {len(bank.accounts)}")



# ======================================================================
# 2. СИМУЛЯЦИЯ: ПОСТАНОВКА ТРАНЗАКЦИЙ В ОЧЕРЕДЬ
# ======================================================================

section("2. СИМУЛЯЦИЯ ТРАНЗАКЦИЙ — ПОСТАНОВКА В ОЧЕРЕДЬ")

descriptions = {}


def add(description, transaction_type, amount, currency,
        sender=None, receiver=None, priority=1, to_queue=None, **options):
    """Создаёт транзакцию, запоминает описание и ставит её в очередь."""

    transaction = Transaction(
        transaction_type, amount, currency,
        acc.get(sender, sender), acc.get(receiver, receiver),
        priority=priority, **options
    )

    descriptions[transaction.transaction_id] = description

    # по умолчанию — в основную (дневную) очередь
    (to_queue or queue).add_transaction(transaction)

    return transaction


# --- Обычные операции ---
add("Пополнение счёта Анны", "deposit", 1000, "USD", receiver="anna_main", priority=3)
add("Анна → Дмитрий", "transfer", 500, "USD", "anna_main", "dmitry_usd", priority=2)
add("Борис (EUR) → Анна (USD), конвертация", "transfer", 300, "EUR", "boris_eur", "anna_main")
add("Снятие наличных Ириной", "withdraw", 200, "USD", sender="irina_main")
add("Пополнение рублёвого счёта Елены", "deposit", 50000, "RUB", receiver="elena_rub")
add("Елена (инвест.) → Анна (сберегат.)", "transfer", 1000, "USD", "elena_invest", "anna_savings")
add("Дмитрий (KZT) → Елена (RUB), конвертация", "transfer", 100000, "KZT", "dmitry_kzt", "elena_rub")
add("Борис (премиум) → Ирина, уход в овердрафт", "transfer", 1500, "USD", "boris_premium", "irina_main")
add("Анна: со сберегательного на основной", "transfer", 200, "USD", "anna_savings", "anna_main")
add("Снятие наличных Ольгой", "withdraw", 100, "USD", sender="olga_main")
add("Дмитрий → Ирина", "transfer", 400, "USD", "dmitry_usd", "irina_main")
add("Борис → Анна, повторный перевод", "transfer", 250, "EUR", "boris_eur", "anna_main")
add("Пополнение счёта Ирины", "deposit", 300, "USD", receiver="irina_main", priority=3)
add("Ольга: со сберегательного на основной", "transfer", 700, "USD", "olga_savings", "olga_main")
add("Елена (RUB) → Дмитрий (KZT), конвертация", "transfer", 50000, "RUB", "elena_rub", "dmitry_kzt")
add("Внешнее снятие Анны (комиссия 2%)", "withdraw", 1000, "USD", sender="anna_main", is_external=True)

# --- Ошибочные операции ---
add("ОШИБКА: Ирина переводит больше, чем есть", "transfer", 7000, "USD", "irina_main", "anna_main")
add("ОШИБКА: снятие с замороженного счёта Павла", "withdraw", 100, "CNY", sender="pavel_cny")
add("ОШИБКА: пополнение закрытого счёта Ирины", "deposit", 100, "USD", receiver="irina_old")
add("ОШИБКА: валюта не совпадает со счётом", "transfer", 100, "EUR", "anna_main", "dmitry_usd")
add("ОШИБКА: превышен овердрафт премиум-счёта", "transfer", 2000, "USD", "boris_premium", "irina_main")
add("ОШИБКА: перевод на несуществующий счёт", "transfer", 100, "USD", "anna_main", "XXXXXXXX")
add("ОШИБКА: нарушение минимального остатка", "transfer", 2000, "USD", "olga_savings", "dmitry_usd")

# --- Подозрительные операции ---
add("РИСК: крупный перевод Ольги новому получателю", "transfer", 12000, "USD", "olga_main", "elena_invest")
add("РИСК: крупное снятие Ольгой", "withdraw", 9000, "USD", sender="olga_main")
add("РИСК: крупное пополнение 1 000 000 RUB", "deposit", 1000000, "RUB", receiver="elena_rub")
add("Ольга → Дмитрий, небольшой перевод", "transfer", 100, "USD", "olga_main", "dmitry_usd")
add("Ольга → Дмитрий, ещё перевод", "transfer", 100, "USD", "olga_main", "dmitry_usd")
add("РИСК: Ольга → Дмитрий, 6-я операция за 10 минут", "transfer", 100, "USD", "olga_main", "dmitry_usd")
add("РИСК: крупный перевод Ольги на фоне частых операций", "transfer", 8500, "USD", "olga_main", "dmitry_usd")

# --- Отложенная и отменённая ---
scheduled = add(
    "Отложенный платёж Анны (на завтра)", "transfer", 150, "USD",
    "anna_main", "dmitry_usd", scheduled_at=datetime.now() + timedelta(days=1)
)

cancelled = add("Перевод Дмитрия, который отменят", "transfer", 50, "USD", "dmitry_usd", "anna_main")
queue.cancel_transaction(cancelled.transaction_id)

print(f"\nВ очереди: {len(queue.transactions)} транзакций, "
      f"готовы к выполнению: {len(queue.get_ready_transactions())}")


def print_results(processed):
    """Печатает результат каждой обработанной транзакции."""

    for number, transaction in enumerate(processed, start=1):

        mark = "✅" if transaction.status == "completed" else "🚫"
        risk = transaction.risk_level or "—"

        print(
            f"{mark} {number:2}. [{transaction.transaction_id}] "
            f"{descriptions[transaction.transaction_id]} | "
            f"{transaction.amount} {transaction.currency} | риск: {risk}"
        )

        if transaction.status != "completed":
            print(f"       причина: {transaction.failure_reason}")


# ======================================================================
# 3. ОБРАБОТКА ОЧЕРЕДИ
# ======================================================================

section("3. ОБРАБОТКА ОЧЕРЕДИ (ДЕНЬ, 12:00)")

day_results = processor.process_queue(queue, current_hour=DAY_HOUR)

print("\n--- Итог обработки ---")

print_results(day_results)


# ======================================================================
# 4. НОЧНЫЕ ТРАНЗАКЦИИ
# ======================================================================

section("4. НОЧНЫЕ ТРАНЗАКЦИИ (03:00)")

night_queue = TransactionQueue(audit_log=audit_log)

add("Ночью: Дмитрий → Ирина", "transfer", 100, "USD",
    "dmitry_usd", "irina_main", to_queue=night_queue)
add("Ночью: снятие наличных Борисом", "withdraw", 200, "EUR",
    sender="boris_eur", to_queue=night_queue)
add("РИСК ночью: крупный перевод Елены", "transfer", 9000, "USD",
    "elena_invest", "irina_main", to_queue=night_queue)

night_results = processor.process_queue(night_queue, current_hour=NIGHT_HOUR)

print()
print_results(night_results)

print("\nОтложенная транзакция:", scheduled.status,
      "| запланирована на", scheduled.scheduled_at.strftime("%d.%m.%Y %H:%M"))
print("Отменённая транзакция:", cancelled.status, "|", cancelled.failure_reason)



# ======================================================================
# 5. ЖУРНАЛ АУДИТА (ЛОГИРОВАНИЕ)
# ======================================================================

section("5. ЖУРНАЛ АУДИТА")

event_counts = {}

for entry in audit_log.entries:
    event_counts[entry["event_type"]] = event_counts.get(entry["event_type"], 0) + 1

print("Всего записей:", len(audit_log.entries))

for event_type, count in event_counts.items():
    print(f"  {event_type}: {count}")

print("\nЖизненный путь одной транзакции в журнале:")

example = day_results[1]

for entry in audit_log.filter(transaction_id=example.transaction_id):
    print(f"  {entry['level']:8} | {entry['event_type']:22} | {entry['message']}")

print("\nЖизненный путь заблокированной транзакции:")

blocked = next(t for t in day_results if t.risk_level == "high")

for entry in audit_log.filter(transaction_id=blocked.transaction_id):
    print(f"  {entry['level']:8} | {entry['event_type']:22} | {entry['message']}")

print("\nЗаписей в файле", audit_log.file_path + ":", len(audit_log.read_from_file()))


# ======================================================================
# 6. ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ
# ======================================================================

audit_report = AuditReport(audit_log, bank)


def show_client(client):
    """Счета, история и подозрительные операции клиента."""

    section(f"6. ЛИЧНЫЙ КАБИНЕТ: {client.full_name}")

    print("\n💰 Счета:")

    for account in bank.search_accounts(client_id=client.client_id):
        print("  ", account)

    print("\n📜 История операций:")

    for transaction in processor.get_client_history(client.client_id):

        mark = "✅" if transaction.status == "completed" else "🚫"

        print(
            f"   {mark} {transaction.created_at.strftime('%H:%M:%S')} | "
            f"{transaction.transaction_type:8} | "
            f"{transaction.amount:>9} {transaction.currency} | "
            f"{descriptions[transaction.transaction_id]}"
        )

    print("\n⚠️ Подозрительные операции:")

    suspicious = [
        item for item in audit_report.suspicious_operations()
        if item["client_id"] == client.client_id
    ]

    if not suspicious:
        print("   нет")

    for item in suspicious:
        status = "ЗАБЛОКИРОВАНА" if item["blocked"] else "с предупреждением"
        print(
            f"   {item['risk_level']:6} | {status:17} | "
            f"{descriptions[item['transaction_id']]} | {', '.join(item['factors'])}"
        )

    profile = audit_report.client_risk_profile(client.client_id)

    print(
        f"\nРиск-профиль: {profile['overall_risk']} | "
        f"заблокировано: {profile['blocked_operations']} | "
        f"неуспешных: {profile['failed_operations']}"
    )


show_client(anna)
show_client(olga)


# ======================================================================
# 7. ОТЧЁТЫ
# ======================================================================

section("7. ОТЧЁТЫ")

print("\n🏆 Топ-3 клиентов (все счета в USD):")

for position, item in enumerate(bank.get_clients_ranking("USD")[:3], start=1):
    print(f"  {position}. {item['full_name']} — {item['total_balance']:,.2f} USD")

print("\n📊 Статистика транзакций:")

statistics = processor.get_statistics()

print("  Всего обработано:", statistics["total"])
print("  По статусу:", statistics["by_status"])
print("  По типу:", statistics["by_type"])
print("  По уровню риска:", statistics["by_risk"])
print(f"  Успешных: {statistics['success_rate']}%")
print("  Объём успешных операций:", statistics["volume_by_currency"])
print("  Комиссии:", statistics["fees_by_currency"])
print("  В очереди осталось (отложенные):", len([
    t for t in queue.transactions if t.status == "pending"
]))
print("  Отменено:", len([
    t for t in queue.transactions if t.status == "cancelled"
]))

print("\n❌ Статистика ошибок:")

errors = audit_report.error_statistics()

print("  Всего:", errors["total_errors"])

for error_type, count in errors["by_type"].items():
    print(f"  {error_type}: {count}")

print("\n💎 Общий баланс банка:")

total = bank.get_total_balance("USD")

for currency, amount in total["by_currency"].items():
    print(f"  {currency}: {amount:,.2f}")

print(f"  Итого в USD: {total['total']:,.2f}")

print("\n🚨 Подозрительные действия в журнале банка:", len(bank.suspicious_activities))

section("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")