from time import time
import re

# calculates days passed since timestamp
def days_since(timestamp):
	return (time()-timestamp)/3600/24

# makes human readable repr of time span since given timestamp
def time_span_str(timestamp):
	if timestamp > 0:
		ago = int(time()-timestamp)/60
		if ago>60:
			ago /= 60
			if ago>24:
				ago/=24
				ago='{} days ago'.format(ago)
			else:
				ago='{} hours ago'.format(ago)
		else:
			ago='{} minutes ago'.format(ago)
	else:
		ago=None
	return ago


# regex registry
regex_reg = {}
# returns nth match of regex in str.
# compiles regex, so that repeated calls can return faster
# n starts with 0
def grep(regex, string, n=None):
	r = regex_reg.get(regex)
	if not r:
		r = re.compile(regex)
		regex_reg[regex]=r
	matches = r.findall(string)
	if n:
		return matches[n]
	return matches