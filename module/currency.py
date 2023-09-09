from forex_python.converter import CurrencyRates

c = CurrencyRates()
EUR = c.get_rate('USD', 'EUR')
JPY = c.get_rate('USD', 'JPY')
KRW = c.get_rate('USD', 'KRW')
INR = c.get_rate('USD', 'INR')
CNY = c.get_rate('USD', 'CNY')

# 1달러를 대한민국 원으로 환산
amount_usd = 1
eur = amount_usd * EUR
jpy = amount_usd * JPY
krw = amount_usd * KRW
inr = amount_usd * INR
cny = amount_usd * CNY

print(inr)

