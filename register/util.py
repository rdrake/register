def clean_phone_num(phone_num):
	return phone_num.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")

def format_currency(amount):
	return "$%0.2f" % (amount / 100)

def format_phone_num(phone_num):
	if len(phone_num) != 10:
		return ""

	return "(%s) %s-%s" % (phone_num[:3], phone_num[3:6], phone_num[6:])

def format_postal_code(postal_code):
	return ("%s %s" % (postal_code[:3], postal_code[3:])).upper()
