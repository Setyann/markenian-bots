### 1. SALARY FLOW (зарплата)
 **INPUT: Salary batch from employer system**
 1. Employer submits payroll request
 2. Tax Authority calculates tax liability
    → net_salary = gross_salary - tax
 3. Treasury validates budget availability
 4. Treasury approves payment split:
    - net_salary → citizen
    - tax_amount → tax account
 5. Central Bank processes settlement
 6. Commercial bank (Linar Bank) credits user account
 7. Tax Authority logs paid tax

**OUTPUT: completed salary transaction**
### 2. PENSION FLOW
 1. Treasury triggers pension batch
 2. Eligibility + amount is predefined (no dynamic calculation here)
 3. Treasury executes payment
 4. Central Bank clears transaction
 5. Bank credits user
 6. Statistics records macro impact
### 3. TAX FLOW (income tax collection)
 1. Income event detected
 2. Tax Authority calculates liability
 3. Liability recorded (not yet money movement)
 4. At payment time:
    Treasury splits funds:
    - tax → state account
    - net → citizen
 5. Central Bank settles transfer
### 4. GOVERNMENT PAYMENT FLOW (contracts, salaries of officials)
 1. Ministry submits payment request
 2. Treasury validates budget line
 3. Approval check (budget limit)
 4. Payment execution via Central Bank
 5. Bank distributes funds
### 5. GDP DATA FLOW (no money movement)
 1. Tax data + bank transactions + production data collected
 2. Statistics Service aggregates data
 3. GDP computed
 4. Report published
### CORE RULES (важно)
- Деньги двигаются только через ЦБ слой
- Бюджет исполняет только Казначейство
- Налоги считаются ДО выплаты
- Статистика не влияет на деньги
- Банки только проводят операции
  
