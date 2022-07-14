
notor = r'([\|]*)'
f = f"({notor}yay{notor})({notor}wow{notor})({notor}boom{notor})"
print(f)
items = ['yay', 'wow', 'boom']
print(''.join([f'({notor}{item}{notor})' for item in items]))
