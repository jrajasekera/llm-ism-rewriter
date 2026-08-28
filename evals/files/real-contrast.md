The earlier profile pointed at the database, and that is where two of us spent
a day. It isn't the database. It's serialization: the JSON encoder allocates a
new buffer for every row, and at 40k rows a second that dominates.
