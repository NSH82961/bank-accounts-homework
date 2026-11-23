"""
Day 7 — демонстрация системы отчётности и визуализации.

Запуск:  python demo_day7.py

Нужна библиотека matplotlib (см. requirements.txt).
Отчёты и графики сохраняются в папку reports/.
"""

import csv
import json
import os

from main import (
    Bank, Client,
    BankAccount, SavingsAccount, PremiumAccount, InvestmentAccount,
    Transaction, TransactionQueue, TransactionProcessor,
    AuditLog, RiskAnalyzer, InvalidOperationError
)
from report_builder import ReportBuilder


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ======================================================================
# 1. ПОДГОТОВКА ДАННЫХ
# ======================================================================

section("1. ПОДГОТОВКА ДАННЫХ")

bank = Bank("Report Bank")
audit_log = AuditLog("day7_audit_log.jsonl", append=False)
risk_analyzer = RiskAnalyzer(bank, large_amount=8000, max_operations=5)
processor = TransactionProcessor(bank, audit_log=audit_log, risk_analyzer=risk_analyzer)
queue = TransactionQueue(audit_log=audit_log)

alice = Client("Alice Brown", 31, "+10000000201", "alice@example.com")
bob = Client("Bob Green", 44, "+10000000202", "bob@example.com")
carol = Client("Carol White", 37, "+10000000203", "carol@example.com")
dan = Client("Dan Black", 26, "+10000000204", "dan@example.com")

for client in (alice, bob, carol, dan):
    bank.add_client(client)

alice_main = BankAccount(owner=alice.full_name, balance=6000)
alice_savings = SavingsAccount(owner=alice.full_name, balance=4000, min_balance=1000)
bob_eur = BankAccount(owner=bob.full_name, balance=3000, currency="EUR")
bob_premium = PremiumAccount(owner=bob.full_name, balance=500, overdraft_limit=1500)
carol_rub = BankAccount(owner=carol.full_name, balance=400000, currency="RUB")
carol_invest = InvestmentAccount(owner=carol.full_name, balance=20000)
dan_main = BankAccount(owner=dan.full_name, balance=1200)

for client, account in [
    (alice, alice_main), (alice, alice_savings),
    (bob, bob_eur), (bob, bob_premium),
    (carol, carol_rub), (carol, carol_invest),
    (dan, dan_main),
]:
    bank.open_account(client.client_id, account)

bank.invest(carol.client_id, carol_invest.account_number, "bonds", 6000, 12)

a = alice_main.account_number
s = alice_savings.account_number
b = bob_eur.account_number
p = bob_premium.account_number
r = carol_rub.account_number
i = carol_invest.account_number
d = dan_main.account_number

transactions = [
    Transaction("deposit", 1500, "USD", None, a),
    Transaction("transfer", 700, "USD", a, d),
    Transaction("transfer", 300, "USD", a, s),
    Transaction("withdraw", 400, "USD", a, None, is_external=True),
    Transaction("transfer", 500, "EUR", b, a),
    Transaction("transfer", 1200, "USD", p, d),
    Transaction("deposit", 90000, "RUB", None, r),
    Transaction("transfer", 2000, "USD", i, a),
    Transaction("transfer", 250, "USD", d, a),
    Transaction("withdraw", 5000, "USD", d, None),             # ошибка: мало средств
    Transaction("transfer", 900, "USD", p, d),                 # ошибка: овердрафт
    Transaction("transfer", 100, "EUR", a, d),                 # ошибка: валюта
    Transaction("transfer", 9000, "USD", i, d),                # риск: заблокирован
    Transaction("withdraw", 8500, "USD", i, None),             # риск: предупреждение
    Transaction("transfer", 3500, "USD", s, a),                # ошибка: мин. остаток
    Transaction("transfer", 200, "USD", a, d),
]

for transaction in transactions:
    queue.add_transaction(transaction)

processed = processor.process_queue(queue, current_hour=12)

completed = len([t for t in processed if t.status == "completed"])

print(f"\nОбработано транзакций: {len(processed)} | "
      f"успешных: {completed} | отклонённых: {len(processed) - completed}")


# ======================================================================
# 2. ОТЧЁТЫ
# ======================================================================

builder = ReportBuilder(bank, processor, audit_log=audit_log, output_dir="reports")

section("2. ОТЧЁТ ПО КЛИЕНТУ — ТЕКСТ")

client_report = builder.client_report(alice.client_id)

print(builder.to_text(client_report))

section("3. ОТЧЁТ ПО БАНКУ — КРАТКО")

bank_report = builder.bank_report()

print("Клиентов:", bank_report["clients_count"])
print("Счетов:", bank_report["accounts_count"])
print("По типам:", bank_report["accounts_by_type"])
print("Итого в USD:", bank_report["total_balance"]["total"])
print("Топ-3:", [c["full_name"] for c in bank_report["top_clients"]])
print("Транзакции по статусу:", bank_report["transaction_statistics"]["by_status"])

section("4. ОТЧЁТ ПО РИСКАМ — КРАТКО")

risk_report = builder.risk_report()

print("Клиенты по уровню риска:", risk_report["clients_by_risk"])
print("Подозрительных операций:", len(risk_report["suspicious_operations"]))
print("Ошибки по типу:", risk_report["error_statistics"]["by_type"])

for item in risk_report["suspicious_operations"]:
    status = "ЗАБЛОКИРОВАНА" if item["blocked"] else "с предупреждением"
    print(f"  {item['risk_level']:6} | {status} | {', '.join(item['factors'])}")


# ======================================================================
# 3. ЭКСПОРТ
# ======================================================================

section("5. ЭКСПОРТ ОТЧЁТОВ")

saved_files = [
    builder.export_to_text(client_report, "client_report.txt"),
    builder.export_to_json(client_report, "client_report.json"),
    builder.export_to_csv(client_report["transactions"], "client_transactions.csv"),

    builder.export_to_text(bank_report, "bank_report.txt"),
    builder.export_to_json(bank_report, "bank_report.json"),
    builder.export_to_csv(bank_report["accounts"], "bank_accounts.csv"),

    builder.export_to_text(risk_report, "risk_report.txt"),
    builder.export_to_json(risk_report, "risk_report.json"),
    builder.export_to_csv(risk_report["suspicious_operations"], "risk_suspicious.csv"),
]

for path in saved_files:
    print(f"  {path} — {os.path.getsize(path)} байт")


section("6. ГРАФИКИ")

charts = builder.save_charts([a, p, d])

for path in charts:
    print(f"  {path} — {os.path.getsize(path)} байт")


# ======================================================================
# 4. ПРОВЕРКИ
# ======================================================================

section("7. ПРОВЕРКА СОХРАНЁННЫХ ФАЙЛОВ")

all_files = saved_files + charts

print("Все файлы созданы:", all(os.path.exists(path) for path in all_files))
print("Все файлы не пустые:", all(os.path.getsize(path) > 0 for path in all_files))

with open("reports/bank_report.json", encoding="utf-8") as file:
    loaded = json.load(file)

print("JSON читается обратно:", loaded["bank_name"] == bank.name)
print("JSON: число счетов совпадает:", loaded["accounts_count"] == len(bank.accounts))

with open("reports/bank_accounts.csv", encoding="utf-8-sig") as file:
    rows = list(csv.DictReader(file))

print("CSV: строк столько же, сколько счетов:", len(rows) == len(bank.accounts))
print("CSV: колонки:", list(rows[0].keys()))

with open("reports/client_transactions.csv", encoding="utf-8-sig") as file:
    client_rows = list(csv.DictReader(file))

print("CSV клиента: строк столько же, сколько операций:",
      len(client_rows) == len(client_report["transactions"]))

print("Графиков сохранено:", len(charts))
print("История баланса Alice:",
      [point["balance"] for point in processor.get_balance_history(a)])


section("8. ПРОВЕРКА НЕКОРРЕКТНЫХ ДАННЫХ")

try:
    builder.client_report("unknown")
except InvalidOperationError as error:
    print("Отчёт по неизвестному клиенту:", error)

try:
    builder.export_to_csv([], "empty.csv")
except InvalidOperationError as error:
    print("CSV без данных:", error)

try:
    ReportBuilder(bank, processor).risk_report()
except InvalidOperationError as error:
    print("Отчёт по рискам без журнала:", error)

try:
    builder.line_balance_history([])
except InvalidOperationError as error:
    print("График без счетов:", error)

try:
    ReportBuilder(bank, processor, base_currency="GBP")
except InvalidOperationError as error:
    print("Недопустимая валюта отчёта:", error)

section("ДЕМОНСТРАЦИЯ DAY7 ЗАВЕРШЕНА")