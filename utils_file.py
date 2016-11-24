def delete_lines(file, count):
    with open(file, "r") as lines:
        data = lines.readlines()
    with open(file, 'w') as new_lines:
        new_lines.writelines(data[count:-1])


def prepend_line(file, line):
    with open(file, 'r') as original: data = original.read()
    with open(file, 'w') as modified: modified.write(line + "\n" + data)
    return "success"
