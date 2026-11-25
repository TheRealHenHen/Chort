import chort

while True:
    text = input("chort > ")
    result, error = chort.run("<stdin>", text)

    if error:
        print(error.as_string())
    elif result != None:
        print(result)