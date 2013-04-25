from sh import wget

ids = [702,
699,
625,
634,
616,
620,
335,
604,
695,
689,
696,
665,
569]

for _id in ids:
  wget("--load-cookies", "cookies.txt", "-O", "waivers/%d.pdf" % _id, "https://register.nascsoccer.org/api/receipt/%d" % _id)
