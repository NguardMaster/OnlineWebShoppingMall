from flask import Blueprint, render_template, request
from forex_python.converter import CurrencyRates

test_module = Blueprint("test_module", __name__)

@test_module.route("/currency", methods=["POST"])
def worldexchange():
    from forex_python.converter import CurrencyRates

    c = CurrencyRates()
    EUR = c.get_rate('USD', 'EUR')
    JPY = c.get_rate('USD', 'JPY')
    KRW = c.get_rate('USD', 'KRW')
    INR = c.get_rate('USD', 'INR')
    CNY = c.get_rate('USD', 'CNY')

    # 1달러를 대한민국 원으로 환산
    amount_usd = 1
    eur = round(amount_usd * EUR,2)
    jpy = round(amount_usd * JPY, 2)
    krw = round(amount_usd * KRW, 2)
    inr = round(amount_usd * INR, 2)
    cny = round(amount_usd * CNY, 2)

    
    return render_template("currency.html", euro=eur, yen=jpy, won=krw, rupee=inr, yuan=cny)
