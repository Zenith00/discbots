import subprocess
def delete_lines(file, count):
    with open(file, "r") as lines:
        data = lines.readlines()
    with open(file, 'w') as new_lines:
        new_lines.writelines(data[count:-1])


def prepend_line(file, line):
    with open(file, 'r') as original: data = original.read()
    with open(file, 'w') as modified: modified.write(line + "\n" + data)
    return "success"

def extract_line(file):
    with open(file, "r") as f:
        first_line = f.readline()
    delete_lines(file, 1)
    return first_line

def append_line(filename, line):
    with open(filename, "a") as file: file.write(line + "\n")
    return rawincount(filename)

def wccount(filename):
    # requires http://gnuwin32.sourceforge.net/packages/coreutils.htm
    out = subprocess.Popen(['wc', '-l', filename],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT
                         ).communicate()[0]
    return int(out.partition(b' ')[0])


def rawincount(filename):
    f = open(filename, 'rb')
    from itertools import takewhile, repeat
    bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
    return sum( buf.count(b'\n') for buf in bufgen )


def read_file(file) -> str:
    with open(file, "r") as file:
        return file.readlines()


def relative_path(file,relative):
    import os
    return os.path.join(os.path.dirname(file), relative)