"""
Day 7 — система отчётности и визуализации.

ReportBuilder собирает отчёты по клиенту, банку и рискам,
сохраняет их в текстовом, JSON и CSV форматах и строит графики.
"""

import csv
import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")   # рисуем в файлы, без открытия окон
import matplotlib.pyplot as plt

from main import (
    InvalidOperationError, InvestmentAccount,
    AuditReport, CurrencyConverter
)


class ReportBuilder:

    def __init__(self, bank, processor, audit_log=None,
                 output_dir="reports", base_currency="USD"):

        if base_currency not in CurrencyConverter.EXCHANGE_RATES:
            raise InvalidOperationError("Недопустимая базовая валюта")

        self.bank = bank
        self.processor = processor
        self.audit_log = audit_log
        self.output_dir = output_dir
        self.base_currency = base_currency

        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _path(self, filename):
        return os.path.join(self.output_dir, filename)

    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _transaction_row(transaction):
        """Транзакция в виде плоского словаря (строка таблицы)."""

        return {
            "transaction_id": transaction.transaction_id,
            "created_at": transaction.created_at.isoformat(timespec="seconds"),
            "type": transaction.transaction_type,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "fee": transaction.fee,
            "sender": transaction.sender,
            "receiver": transaction.receiver,
            "status": transaction.status,
            "risk_level": transaction.risk_level,
            "failure_reason": transaction.failure_reason
        }

    def _account_row(self, account):
        """Счёт в виде плоского словаря (строка таблицы)."""

        total = account._balance

        if isinstance(account, InvestmentAccount):
            total += sum(account.portfolio.values())

        return {
            "account_number": account.account_number,
            "owner": account.owner,
            "account_type": type(account).__name__,
            "status": account.status,
            "currency": account.currency,
            "balance": round(account._balance, 2),
            "total_with_investments": round(total, 2),
            "total_in_base": round(CurrencyConverter.convert(
                total, account.currency, self.base_currency
            ), 2)
        }

    def _audit_report(self):

        if self.audit_log is None:
            raise InvalidOperationError("Для отчёта по рискам нужен журнал аудита")

        return AuditReport(self.audit_log, self.bank)

    # ------------------------------------------------------------------
    # Типы отчётов
    # ------------------------------------------------------------------

    def client_report(self, client_id):

        if client_id not in self.bank.clients:
            raise InvalidOperationError("Клиент не найден в банке")

        client = self.bank.clients[client_id]

        accounts = [
            self._account_row(self.bank.accounts[number])
            for number in client.account_numbers
        ]

        history = [
            self._transaction_row(transaction)
            for transaction in self.processor.get_client_history(client_id)
        ]

        report = {
            "report_type": "client",
            "generated_at": self._now(),
            "client": {
                "client_id": client.client_id,
                "full_name": client.full_name,
                "age": client.age,
                "status": client.status
            },
            "accounts": accounts,
            "total_in_base": round(sum(a["total_in_base"] for a in accounts), 2),
            "base_currency": self.base_currency,
            "transactions": history,
            "transactions_completed": len([t for t in history if t["status"] == "completed"]),
            "transactions_failed": len([t for t in history if t["status"] == "failed"])
        }

        if self.audit_log is not None:
            report["risk_profile"] = self._audit_report().client_risk_profile(client_id)

        return report

    def bank_report(self):

        accounts = [self._account_row(a) for a in self.bank.accounts.values()]

        by_type = {}
        by_status = {}

        for account in accounts:
            by_type[account["account_type"]] = by_type.get(account["account_type"], 0) + 1
            by_status[account["status"]] = by_status.get(account["status"], 0) + 1

        return {
            "report_type": "bank",
            "generated_at": self._now(),
            "bank_name": self.bank.name,
            "clients_count": len(self.bank.clients),
            "accounts_count": len(accounts),
            "accounts_by_type": by_type,
            "accounts_by_status": by_status,
            "total_balance": self.bank.get_total_balance(self.base_currency),
            "top_clients": self.bank.get_clients_ranking(self.base_currency)[:3],
            "transaction_statistics": self.processor.get_statistics(),
            "accounts": accounts
        }

    def risk_report(self):

        audit_report = self._audit_report()

        profiles = [
            audit_report.client_risk_profile(client_id)
            for client_id in self.bank.clients
        ]

        clients_by_risk = {"low": 0, "medium": 0, "high": 0}

        for profile in profiles:
            clients_by_risk[profile["overall_risk"]] += 1

        return {
            "report_type": "risk",
            "generated_at": self._now(),
            "suspicious_operations": audit_report.suspicious_operations(),
            "error_statistics": audit_report.error_statistics(),
            "clients_by_risk": clients_by_risk,
            "client_profiles": profiles,
            "bank_alerts": len(self.bank.suspicious_activities)
        }


    # ------------------------------------------------------------------
    # Текстовый формат
    # ------------------------------------------------------------------

    def to_text(self, report):
        """Превращает отчёт (словарь) в читаемый текст."""

        lines = [
            "=" * 60,
            f"ОТЧЁТ: {report.get('report_type', '').upper()}",
            f"Сформирован: {report.get('generated_at', '')}",
            "=" * 60
        ]

        def add(value, indent):

            space = "  " * indent

            if isinstance(value, dict):
                for key, item in value.items():
                    if isinstance(item, (dict, list)):
                        lines.append(f"{space}{key}:")
                        add(item, indent + 1)
                    else:
                        lines.append(f"{space}{key}: {item}")

            elif isinstance(value, list):

                if not value:
                    lines.append(f"{space}(нет данных)")

                elif isinstance(value[0], dict):
                    # список словарей — таблица: строка заголовков и строки значений
                    keys = list(value[0].keys())
                    lines.append(space + " | ".join(keys))
                    lines.append(space + "-" * 40)
                    for item in value:
                        lines.append(space + " | ".join(str(item.get(key)) for key in keys))

                else:
                    for item in value:
                        lines.append(f"{space}- {item}")

        body = {
            key: value for key, value in report.items()
            if key not in ("report_type", "generated_at")
        }

        add(body, 0)

        return "\n".join(lines)

    def export_to_text(self, report, filename):

        path = self._path(filename)

        with open(path, "w", encoding="utf-8") as file:
            file.write(self.to_text(report))

        return path

    # ------------------------------------------------------------------
    # Экспорт
    # ------------------------------------------------------------------

    def export_to_json(self, report, filename):

        path = self._path(filename)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2, default=str)

        return path

    def export_to_csv(self, rows, filename):
        """Сохраняет список плоских словарей как таблицу CSV."""

        if not isinstance(rows, list) or not rows:
            raise InvalidOperationError("Для CSV нужен непустой список строк")

        fieldnames = []

        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        path = self._path(filename)

        # utf-8-sig — чтобы Excel правильно показал русские буквы
        with open(path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return path    


    # ------------------------------------------------------------------
    # Графики
    # ------------------------------------------------------------------

    def pie_balance_by_currency(self, filename="pie_balance_by_currency.png"):
        """Круговая: доля средств банка в каждой валюте (в базовой валюте)."""

        by_currency = self.bank.get_total_balance(self.base_currency)["by_currency"]

        labels = []
        values = []

        for currency, amount in by_currency.items():
            converted = CurrencyConverter.convert(amount, currency, self.base_currency)
            if converted > 0:
                labels.append(currency)
                values.append(converted)

        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(f"Средства банка по валютам (в {self.base_currency})")

        return self._save(fig, filename)

    def pie_transactions_by_status(self, filename="pie_transactions_by_status.png"):
        """Круговая: транзакции по статусу."""

        by_status = self.processor.get_statistics()["by_status"]

        if not by_status:
            raise InvalidOperationError("Нет обработанных транзакций")

        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            list(by_status.values()),
            labels=list(by_status.keys()),
            autopct="%1.1f%%",
            startangle=90
        )
        ax.set_title("Транзакции по статусу")

        return self._save(fig, filename)

    def bar_clients_balance(self, filename="bar_clients_balance.png"):
        """Столбчатая: средства каждого клиента в базовой валюте."""

        ranking = self.bank.get_clients_ranking(self.base_currency)

        names = [item["full_name"] for item in ranking]
        totals = [item["total_balance"] for item in ranking]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(names, totals)
        ax.bar_label(bars, fmt="%.0f")
        ax.set_title(f"Средства клиентов (в {self.base_currency})")
        ax.set_ylabel(self.base_currency)
        ax.tick_params(axis="x", rotation=30)

        return self._save(fig, filename)

    def bar_risk_levels(self, filename="bar_risk_levels.png"):
        """Столбчатая: транзакции по уровню риска."""

        by_risk = self.processor.get_statistics()["by_risk"]

        order = ["low", "medium", "high", "not_checked"]
        labels = [level for level in order if level in by_risk]
        values = [by_risk[level] for level in labels]

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, values, color=["green", "orange", "red", "gray"][:len(labels)])
        ax.bar_label(bars)
        ax.set_title("Транзакции по уровню риска")
        ax.set_ylabel("Количество")

        return self._save(fig, filename)

    def line_balance_history(self, account_numbers,
                             filename="line_balance_history.png"):
        """График движения баланса одного или нескольких счетов."""

        if not account_numbers:
            raise InvalidOperationError("Нужен хотя бы один счёт")

        fig, ax = plt.subplots(figsize=(10, 6))

        for account_number in account_numbers:

            history = self.processor.get_balance_history(account_number)

            if not history:
                continue

            account = self.bank.accounts[account_number]

            ax.plot(
                [point["step"] for point in history],
                [point["balance"] for point in history],
                marker="o",
                label=f"{account.owner} ****{account_number[-4:]} ({account.currency})"
            )

        ax.set_title("Движение баланса")
        ax.set_xlabel("Номер операции по счёту")
        ax.set_ylabel("Баланс")
        ax.grid(True)
        ax.legend()

        return self._save(fig, filename)

    def save_charts(self, account_numbers):
        """Строит и сохраняет все графики. Возвращает список путей к файлам."""

        return [
            self.pie_balance_by_currency(),
            self.pie_transactions_by_status(),
            self.bar_clients_balance(),
            self.bar_risk_levels(),
            self.line_balance_history(account_numbers)
        ]

    def _save(self, fig, filename):

        path = self._path(filename)

        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)   # освобождаем память

        return path    