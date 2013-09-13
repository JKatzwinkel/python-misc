from time import time


def days_since(timestamp):
	return (time()-timestamp)/3600/24


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
