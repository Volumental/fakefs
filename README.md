# fakefs
Introducing fakefs, easy faking file system
    
Easily dictate how the filessytem is supposed to behave during tests. Benefits:
* All in memory - Very fast
* Unit tests does not mess with your harddrive needlessly, leave stray files around and shit. Clean and beautiful.
* Minute control - Decide whether a file should exist or not, and what contents it should have
* Possible to assert on file contents when e.g. writing files.
* Batteries not included.

## Usage
    fs = FakeFilesystem()
    fs.add_file('file.txt', data='contents goes here')
    with fs.monkey.patch():
        # Production code
        with open('file.txt') as f:
            print(f.read())

## Author
Samuel Carlsson <samuel.carlsson@volumental.com>
