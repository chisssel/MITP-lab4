-- Задание 9: SQL-запрос для сверки показаний счётчиков и платежей
-- По каждому лицевому счёту за указанный период показывает:
--   account_number, address, owner_name
--   total_readings  — сумма показаний за период
--   total_payments  — сумма платежей за период
--   debt            — задолженность (total_readings - total_payments)
-- Отбираются только счета с расхождениями (> 0 задолженность)
-- Период задаётся через :period_start и :period_end

SELECT
    b.account_number,
    b.address,
    b.owner_name,
    COALESCE(SUM(mr.reading_value), 0) AS total_readings,
    COALESCE(SUM(p.amount), 0)         AS total_payments,
    COALESCE(SUM(mr.reading_value), 0) - COALESCE(SUM(p.amount), 0) AS debt
FROM bills b
LEFT JOIN meter_readings mr
    ON mr.bill_id = b.id
    AND mr.reading_date >= :period_start
    AND mr.reading_date < :period_end
LEFT JOIN payments p
    ON p.bill_id = b.id
    AND p.payment_date >= :period_start
    AND p.payment_date < :period_end
GROUP BY b.id, b.account_number, b.address, b.owner_name
HAVING COALESCE(SUM(mr.reading_value), 0) - COALESCE(SUM(p.amount), 0) > 0
ORDER BY debt DESC;
