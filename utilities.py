
def pluralize(word, value, plural=None):
	if plural == None: plural = word + "s"
	if value == 1: return word
	return plural

def mention(id, t='user'):
	types = {'user': '@!', 'role': '@&'}
	return f"<{types[t]}{id}>"