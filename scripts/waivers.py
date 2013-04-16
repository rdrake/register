from sh import wget

ids = [675, 678, 679, 680, 681, 463, 345, 665, 634, 655]

for _id in ids:
  wget("--load-cookies", "cookies.txt", "-O", "waivers/%d.pdf" % _id, "https://register.nascsoccer.org/api/receipt/%d" % _id)
