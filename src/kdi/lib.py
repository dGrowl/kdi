def fibonacci(n: int):
	if n < 2:
		return n
	a = 0
	b = 1
	for _ in range(n - 1):
		a, b = b, a + b
	return b
